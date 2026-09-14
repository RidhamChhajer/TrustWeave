import asyncio
from dataclasses import asdict, replace
import json
import logging
import secrets
import ssl
import struct

import pytest

from client.bob import echo
from config.settings import Settings
from network.connection import ConnectionFailure, close_writer
from network.secure import SecureServer, connect
from tests.wire_proxy import WireProxy


def options(port=0):
    return Settings(port=port, io_timeout=1, connect_timeout=1, close_timeout=0.3)


def test_wire_encryption_bidirectional_metadata_and_logs(identities, caplog, monkeypatch, tmp_path):
    creds, passwords = identities
    client_message = b"CONFIDENTIAL-ALICE-" + secrets.token_hex(32).encode()
    server_message = b"CONFIDENTIAL-BOB-" + secrets.token_hex(32).encode()
    received = []
    keylog = tmp_path / "forbidden-keylog"
    monkeypatch.setenv("SSLKEYLOGFILE", str(keylog))

    async def run():
        async def handler(connection):
            received.append(connection.info)
            await connection.send(server_message)
            received.append(await connection.receive())
            await connection.send(b"ACK")

        async with await SecureServer.start(options(), creds["bob"], lambda: passwords["bob"], handler) as server:
            async with WireProxy(server.port) as proxy:
                async with await connect(options(proxy.port), creds["alice"], lambda: passwords["alice"]) as connection:
                    assert await connection.receive() == server_message
                    await connection.send(client_message)
                    assert await connection.receive() == b"ACK"
                    assert connection.info.protocol == "TLSv1.3"
                    assert connection.info.session_id == received[0].session_id
                    assert connection.info.key_id == received[0].key_id
                    assert connection.info.peer_fingerprint == creds["alice"].expected_peer_pin
                    assert set(asdict(connection.info)) == {
                        "session_id", "connected", "elapsed_ms", "protocol", "cipher", "peer_fingerprint"}
                assert received[1] == client_message
                for direction in ("client", "server"):
                    wire = bytes(proxy.captured[direction])
                    assert len(wire) > 100
                    assert client_message not in wire
                    assert server_message not in wire
                    assert struct.pack("!I", len(client_message)) + client_message not in wire
    with caplog.at_level(logging.INFO, logger="adaptive_trust"):
        asyncio.run(run())
    logs = caplog.text.encode()
    assert client_message not in logs and server_message not in logs
    for password in passwords.values():
        assert password not in logs
    assert b"PRIVATE KEY" not in logs
    assert b"SESSION_FAILED" not in logs
    assert not keylog.exists()
    for record in caplog.records:
        if record.name == "adaptive_trust":
            assert isinstance(json.loads(record.message), dict)


def test_tampered_post_handshake_record_never_delivered(identities):
    creds, passwords = identities
    delivered = []

    async def run():
        rejected = asyncio.Event()
        async def handler(connection):
            try:
                delivered.append(await connection.receive())
            except ConnectionFailure:
                rejected.set()

        async with await SecureServer.start(options(), creds["bob"], lambda: passwords["bob"], handler) as server:
            async with WireProxy(server.port) as proxy:
                async with await connect(options(proxy.port), creds["alice"], lambda: passwords["alice"]) as connection:
                    proxy.corrupt_next = True
                    await connection.send(b"must never reach Bob")
                    with pytest.raises(ConnectionFailure):
                        await connection.receive()
                    await asyncio.wait_for(rejected.wait(), 2)
                    assert proxy.corrupted
                    assert not delivered
                    assert not connection.info.connected
    asyncio.run(run())


@pytest.mark.parametrize("side", ["alice", "bob"])
def test_identity_pin_rejection_on_real_sockets(identities, side):
    original, passwords = identities
    creds = dict(original)
    creds[side] = replace(creds[side], expected_peer_pin="0" * 64)

    async def run():
        delivered = []
        async def handler(connection):
            try:
                delivered.append(await connection.receive())
            except ConnectionFailure:
                pass
        async with await SecureServer.start(options(), creds["bob"], lambda: passwords["bob"], handler) as server:
            with pytest.raises(ConnectionFailure):
                await connect(options(server.port), creds["alice"], lambda: passwords["alice"])
        assert not delivered
    asyncio.run(run())


@pytest.mark.parametrize("bad_client", ["plaintext", "no_certificate", "tls12"])
def test_invalid_transport_never_reaches_handler(identities, bad_client):
    creds, passwords = identities

    async def run():
        reached = []
        async def handler(connection):
            reached.append(True)
        async with await SecureServer.start(options(), creds["bob"], lambda: passwords["bob"], handler) as server:
            writer = None
            try:
                if bad_client == "plaintext":
                    reader, writer = await asyncio.open_connection("127.0.0.1", server.port)
                    writer.write(b"THIS IS PLAINTEXT NOT TLS")
                    await writer.drain()
                else:
                    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                    ctx.load_verify_locations(str(creds["alice"].authority))
                    if bad_client == "tls12":
                        ctx.maximum_version = ssl.TLSVersion.TLSv1_2
                    reader, writer = await asyncio.wait_for(asyncio.open_connection(
                        "127.0.0.1", server.port, ssl=ctx, server_hostname="localhost"), 2)
                assert await asyncio.wait_for(reader.read(1), 2) == b""
            except (ssl.SSLError, ConnectionError):
                pass
            finally:
                if writer is not None:
                    await close_writer(writer, 0.3)
        assert not reached
    asyncio.run(run())


def test_secure_frames_limits_and_fresh_reconnect(identities):
    creds, passwords = identities
    async def run():
        ids = set()
        async with await SecureServer.start(options(), creds["bob"], lambda: passwords["bob"], echo) as server:
            for _ in range(2):
                async with await connect(options(server.port), creds["alice"], lambda: passwords["alice"]) as connection:
                    ids.add(connection.info.session_id)
                    for payload in (b"", b"a" * 1048576, secrets.token_bytes(128)):
                        await connection.send(payload)
                        assert await connection.receive() == payload
            assert len(ids) == 2
    asyncio.run(run())


def test_secure_malformed_frame_closes_connection(identities):
    creds, passwords = identities
    async def run():
        async with await SecureServer.start(options(), creds["bob"], lambda: passwords["bob"], echo) as server:
            async with await connect(options(server.port), creds["alice"], lambda: passwords["alice"]) as connection:
                connection._writer.write(struct.pack("!I", 1048577))
                await connection._writer.drain()
                with pytest.raises(ConnectionFailure):
                    await connection.receive()
    asyncio.run(run())


def test_idle_secure_receive_and_server_shutdown(identities):
    creds, passwords = identities
    async def run():
        server = await SecureServer.start(options(), creds["bob"], lambda: passwords["bob"], echo)
        async with await connect(replace(options(server.port), io_timeout=0.05), creds["alice"], lambda: passwords["alice"]) as connection:
            with pytest.raises(ConnectionFailure):
                await connection.receive()
        async with await connect(options(server.port), creds["alice"], lambda: passwords["alice"]) as connection:
            await asyncio.wait_for(server.close(), 1)
            with pytest.raises(ConnectionFailure):
                await connection.receive()
        assert not server._tasks
    asyncio.run(run())


def test_client_handshake_timeout(identities):
    creds, passwords = identities
    async def run():
        writers = []
        server = await asyncio.start_server(lambda r, w: writers.append(w), "127.0.0.1", 0)
        try:
            with pytest.raises(ConnectionFailure):
                await connect(replace(options(server.sockets[0].getsockname()[1]), connect_timeout=0.05),
                              creds["alice"], lambda: passwords["alice"])
        finally:
            server.close()
            # wait_closed waits for active clients on current Python. Close the
            # deliberately stalled handshake transports before joining the server.
            for writer in writers:
                await close_writer(writer, 0.3)
            await asyncio.wait_for(server.wait_closed(), 1)
    asyncio.run(run())


def test_server_shutdown_closes_incomplete_handshake(identities):
    creds, passwords = identities
    async def run():
        server = await SecureServer.start(replace(options(), connect_timeout=10),
                                          creds["bob"], lambda: passwords["bob"], echo)
        reader, writer = await asyncio.open_connection("127.0.0.1", server.port)
        try:
            await asyncio.sleep(0.05)
            await asyncio.wait_for(server.close(), 1)
            assert await asyncio.wait_for(reader.read(1), 0.5) == b""
        finally:
            await close_writer(writer, 0.3)
            await server.close()
    asyncio.run(run())
