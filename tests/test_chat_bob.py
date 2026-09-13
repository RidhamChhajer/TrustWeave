import asyncio
import secrets
import socket

import pytest

from chat.bundles import credentials_from_bundle, provision_bundles
from chat.config import ChatConfig
from chat.runtime import BobRuntime
from config.settings import Settings
from network.connection import ConnectionFailure
from network.secure import connect


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def make_bob(tmp_path):
    passwords = {r: secrets.token_urlsafe(24).encode() for r in ("ca", "alice", "bob")}
    bundles = provision_bundles(tmp_path / "identities", passwords)
    return BobRuntime(bundles["bob"], ChatConfig(tls_port=free_port())), bundles, passwords


def test_bob_unlock_listener_one_peer_refresh_shutdown(tmp_path):
    bob, bundles, passwords = make_bob(tmp_path)
    async def run():
        with pytest.raises(ValueError):
            await bob.unlock("wrong password")
        await bob.unlock(passwords["bob"].decode())
        await bob.start_server()
        alice = credentials_from_bundle(bundles["alice"], "alice")
        first = await connect(Settings(port=bob.server.port), alice, lambda: passwords["alice"], server_hostname="bob.local")
        second = await connect(Settings(port=bob.server.port), alice, lambda: passwords["alice"], server_hostname="bob.local")
        with pytest.raises(ConnectionFailure):
            await second.receive()
        state = bob.snapshot()
        assert state["state"] == "VERIFYING"
        assert not {"score", "history", "trust", "audit", "signals", "key_id"} & state.keys()
        bob.messages.append({"text": "in memory", "sender": "alice"})
        await bob.browser_closed()
        assert bob.snapshot()["messages"][0]["text"] == "in memory"
        await bob.close()
        assert not bob.messages and bob._password is None and bob.server is None
        await first.close()
        await second.close()
    asyncio.run(run())


def test_bob_occupied_port(tmp_path):
    bob, _, passwords = make_bob(tmp_path)
    async def run():
        await bob.unlock(passwords["bob"].decode())
        with socket.socket() as sock:
            sock.bind(("0.0.0.0", bob.config.tls_port))
            sock.listen()
            with pytest.raises(ValueError):
                await bob.start_server()
            assert bob.server is None
        await bob.close()
    asyncio.run(run())
