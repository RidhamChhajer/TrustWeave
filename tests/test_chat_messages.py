import asyncio
from dataclasses import replace
import json
import logging

from chat.alice import AliceRuntime
from chat.coordinator import State
from tests.test_chat_bob import make_bob
from tests.test_chat_verification import wait_for


async def activate(alice, bob, passwords):
    await bob.unlock(passwords["bob"].decode())
    await bob.start_server()
    await alice.unlock(passwords["alice"].decode())
    await alice._connect("127.0.0.1")
    await wait_for(lambda: alice.pending and bob.pending)
    await asyncio.gather(alice.confirm(alice.pending["id"], "MATCH"), bob.confirm(bob.pending["id"], "MATCH"))
    await wait_for(lambda: alice.gate.state == bob.gate.state == State.ACTIVE)


def test_bidirectional_order_unicode_bounds_heartbeat_and_no_leak(tmp_path, caplog):
    bob, bundles, passwords = make_bob(tmp_path)
    bob.config = replace(bob.config, heartbeat_seconds=0.05)
    database = tmp_path / "alice.db"
    alice = AliceRuntime(bundles["alice"], bob.config, database)
    async def run():
        try:
            await activate(alice, bob, passwords)
            await asyncio.gather(alice.send_chat("LEAK-MARKER-ALICE नमस्ते"), bob.send_chat("LEAK-MARKER-BOB 🌍"))
            await asyncio.gather(*(alice.send_chat(f"ordered {i}") for i in range(20)))
            await bob.send_chat("🌍" * 1024)
            await wait_for(lambda: not alice.deliveries and not bob.deliveries)
            assert len(alice.messages) == len(bob.messages) == 23
            assert [m["text"] for m in bob.messages if m["text"].startswith("ordered")] == [f"ordered {i}" for i in range(20)]
            assert all(m["status"] == "delivered" for m in alice.messages if m["sender"] == "alice")
            await wait_for(lambda: alice.guard.last_raw.get("rtt_ms") is not None)
            await asyncio.sleep(0.25)
            assert alice.gate.state == State.ACTIVE and len(alice.history) > 2
            assert any(m.source == "authenticated_heartbeat" for m in alice.collector.measurements)
            await bob.browser_closed()
            assert len(bob.snapshot()["messages"]) == 23
            assert "LEAK-MARKER" not in json.dumps(alice.telemetry())
        finally:
            await asyncio.wait_for(alice.close(), 3)
            await asyncio.wait_for(bob.close(), 3)
    with caplog.at_level(logging.INFO):
        asyncio.run(run())
    assert "LEAK-MARKER" not in caplog.text
    assert b"LEAK-MARKER" not in database.read_bytes()
