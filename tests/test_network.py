import asyncio
import struct
from contextlib import asynccontextmanager

import pytest

from config.settings import Settings
from network.connection import ConnectionFailure, FramedConnection, PeerClosed, ProtocolError
from network.connection import SessionInfo
from time import perf_counter
import uuid


@asynccontextmanager
async def pair(settings=None):
    settings = settings or Settings(port=0, io_timeout=0.3)
    accepted = asyncio.Queue()
    server = await asyncio.start_server(lambda r, w: accepted.put_nowait((r, w)), "127.0.0.1", 0)
    start = perf_counter()
    r, w = await asyncio.open_connection("127.0.0.1", server.sockets[0].getsockname()[1])
    a = FramedConnection(r, w, settings, SessionInfo(uuid.uuid4().hex, elapsed_ms=(perf_counter() - start) * 1000))
    r, w = await asyncio.wait_for(accepted.get(), 1)
    b = FramedConnection(r, w, settings)
    try:
        yield a, b
    finally:
        await a.close()
        await b.close()
        server.close()
        await server.wait_closed()


def test_bidirectional_and_reconnect():
    async def run():
        ids = set()
        for _ in range(2):
            async with pair() as (a, b):
                ids.add(a.info.session_id)
                assert a.info.elapsed_ms >= 0
                for payload in (b"hello", b"", bytes(range(256))):
                    await a.send(payload)
                    assert await b.receive() == payload
                    await b.send(payload[::-1])
                    assert await a.receive() == payload[::-1]
        assert len(ids) == 2
    asyncio.run(run())


def test_fragmented_and_coalesced_frames():
    async def run():
        async with pair() as (a, b):
            data = struct.pack("!I", 3) + b"abc" + struct.pack("!I", 2) + b"de"
            for chunk in (data[:1], data[1:3], data[3:6], data[6:]):
                a._writer.write(chunk)
                await a._writer.drain()
            assert await b.receive() == b"abc"
            assert await b.receive() == b"de"
    asyncio.run(run())


@pytest.mark.parametrize("data", [b"\x00", struct.pack("!I", 5) + b"ab", struct.pack("!I", 1048577)])
def test_malformed_frames(data):
    async def run():
        async with pair() as (a, b):
            a._writer.write(data)
            await a._writer.drain()
            await a.close()
            with pytest.raises(ProtocolError):
                await b.receive()
            assert not b.info.connected
    asyncio.run(run())


def test_timeout_and_closed_connection():
    async def run():
        async with pair() as (a, b):
            with pytest.raises(ConnectionFailure, match="receive failed"):
                await a.receive()
            assert not a.info.connected
            with pytest.raises(ConnectionFailure, match="closed"):
                await a.send(b"x")
    asyncio.run(run())


def test_disconnect():
    async def run():
        async with pair() as (a, b):
            await a.close()
            with pytest.raises(PeerClosed):
                await b.receive()
    asyncio.run(run())


def test_send_limit():
    async def run():
        async with pair(Settings(port=0, max_frame=8)) as (a, b):
            with pytest.raises(ProtocolError):
                await a.send(b"x" * 9)
            assert not a.info.connected
    asyncio.run(run())


def test_serialized_sends_and_concurrent_receive():
    async def run():
        async with pair() as (a, b):
            await asyncio.gather(*(a.send(bytes([i])) for i in range(10)))
            assert [await b.receive() for _ in range(10)] == [bytes([i]) for i in range(10)]
            pending = asyncio.create_task(b.receive())
            await asyncio.sleep(0)
            with pytest.raises(RuntimeError, match="concurrent"):
                await b.receive()
            pending.cancel()
            with pytest.raises(asyncio.CancelledError):
                await pending
            assert not b.info.connected
    asyncio.run(run())
