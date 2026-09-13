"""In-memory endpoint runtime. Persistent operations receive metadata only."""

import asyncio
from collections import deque
import ipaddress
import socket
from time import perf_counter

from chat.bridge import Events
from chat.bundles import credentials_from_bundle
from chat.config import ChatConfig
from chat.coordinator import Coordinator, State
from chat.protocol import MAX_ENVELOPE, ChatProtocolError, DuplicateCache, envelope
from chat.verification import DualVerification
from config.settings import Settings
from crypto.key_exchange import context
from network.connection import ConnectionFailure
from network.secure import SecureServer


def private_ipv4(value):
    address = ipaddress.IPv4Address(value)
    if not any(address in ipaddress.IPv4Network(net) for net in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")):
        raise ValueError("Enter Bob's private LAN IPv4 address.")
    return str(address)


def private_addresses():
    candidates = set()
    for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
        try:
            candidates.add(private_ipv4(item[4][0]))
        except ValueError:
            pass
    return sorted(candidates)


class Endpoint:
    def __init__(self, role, bundle, config=ChatConfig()):
        self.role, self.bundle, self.config = role, bundle, config
        self.gate = Coordinator(role, config)
        self.events = Events(config.queue_size)
        self.messages = deque(maxlen=config.history_size)
        self.credentials = None
        self._password = None
        self.error = None
        self.pending = None
        self.mode = "normal"
        self.reader_task = None
        self.server = None
        self.unlocked = False
        self._command_lock = asyncio.Lock()
        self._closing = False
        self.dual = None
        self.verification_lock = asyncio.Lock()
        self.verification_timer = None
        self.deliveries = {}
        self.chat_send_lock = asyncio.Lock()
        self.resume = None
        self.recovery_timer = None
        self.verification_ids = DuplicateCache(config.duplicate_cache)

    def snapshot(self):
        return {"role": self.role, "state": self.gate.state.value, "unlocked": self.unlocked,
                "listening": self.server is not None, "port": self.server.port if self.server else self.config.tls_port,
                "addresses": private_addresses() if self.role == "bob" else [],
                "messages": [dict(m) for m in self.messages], "pending": dict(self.pending) if self.pending else None,
                "condition": "Intentional latency is active" if self.mode == "latency" else None,
                "error": self.error}

    def publish(self):
        self.events.publish({"event": "state", "data": self.snapshot()})

    def transport_settings(self, host):
        return Settings(host=host, port=self.config.tls_port, max_frame=MAX_ENVELOPE,
                        io_timeout=max(10, self.config.verification_timeout + 5), connect_timeout=5, close_timeout=1)

    async def unlock(self, password):
        if self.unlocked:
            raise ValueError("Identity is already unlocked.")
        try:
            credentials = credentials_from_bundle(self.bundle, self.role)
            secret = password.encode("utf-8")
            context(credentials, lambda: secret, server=self.role == "bob")
        except Exception:
            self.error = "Cannot unlock identity. Check the password and the device bundle."
            self.publish()
            raise ValueError(self.error) from None
        self.credentials, self._password = credentials, secret
        self.unlocked = True
        self.error = None
        self.publish()

    async def command(self, command):
        async with self._command_lock:
            kind = command["command"]
            if kind == "unlock":
                await self.unlock(command["password"])
            elif kind == "disconnect":
                await self.disconnect()
            elif kind == "start_server" and self.role == "bob":
                await self.start_server()
            elif kind == "send_chat":
                await self.send_chat(command["text"])
            elif kind == "confirm_verification":
                await self.confirm(command["request_id"], command["decision"])
            else:
                raise ValueError("Command is unavailable on this endpoint.")

    async def send_chat(self, text):
        async with self.chat_send_lock:
            if len(self.deliveries) >= self.config.queue_size:
                raise ValueError("Too many messages awaiting delivery. Wait for the peer.")
            message = envelope("chat", self.role, text=text)
            self.gate.queue_chat(message)
            entry = {"id": message["id"], "sender": self.role, "timestamp": message["timestamp"],
                     "text": text, "status": "sending"}
            self.messages.append(entry)
            self.deliveries[message["id"]] = (entry, self.gate.generation)
            try:
                sent = await self.gate.flush_one()
                if sent is None:
                    entry["status"] = "discarded"
                    self.deliveries.pop(message["id"], None)
                elif entry["status"] == "sending":
                    entry["status"] = "sent"
            except Exception:
                entry["status"] = "not delivered"
                self.deliveries.pop(message["id"], None)
                self.publish()
                raise ValueError("Message was not delivered. Check the connection and verification state.") from None
            self.publish()

    async def confirm(self, request_id, decision):
        async with self.verification_lock:
            if self.dual is None or self.gate.state != State.VERIFYING:
                await self.restrict()
                raise ValueError("No verification is pending.")
            dual = self.dual
            try:
                # Serialize local sends and peer decisions to keep result ordering
                # deterministic even when both people click simultaneously.
                if request_id != dual.id or self.role in dual.decisions:
                    raise ChatProtocolError()
                await self.gate.control(envelope("verify_response", self.role, request_id=request_id,
                                                relationship=dual.relationship, decision=decision))
                dual.decide(self.role, request_id, dual.relationship, decision)
                self.pending = dual.snapshot(self.role)
                self.publish()
                if decision != "MATCH" and self.role == "bob":
                    await self.restrict()
            except Exception:
                await self.restrict()
                raise

    def begin_verification(self, request_id, relationship, reason, recovery=False):
        if self.dual is not None or relationship != self.gate.connection.metrics.session.relationship_id:
            raise ChatProtocolError()
        if self.gate.state == State.ACTIVE:
            self.gate.transition(State.VERIFYING)
        if self.gate.state != State.VERIFYING:
            raise ChatProtocolError()
        self.verification_ids.accept(request_id)
        self.dual = DualVerification(request_id, relationship, reason, recovery)
        self.pending = self.dual.snapshot(self.role)
        async def timeout():
            await asyncio.sleep(self.config.verification_timeout)
            if self.dual:
                await self.restrict("Safety-code comparison timed out. Start a new session.")
        self.verification_timer = asyncio.create_task(timeout())
        self.publish()

    def clear_verification(self):
        if self.verification_timer and self.verification_timer is not asyncio.current_task():
            self.verification_timer.cancel()
        self.verification_timer = None
        self.dual = None
        self.pending = None

    async def handle(self, message):
        kind = message["type"]
        if kind in {"verify_request", "verify_response", "verification_result"}:
            async with self.verification_lock:
                if kind == "verify_request" and self.role == "bob":
                    self.begin_verification(message["request_id"], message["relationship"], message["reason"], message["recovery"])
                elif kind == "verify_response" and self.dual:
                    self.dual.decide(message["sender"], message["request_id"], message["relationship"], message["decision"])
                    self.pending = self.dual.snapshot(self.role)
                    self.publish()
                    if message["decision"] != "MATCH" and self.role == "bob":
                        await self.restrict()
                elif kind == "verification_result" and self.role == "bob" and self.resume and not self.dual:
                    if (self.gate.state != State.VERIFYING or message["request_id"] != self.resume["id"]
                        or message["relationship"] != self.resume["relationship"] or not message["recovery"]
                        or message["result"] != "SUCCESS"):
                        raise ChatProtocolError()
                    self.resume["confirmed"] = True
                    await self.gate.control(envelope("session_notice", self.role, notice="ready"))
                elif kind == "verification_result" and self.role == "bob" and self.dual:
                    dual = self.dual
                    if (message["request_id"] != dual.id or message["relationship"] != dual.relationship
                        or message["recovery"] != dual.recovery or message["result"] != "SUCCESS"
                        or dual.decisions != {"alice": "MATCH", "bob": "MATCH"}):
                        raise ChatProtocolError()
                    if message["recovery"]:
                        await self.recovery_approved()
                    else:
                        self.gate.transition(State.ACTIVE)
                    self.clear_verification()
                    self.publish()
                else:
                    raise ChatProtocolError()
        elif kind == "chat":
            if self.gate.state != State.ACTIVE:
                return
            self.messages.append({"id": message["id"], "sender": message["sender"], "text": message["text"],
                                  "timestamp": message["timestamp"], "status": "received"})
            self.publish()
            await self.gate.control(envelope("chat_ack", self.role, chat_id=message["id"]))
        elif kind == "chat_ack":
            delivery = self.deliveries.pop(message["chat_id"], None)
            if delivery is None:
                raise ChatProtocolError()
            entry, generation = delivery
            entry["status"] = "delivered" if generation == self.gate.generation else "delivery unconfirmed"
            self.publish()
        elif kind == "ping":
            await self.gate.control(envelope("pong", self.role, ping_id=message["id"]))
        elif kind == "session_notice" and message["notice"] == "reconnect" and self.role == "bob" and self.resume:
            if self.gate.state != State.RECONNECTING:
                raise ChatProtocolError()
        elif kind == "session_notice" and message["notice"] == "ready" and self.role == "bob" and self.resume:
            if self.gate.state != State.VERIFYING or not self.resume.get("confirmed"):
                raise ChatProtocolError()
            self.gate.transition(State.ACTIVE)
            self.clear_recovery()
            self.publish()
        elif kind == "session_notice" and message["notice"] == "shutdown":
            await self.restrict("Peer disconnected. Start a new session when both devices are ready.")
        else:
            raise ChatProtocolError()

    async def recovery_approved(self):
        self.resume = {"id": self.dual.id, "relationship": self.dual.relationship}
        self.gate.transition(State.RECONNECTING)
        self.fail_deliveries()
        async def expire():
            await asyncio.sleep(self.config.verification_timeout)
            if self.resume:
                await self.restrict("TLS recovery timed out. Start a new session.")
        self.recovery_timer = asyncio.create_task(expire())

    def clear_recovery(self):
        if self.recovery_timer and self.recovery_timer is not asyncio.current_task():
            self.recovery_timer.cancel()
        self.recovery_timer = None
        self.resume = None

    async def read_loop(self, connection):
        try:
            while not self._closing and connection is self.gate.connection and connection.info.connected:
                message = await self.gate.receive()
                if message is not None:
                    await self.handle(message)
        except asyncio.CancelledError:
            raise
        except Exception:
            if not self._closing and connection is self.gate.connection and self.gate.state != State.RECONNECTING:
                await self.restrict("Secure session stopped. Check Wi-Fi and the peer, then start a new session.")

    async def restrict(self, reason="Verification failed. Start a new session to compare again."):
        if self.gate.state not in {State.RESTRICTED, State.CLOSED}:
            self.gate.transition(State.RESTRICTED)
        if self.dual:
            self.dual.fail()
        self.clear_verification()
        self.clear_recovery()
        self.error = reason
        self.fail_deliveries()
        if self.gate.connection:
            await self.gate.connection.close()
        self.publish()

    async def browser_closed(self):
        # Refresh can recover the in-memory conversation. Losing a comparison
        # surface, however, must never leave an approval request live.
        if not self.events.clients and self.pending:
            await self.restrict("Browser closed during verification. Start a new session.")

    def fail_deliveries(self):
        for entry, _ in self.deliveries.values():
            entry["status"] = "not delivered"
        self.deliveries.clear()

    async def disconnect(self):
        self._closing = True
        try:
            if self.gate.connection and self.gate.connection.info.connected:
                try:
                    await self.gate.control(envelope("session_notice", self.role, notice="shutdown"))
                except Exception:
                    pass
                await self.gate.connection.close()
            if self.reader_task and self.reader_task is not asyncio.current_task():
                self.reader_task.cancel()
                await asyncio.gather(self.reader_task, return_exceptions=True)
            if self.server:
                await self.server.close()
                self.server = None
            if self.gate.state != State.CLOSED:
                self.gate.transition(State.CLOSED)
            if self.dual:
                self.dual.fail()
            self.clear_verification()
            self.clear_recovery()
            self.fail_deliveries()
        finally:
            self._closing = False
            self.publish()

    async def close(self):
        await self.disconnect()
        self._password = None
        self.credentials = None
        self.messages.clear()
        self.unlocked = False


class BobRuntime(Endpoint):
    def __init__(self, bundle, config=ChatConfig()):
        super().__init__("bob", bundle, config)
        self.occupied = False
        self.latency_seconds = 3.2
        self.delayed = asyncio.Queue(config.queue_size)
        self.delay_task = None
        self.condition_changed = asyncio.Event()

    async def handle(self, message):
        if message["type"] == "demo_mode":
            if self.gate.state not in {State.ACTIVE, State.VERIFYING}:
                raise ChatProtocolError()
            mode = message["mode"]
            self.mode = mode
            self.condition_changed.set()
            if mode == "reconnect_burst":
                if self.gate.state != State.ACTIVE:
                    raise ChatProtocolError()
                self.resume = {"id": message["id"], "relationship": self.gate.connection.metrics.session.relationship_id}
                self.gate.transition(State.RECONNECTING)
                self.fail_deliveries()
                async def expire():
                    await asyncio.sleep(self.config.verification_timeout)
                    if self.resume:
                        await self.restrict("Reconnect burst timed out. Start a new session.")
                self.recovery_timer = asyncio.create_task(expire())
            self.publish()
        elif message["type"] in {"ping", "chat"} and self.mode == "latency":
            if self.delayed.full():
                raise ChatProtocolError()
            self.delayed.put_nowait((self.gate.generation, message, perf_counter() + self.latency_seconds))
            if self.delay_task is None or self.delay_task.done():
                self.delay_task = asyncio.create_task(self.delay_loop())
        else:
            await super().handle(message)

    async def delay_loop(self):
        try:
            while not self.delayed.empty() and not self._closing:
                generation, message, deadline = self.delayed.get_nowait()
                self.condition_changed.clear()
                if self.mode == "latency":
                    try:
                        await asyncio.wait_for(self.condition_changed.wait(), max(0, deadline - perf_counter()))
                    except asyncio.TimeoutError:
                        pass
                if message["type"] == "chat" and (self.gate.generation != generation or self.gate.state != State.ACTIVE):
                    continue
                await super().handle(message)
        except asyncio.CancelledError:
            raise
        except Exception:
            await self.restrict()

    async def disconnect(self):
        self.mode = "normal"
        self.condition_changed.set()
        if self.delay_task:
            self.delay_task.cancel()
            await asyncio.gather(self.delay_task, return_exceptions=True)
        while not self.delayed.empty():
            self.delayed.get_nowait()
        await super().disconnect()

    async def start_server(self):
        if not self.unlocked or self.server:
            raise ValueError("Unlock identity and stop any existing listener first.")
        self.gate = Coordinator(self.role, self.config)
        self.gate.transition(State.CONNECTING)
        try:
            self.server = await SecureServer.start(self.transport_settings("0.0.0.0"), self.credentials,
                                                   lambda: self._password, self.accept, max_connections=4)
            self.error = None
        except Exception:
            self.gate.transition(State.CLOSED)
            self.error = "Cannot listen on the TLS port. Close the other server and try again."
            raise ValueError(self.error) from None
        finally:
            self.publish()

    async def accept(self, connection):
        if self.occupied or self.gate.state not in {State.CONNECTING, State.RECONNECTING}:
            await connection.close()
            return
        if self.gate.state == State.RECONNECTING and (not self.resume or connection.metrics.session.relationship_id != self.resume["relationship"]):
            await connection.close()
            await self.restrict()
            return
        self.occupied = True
        self.gate.attach(connection)
        self.publish()
        try:
            await self.read_loop(connection)
        finally:
            self.occupied = False
