import asyncio
import json

import pytest

from chat.alice import AliceRuntime
from chat.runtime import private_ipv4
from tests.test_chat_bob import make_bob


@pytest.mark.parametrize("address", ["127.0.0.1", "8.8.8.8", "0.0.0.0", "224.0.0.1", "169.254.1.2", "::1", "bob.local", "999.1.2.3"])
def test_private_address_validation(address):
    with pytest.raises(ValueError):
        private_ipv4(address)


def test_private_address():
    for address in ("192.168.1.2", "10.0.0.5", "172.16.3.4"):
        assert private_ipv4(address) == address


def test_alice_secure_connect_telemetry_separation(tmp_path):
    bob, bundles, passwords = make_bob(tmp_path)
    database = tmp_path / "alice.db"
    alice = AliceRuntime(bundles["alice"], bob.config, database)
    async def run():
        await bob.unlock(passwords["bob"].decode())
        await bob.start_server()
        await alice.unlock(passwords["alice"].decode())
        await alice._connect("127.0.0.1")
        alice.messages.append({"text": "CHAT-LEAK-MARKER", "sender": "alice"})
        telemetry = alice.telemetry()
        assert telemetry["session"]["protocol"] == "TLSv1.3"
        assert telemetry["relationship_id"]
        assert "CHAT-LEAK-MARKER" not in json.dumps(telemetry)
        assert "observatory" not in bob.snapshot()
        await alice.close()
        await bob.close()
    asyncio.run(run())
    assert b"CHAT-LEAK-MARKER" not in database.read_bytes()
