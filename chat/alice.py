"""Alice-only trust observatory and pinned numeric-address client."""

import asyncio
from collections import deque
from dataclasses import replace
import json
from time import perf_counter
from time import monotonic

from chat.config import ChatConfig
from chat.coordinator import Coordinator, GuardAdapter, State
from chat.runtime import Endpoint, private_ipv4
from chat.protocol import envelope
from dashboard.presentation import guard_snapshot
from network.secure import connect
from network.snapshot import raw_snapshot
from storage.relationship_store import RelationshipStore
from storage.relationship_store import timestamp
from trust.normalization import normalize_snapshot
from trust.signal_collector import ContextSignalCollector
from verification.session_guard import SessionGuard
from verification.verification import Outcome


class AliceRuntime(Endpoint):
    def __init__(self, bundle, config=ChatConfig(), database=".state/chat-alice.db"):
        super().__init__("alice", bundle, config)
        self.database = database
        self.store = None
        self.guard = None
        self.collector = ContextSignalCollector()
        self.history = deque(maxlen=300)
        self.address = None
        self.assessment_task = None
        self.ping = None
        self.last_heartbeat = None
        self.heartbeat_interval_ms = None
        self._stop_measurements = False
        self.recovery_ready = None
        self.approved_recovery = None
        self.demo_task = None

    async def command(self, command):
        if command["command"] == "set_demo_mode":
            async with self._command_lock:
                await self.set_demo_mode(command["mode"])
        elif command["command"] == "connect":
            async with self._command_lock:
                await self.connect_address(command["address"])
        else:
            await super().command(command)

    async def connect_address(self, address):
        address = private_ipv4(address)
        await self._connect(address)

    async def establish(self):
        return await connect(self.transport_settings(self.address), self.credentials, lambda: self._password,
                             server_hostname="bob.local", collector=self.collector)

    async def _connect(self, address):
        """Internal seam allows loopback TLS tests without weakening browser input."""
        if not self.unlocked or self.gate.state not in {State.LOCKED, State.CLOSED, State.RESTRICTED}:
            raise ValueError("Unlock identity and close the previous session first.")
        if self.guard:
            await self.disconnect()
        self.gate = Coordinator(self.role, self.config)
        self.gate.transition(State.CONNECTING)
        self.address = address
        self.publish()
        try:
            connection = await self.establish()
            self.gate.attach(connection)
            if self.store is None:
                self.store = RelationshipStore(self.database)
            self.guard = SessionGuard(GuardAdapter(self.gate), self.store, self.respond,
                                      reconnect=self.recover, timeout=self.config.verification_timeout,
                                      verification_simulated=False, rotate_on_initial_verification=False,
                                      verify_before_rotation=True)
            # Every new application connection requires both humans, even when
            # the relationship was successfully verified in an earlier run.
            self.guard.verified = False
            self.guard.baselines = replace(self.guard.baselines, timing_ms=self.config.heartbeat_seconds * 1000)
            self.error = None
            self.reader_task = asyncio.create_task(self.read_loop(connection))
            await self.connected()
        except Exception:
            await self.restrict("Cannot connect securely. Check Bob's private IP, listener, Private-network firewall permission, and identity bundle.")
            raise ValueError("Secure connection failed.") from None
        self.publish()

    async def connected(self):
        self._stop_measurements = False
        self.assessment_task = asyncio.create_task(self.measure_loop())

    async def measure_loop(self):
        try:
            await self.assess()
            while not self._stop_measurements and self.gate.state not in {State.CLOSED, State.RESTRICTED}:
                if self.demo_task and not self.demo_task.done():
                    await asyncio.sleep(0.05)
                    continue
                await asyncio.sleep(self.config.heartbeat_seconds)
                if self.gate.state != State.ACTIVE:
                    continue
                message = envelope("ping", "alice")
                now = perf_counter()
                future = asyncio.get_running_loop().create_future()
                self.ping = (message["id"], now, future)
                await self.gate.control(message)
                await asyncio.wait_for(future, 8)
                self.ping = None
                await self.assess()
        except asyncio.CancelledError:
            raise
        except Exception:
            await self.restrict("Heartbeat stopped. Check the private Wi-Fi connection and Bob's application.")

    async def handle(self, message):
        if message["type"] == "session_notice" and message["notice"] == "ready":
            if not self.recovery_ready or self.recovery_ready.done():
                from chat.protocol import ChatProtocolError
                raise ChatProtocolError()
            self.recovery_ready.set_result(True)
        elif message["type"] == "pong":
            if not self.ping or message["ping_id"] != self.ping[0] or self.ping[2].done():
                from chat.protocol import ChatProtocolError
                raise ChatProtocolError()
            self.gate.connection.metrics.record_round_trip((perf_counter() - self.ping[1]) * 1000,
                                                            source="authenticated_heartbeat")
            completed = perf_counter()
            self.heartbeat_interval_ms = None if self.last_heartbeat is None else (completed - self.last_heartbeat) * 1000
            self.last_heartbeat = completed
            self.ping[2].set_result(True)
        else:
            await super().handle(message)

    def trust_input(self):
        raw = raw_snapshot(self.gate.connection)
        # A human's typing cadence is not a trust signal. Use the measured
        # authenticated heartbeat completion cadence, which continues during silence.
        raw["timing_ms"] = self.heartbeat_interval_ms
        if self.mode == "ip_change":
            raw["peer_ip"] = "192.0.2.1"
        return raw

    async def set_demo_mode(self, mode):
        from chat.protocol import MODES
        if mode not in MODES or self.gate.state not in {State.ACTIVE, State.VERIFYING}:
            raise ValueError("Connect and verify before selecting a condition.")
        if self.demo_task and not self.demo_task.done():
            raise ValueError("Wait for the bounded reconnect burst to finish.")
        if mode != "normal" and self.gate.state != State.ACTIVE:
            raise ValueError("Complete verification before starting a condition.")
        if self.mode != "normal":
            self.store.audit(self.guard.context.session_id, "DEMO_STOPPED", condition=self.mode)
        self.mode = mode
        if mode != "normal":
            self.store.audit(self.guard.context.session_id, "DEMO_STARTED", condition=mode)
        if mode == "reconnect_burst":
            self.demo_task = asyncio.create_task(self.reconnect_burst())
        else:
            await self.gate.control(envelope("demo_mode", "alice", mode=mode))
        self.publish()

    async def reconnect_burst(self):
        try:
            # Let an already-issued ping/assessment finish before replacing TLS.
            while self.ping or self.guard._lock.locked():
                await asyncio.sleep(0.01)
            for _ in range(self.config.reconnect_attempts):
                if self.gate.state != State.ACTIVE:
                    raise ValueError("Session no longer active.")
                message = envelope("demo_mode", "alice", mode="reconnect_burst")
                self.approved_recovery = {"id": message["id"], "relationship": self.guard.context.relationship_id}
                await self.gate.control(message)
                self.gate.transition(State.RECONNECTING)
                previous = self.guard.context.session_id
                self.fail_deliveries()
                await self.gate.connection.close()
                replacement = await self.recover()
                self.guard.connection = replacement
                self.guard.context = replacement.metrics.session
                self.store.finish_session(previous)
                self.store.start_session(self.guard.context.session_id, self.guard.context.relationship_id)
                self.guard.key_started = monotonic()
                self.store.key_event(self.guard.context.session_id, "STANDARD_ROTATION", replacement.info.key_id)
                await self.gate.control(envelope("session_notice", "alice", notice="ready"))
                self.approved_recovery = None
                self.gate.transition(State.ACTIVE)
                self.publish()
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            raise
        except Exception:
            await self.restrict("Reconnect burst stopped safely. Start a new session.")

    async def assess(self):
        try:
            await self.guard.assess(self.trust_input())
            if self.guard.restricted:
                await self.restrict()
            elif self.gate.state == State.VERIFYING and self.dual is None:
                if self.approved_recovery:
                    await self.gate.control(envelope("session_notice", "alice", notice="ready"))
                    self.approved_recovery = None
                self.gate.transition(State.ACTIVE)
            self.history.append({"timestamp": timestamp(), "score": self.guard.engine.score,
                                 "delta": self.guard.last_assessment.delta,
                                 "triggered": self.guard.last_decision.requires_verification})
            self.publish()
        except asyncio.CancelledError:
            raise
        except Exception:
            await self.restrict()

    async def respond(self, request):
        relationship = self.guard.context.relationship_id
        recovery = self.guard.verified
        self.begin_verification(request.id, relationship, request.reason, recovery)
        dual = self.dual
        await self.gate.control(envelope("verify_request", "alice", request_id=request.id,
                                        relationship=relationship, reason=request.reason, recovery=recovery))
        try:
            success = await dual.ready
            if not success or self.gate.state != State.VERIFYING:
                return Outcome.FAILURE
            await self.gate.control(envelope("verification_result", "alice", request_id=request.id,
                                            relationship=relationship, result="SUCCESS", recovery=recovery))
            if recovery:
                self.approved_recovery = {"id": request.id, "relationship": relationship}
                await self.gate.control(envelope("session_notice", "alice", notice="reconnect"))
                self.gate.transition(State.RECONNECTING)
                self.fail_deliveries()
            self.clear_verification()
            return Outcome.SUCCESS
        finally:
            if self.dual is dual:
                dual.fail()
                self.clear_verification()

    async def recover(self):
        approval = self.approved_recovery
        if not approval or self.gate.state != State.RECONNECTING:
            raise ValueError("Fresh TLS requires dual approval.")
        if self.reader_task:
            self.reader_task.cancel()
            await asyncio.gather(self.reader_task, return_exceptions=True)
        replacement = None
        for attempt in range(self.config.reconnect_attempts):
            try:
                replacement = await self.establish()
                break
            except Exception:
                if attempt + 1 == self.config.reconnect_attempts:
                    raise ValueError("TLS recovery failed.") from None
                await asyncio.sleep(0.1 * (attempt + 1))
        if replacement.metrics.session.relationship_id != approval["relationship"]:
            await replacement.close()
            raise ValueError("Replacement identity differs.")
        self.gate.attach(replacement)
        self.last_heartbeat = None
        self.heartbeat_interval_ms = None
        self.recovery_ready = asyncio.get_running_loop().create_future()
        self.reader_task = asyncio.create_task(self.read_loop(replacement))
        try:
            await self.gate.control(envelope("verification_result", "alice", request_id=approval["id"],
                                            relationship=approval["relationship"], result="SUCCESS", recovery=True))
            await asyncio.wait_for(self.recovery_ready, self.config.verification_timeout)
        finally:
            self.recovery_ready = None
        return GuardAdapter(self.gate)

    def telemetry(self):
        data = guard_snapshot(self.guard)
        data["history"] = list(self.history)
        data["relationship_id"] = self.guard.context.relationship_id if self.guard else None
        data["normalized"] = normalize_snapshot(self.guard.last_raw, self.guard.baselines,
                                                 self.guard.normalization_policy) if self.guard else {}
        data["timeline"] = []
        data["mode"] = self.mode
        data["condition_label"] = {"normal": "NORMAL OBSERVATION", "latency": "REAL INDUCED CONDITION",
                                   "reconnect_burst": "REAL CONNECTION EVENT", "ip_change": "SIMULATED METADATA"}[self.mode]
        if self.store and self.guard:
            rows = self.store.db.execute("SELECT timestamp,event_type,metadata FROM audit_events WHERE relationship_id=? ORDER BY id DESC LIMIT 100",
                                         (self.guard.context.relationship_id,)).fetchall()
            data["timeline"] = [{"timestamp": row["timestamp"], "event": row["event_type"],
                                 "metadata": json.loads(row["metadata"])} for row in reversed(rows)]
        return data

    def snapshot(self):
        return {**super().snapshot(), "observatory": self.telemetry()}

    async def disconnect(self):
        # Python 3.10 wait_for can consume cancellation when its child completes
        # in the same loop turn. A durable stop flag makes shutdown independent
        # of that race instead of repeatedly cancelling an otherwise live loop.
        self._stop_measurements = True
        if self.demo_task and self.demo_task is not asyncio.current_task():
            self.demo_task.cancel()
            await asyncio.gather(self.demo_task, return_exceptions=True)
        if self.assessment_task and self.assessment_task is not asyncio.current_task():
            self.assessment_task.cancel()
            await asyncio.gather(self.assessment_task, return_exceptions=True)
        await super().disconnect()
        if self.guard:
            await self.guard.close()

    async def close(self):
        await super().close()
        if self.store:
            self.store.close()
            self.store = None
        self.guard = None
        self.history.clear()

    async def restrict(self, reason="Verification failed. Start a new session to compare again."):
        try:
            await super().restrict(reason)
        finally:
            # Transport/protocol failures must invalidate persisted verification
            # too, even if no assessment happened after the failure.
            if self.guard and not self.guard.restricted:
                await self.guard.restrict()
