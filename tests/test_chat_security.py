import asyncio
from dataclasses import replace
import json
import logging
import socket

import pytest
import uvicorn
from websockets.asyncio.client import connect as websocket_connect
from websockets.exceptions import InvalidStatus

from chat.alice import AliceRuntime
from chat.bridge import create_app
from chat.coordinator import State
from chat.protocol import envelope, encode
from config.settings import Settings
from network.secure import SecureServer
from tests.test_chat_bob import make_bob, free_port
from tests.test_chat_bridge import FakeRuntime
from tests.test_chat_messages import activate
from tests.test_chat_verification import wait_for


@pytest.mark.parametrize("bad", ["json", "utf8", "role", "duplicate", "stale"])
def test_authenticated_bad_input_restricts_and_audits(tmp_path, caplog, bad):
    bob, bundles, passwords = make_bob(tmp_path)
    alice = AliceRuntime(bundles["alice"], bob.config, tmp_path / "alice.db")
    async def run():
        try:
            await activate(alice, bob, passwords)
            if bad == "stale":
                payload = encode(envelope("verify_response", "bob", request_id="f" * 32,
                                         relationship=alice.guard.context.relationship_id, decision="MATCH"))
            elif bad == "role":
                payload = encode(envelope("chat", "alice", text="PROTOCOL-LEAK-MARKER"))
            elif bad == "duplicate":
                payload = encode(envelope("chat", "bob", text="PROTOCOL-LEAK-MARKER"))
                # A valid incoming chat is delivered once, then its replay closes.
                message = json.loads(payload)
                bob.deliveries[message["id"]] = ({"status": "sent"}, bob.gate.generation)
                await bob.gate.connection.send(payload)
                await wait_for(lambda: not bob.deliveries)
            else:
                payload = b'PROTOCOL-LEAK-MARKER' + (b'\xff' if bad == "utf8" else b'{')
            await bob.gate.connection.send(payload)
            await wait_for(lambda: alice.gate.state == State.RESTRICTED and alice.guard.restricted)
            row = alice.store.relationship(alice.guard.context.relationship_id)
            assert not row["verified"]
            assert "PROTOCOL-LEAK-MARKER" not in json.dumps(alice.telemetry())
        finally:
            await asyncio.wait_for(alice.close(), 3)
            await asyncio.wait_for(bob.close(), 3)
    with caplog.at_level(logging.INFO):
        asyncio.run(run())
    assert "PROTOCOL-LEAK-MARKER" not in caplog.text
    for path in tmp_path.glob("alice.db*"):
        assert b"PROTOCOL-LEAK-MARKER" not in path.read_bytes()


def test_real_loopback_websocket_smoke_and_origin_rejection():
    async def run():
        runtime = FakeRuntime()
        runtime.config = replace(runtime.config, ui_port=free_port())
        server = uvicorn.Server(uvicorn.Config(create_app(runtime), host="127.0.0.1", port=runtime.config.ui_port,
            ws="websockets-sansio", log_level="critical", access_log=False, ws_max_size=32768, ws_max_queue=16))
        task = asyncio.create_task(server.serve())
        try:
            await wait_for(lambda: server.started)
            address = f"127.0.0.1:{runtime.config.ui_port}"
            async with websocket_connect(f"ws://{address}/ws", origin=f"http://{address}", proxy=None) as websocket:
                assert json.loads(await websocket.recv())["data"]["role"] == "bob"
                await websocket.send('{"command":"unknown","password":"PASSWORD-MARKER"}')
                assert "PASSWORD-MARKER" not in await websocket.recv()
                await websocket.send('{"command":"unlock","password":"PASSWORD-MARKER"}')
                assert "PASSWORD-MARKER" not in await websocket.recv()
            with pytest.raises(InvalidStatus):
                async with websocket_connect(f"ws://{address}/ws", origin="http://evil.invalid", proxy=None):
                    pass
        finally:
            server.should_exit = True
            await asyncio.wait_for(task, 3)
    asyncio.run(run())


def test_prehandshake_concurrency_bound(identities):
    credentials, passwords = identities
    async def run():
        server = await SecureServer.start(Settings(port=0), credentials["bob"], lambda: passwords["bob"],
                                          lambda _: asyncio.sleep(1), max_connections=2)
        clients = []
        try:
            for _ in range(8):
                clients.append(await asyncio.open_connection("127.0.0.1", server.port))
            await asyncio.sleep(0.05)
            assert len(server._tasks) <= 2
        finally:
            await server.close()
            for _, writer in clients:
                writer.close()
                try:
                    await writer.wait_closed()
                except OSError:
                    pass
    asyncio.run(run())
