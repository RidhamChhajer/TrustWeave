"""Bounded length-prefixed framing over an existing asyncio byte stream."""

import asyncio
from dataclasses import dataclass, replace
import struct
import uuid

from config.settings import Settings
from event_log import event
from network.metrics import SessionMetrics


class ConnectionFailure(Exception):
    """Transport failure with a non-sensitive diagnostic."""


class PeerClosed(ConnectionFailure):
    """Peer disconnected between frames."""


class ProtocolError(ConnectionFailure):
    """Invalid or incomplete application framing."""


@dataclass(frozen=True)
class SessionInfo:
    session_id: str
    connected: bool = True
    elapsed_ms: float | None = None
    protocol: str | None = None
    cipher: str | None = None
    peer_fingerprint: str | None = None

    @property
    def key_id(self) -> str:
        """Connection epoch label, not a key or TLS secret."""
        return self.session_id + ":tls-traffic"


async def close_writer(writer: asyncio.StreamWriter, timeout: float) -> None:
    writer.close()
    try:
        await asyncio.wait_for(writer.wait_closed(), timeout)
    except (OSError, asyncio.TimeoutError):
        writer.transport.abort()
    except asyncio.CancelledError:
        writer.transport.abort()
        raise


class FramedConnection:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
                 settings: Settings, info: SessionInfo | None = None, metrics: SessionMetrics | None = None):
        self._reader = reader
        self._writer = writer
        self._settings = settings
        self._info = info or SessionInfo(uuid.uuid4().hex)
        self._send_lock = asyncio.Lock()
        self._receiving = False
        self._closed = False
        self.metrics = metrics
        self._verification_pending = False

    def require_verification(self, required: bool) -> None:
        self._verification_pending = required

    @property
    def info(self) -> SessionInfo:
        return self._info

    def _check_open(self) -> None:
        if self._closed:
            raise ConnectionFailure("connection is closed")
        if self._verification_pending:
            raise ConnectionFailure("identity verification required")

    async def send(self, payload: bytes) -> None:
        self._check_open()
        if not isinstance(payload, bytes):
            raise TypeError("payload must be bytes")
        if len(payload) > self._settings.max_frame:
            await self.close()
            raise ProtocolError("frame exceeds configured limit")

        async def write() -> None:
            async with self._send_lock:
                self._check_open()
                self._writer.write(struct.pack("!I", len(payload)) + payload)
                await self._writer.drain()
                if self.metrics is not None:
                    self.metrics.frame("sent")

        try:
            await asyncio.wait_for(write(), self._settings.io_timeout)
        except asyncio.CancelledError:
            await self.close()
            raise
        except (OSError, asyncio.TimeoutError):
            await self.close()
            raise ConnectionFailure("send failed") from None
        event("FRAME_SENT", session_id=self.info.session_id, byte_count=len(payload))

    async def receive(self) -> bytes:
        self._check_open()
        if self._receiving:
            raise RuntimeError("concurrent receive is not supported")
        self._receiving = True

        async def read() -> bytes:
            try:
                header = await self._reader.readexactly(4)
            except asyncio.IncompleteReadError as exc:
                if not exc.partial:
                    raise PeerClosed("peer disconnected") from None
                raise ProtocolError("truncated frame header") from None
            size = struct.unpack("!I", header)[0]
            if size > self._settings.max_frame:
                raise ProtocolError("frame exceeds configured limit")
            try:
                return await self._reader.readexactly(size)
            except asyncio.IncompleteReadError:
                raise ProtocolError("truncated frame body") from None

        try:
            payload = await asyncio.wait_for(read(), self._settings.io_timeout)
        except asyncio.CancelledError:
            await self.close()
            raise
        except ConnectionFailure:
            await self.close()
            raise
        except (OSError, asyncio.TimeoutError):
            await self.close()
            raise ConnectionFailure("receive failed") from None
        finally:
            self._receiving = False
        self._check_open()
        if self.metrics is not None:
            self.metrics.frame("received")
        event("FRAME_RECEIVED", session_id=self.info.session_id, byte_count=len(payload))
        return payload

    async def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._info = replace(self._info, connected=False)
            try:
                await close_writer(self._writer, self._settings.close_timeout)
            finally:
                event("SESSION_CLOSED", session_id=self.info.session_id)

    async def __aenter__(self) -> "FramedConnection":
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.close()
