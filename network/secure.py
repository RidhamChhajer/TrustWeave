"""Public transport: mutual TLS, pinned identities, then encrypted framed messages."""

import asyncio
from collections.abc import Awaitable, Callable
from time import perf_counter
import socket
import uuid

from config.settings import Settings
from crypto.identity import Credentials, fingerprint
from cryptography import x509
from crypto.key_exchange import AuthenticationError, authenticate, context
from event_log import event
from network.connection import ConnectionFailure, FramedConnection, SessionInfo, close_writer
from network.metrics import SessionMetrics
from network.session import SessionContext
from trust.signal_collector import ContextSignalCollector

Handler = Callable[[FramedConnection], Awaitable[None]]


async def connect(settings: Settings, credentials: Credentials, password: Callable[[], bytes],
                  *, server_hostname: str = "localhost", collector: ContextSignalCollector | None = None) -> FramedConnection:
    """No plaintext or unverified connection is returned to the caller."""
    ctx = context(credentials, password, server=False)
    local_pin = fingerprint(x509.load_pem_x509_certificate(credentials.certificate.read_bytes()))
    writer = None
    start = perf_counter()
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(settings.host, settings.port, ssl=ctx,
                                    server_hostname=server_hostname,
                                    ssl_handshake_timeout=settings.connect_timeout),
            settings.connect_timeout)
        handshake_ms = (perf_counter() - start) * 1000
        peer = authenticate(writer.get_extra_info("ssl_object"), credentials.expected_peer_pin)
        session_id = (await asyncio.wait_for(reader.readexactly(16), settings.io_timeout)).hex()
        info = SessionInfo(session_id, elapsed_ms=(perf_counter() - start) * 1000,
                           protocol=peer.protocol, cipher=peer.cipher, peer_fingerprint=peer.fingerprint)
        event("HANDSHAKE_COMPLETED", session_id=session_id, elapsed_ms=info.elapsed_ms,
              protocol=peer.protocol, cipher=peer.cipher)
        session = SessionContext.create(session_id, local_pin, peer.fingerprint, writer.get_extra_info("peername")[0])
        metrics = SessionMetrics(session, collector if collector is not None else ContextSignalCollector(),
                                 handshake_ms, "tcp_tls_connect")
        return FramedConnection(reader, writer, settings, info, metrics)
    except asyncio.CancelledError:
        if writer is not None:
            await close_writer(writer, settings.close_timeout)
        raise
    except (OSError, asyncio.TimeoutError, asyncio.IncompleteReadError, AuthenticationError):
        if writer is not None:
            await close_writer(writer, settings.close_timeout)
        event("CONNECTION_REJECTED")
        raise ConnectionFailure("secure connection establishment failed") from None


class SecureServer:
    """Owns accepted connections/tasks and their cleanup at shutdown."""

    def __init__(self, settings: Settings, credentials: Credentials, handler: Handler):
        self.settings = settings
        self.credentials = credentials
        self.handler = handler
        self._tasks: set[asyncio.Task] = set()
        self._listener: socket.socket | None = None
        self._accept_task: asyncio.Task | None = None
        self._sockets: set[socket.socket] = set()
        self.collector = ContextSignalCollector()
        self._local_pin = fingerprint(x509.load_pem_x509_certificate(credentials.certificate.read_bytes()))

    @classmethod
    async def start(cls, settings: Settings, credentials: Credentials,
                    password: Callable[[], bytes], handler: Handler, *, max_connections=64) -> "SecureServer":
        if type(max_connections) is not int or not 1 <= max_connections <= 256:
            raise ValueError("invalid connection bound")
        instance = cls(settings, credentials, handler)
        instance.max_connections = max_connections
        ctx = context(credentials, password, server=True)
        loop = asyncio.get_running_loop()
        addresses = await loop.getaddrinfo(settings.host, settings.port, type=socket.SOCK_STREAM)
        family, _, _, _, address = addresses[0]
        instance._listener = socket.create_server(address[:2], family=family)
        instance._listener.setblocking(False)
        instance._accept_task = asyncio.create_task(instance._accept(ctx))
        event("SERVER_STARTED", port=instance.port)
        return instance

    @property
    def port(self) -> int:
        if self._listener is None or self._listener.fileno() == -1:
            raise RuntimeError("server is not listening")
        return self._listener.getsockname()[1]

    async def _accept(self, ctx) -> None:
        loop = asyncio.get_running_loop()
        while True:
            accepted, _ = await loop.sock_accept(self._listener)
            if len(self._tasks) >= self.max_connections:
                accepted.close()
                continue
            accepted.setblocking(False)
            self._sockets.add(accepted)
            task = asyncio.create_task(self._establish(accepted, ctx))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

    async def _establish(self, accepted: socket.socket, ctx) -> None:
        # Owning this task before TLS starts lets shutdown cancel incomplete handshakes.
        loop = asyncio.get_running_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        writer = None
        handshake_start = perf_counter()
        try:
            transport, _ = await loop.connect_accepted_socket(
                lambda: protocol, accepted, ssl=ctx,
                ssl_handshake_timeout=self.settings.connect_timeout)
            writer = asyncio.StreamWriter(transport, protocol, reader, loop)
            await self._handle(reader, writer, (perf_counter() - handshake_start) * 1000)
        except asyncio.CancelledError:
            raise
        except (OSError, asyncio.TimeoutError):
            event("CONNECTION_REJECTED")
        finally:
            if writer is None:
                accepted.close()
            self._sockets.discard(accepted)

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, handshake_ms: float) -> None:
        connection = None
        try:
            peer = authenticate(writer.get_extra_info("ssl_object"), self.credentials.expected_peer_pin)
            session_id = uuid.uuid4().hex
            # Random epoch identifier is sent only within the authenticated TLS channel.
            writer.write(bytes.fromhex(session_id))
            await asyncio.wait_for(writer.drain(), self.settings.io_timeout)
            # Handshake timing is collected separately from the public connection epoch.
            info = SessionInfo(session_id, protocol=peer.protocol, cipher=peer.cipher,
                               peer_fingerprint=peer.fingerprint)
            session = SessionContext.create(session_id, self._local_pin, peer.fingerprint, writer.get_extra_info("peername")[0])
            metrics = SessionMetrics(session, self.collector, handshake_ms, "tls_handshake")
            connection = FramedConnection(reader, writer, self.settings, info, metrics)
            event("HANDSHAKE_COMPLETED", session_id=session_id, protocol=peer.protocol, cipher=peer.cipher)
            await self.handler(connection)
        except AuthenticationError:
            event("CONNECTION_REJECTED")
        except (ConnectionFailure, OSError, asyncio.TimeoutError):
            event("SESSION_FAILED")
        except asyncio.CancelledError:
            raise
        except Exception:
            # Exception strings/tracebacks may contain application payloads.
            event("SESSION_FAILED")
        finally:
            if connection is not None:
                await connection.close()
            else:
                await close_writer(writer, self.settings.close_timeout)

    async def serve_forever(self) -> None:
        if self._accept_task is None:
            raise RuntimeError("server is not started")
        await self._accept_task

    async def close(self) -> None:
        if self._accept_task is not None:
            self._accept_task.cancel()
            await asyncio.gather(self._accept_task, return_exceptions=True)
        if self._listener is not None:
            self._listener.close()
        tasks = tuple(self._tasks)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        # A task canceled before its first instruction cannot execute a finally block.
        for accepted in self._sockets:
            accepted.close()
        self._sockets.clear()

    async def __aenter__(self) -> "SecureServer":
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.close()
