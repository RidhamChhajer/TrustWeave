"""Local readiness only: real TLS and delay, automated decisions, no physical LAN claim."""

import asyncio
from dataclasses import replace
import json
import logging

import pytest

from chat.alice import AliceRuntime
from chat.coordinator import State
from tests.test_chat_bob import make_bob
from tests.test_chat_messages import activate
from tests.test_chat_verification import wait_for


@pytest.mark.parametrize("run_number", [1, 2])
def test_complete_local_acceptance_sequence(tmp_path, caplog, run_number):
    bob, bundles, passwords = make_bob(tmp_path)
    bob.config = replace(bob.config, heartbeat_seconds=0.05)
    bob.latency_seconds = 0.3  # Real delay; shorter than the presenter's 3.2 seconds.
    database = tmp_path / "alice.db"
    alice = AliceRuntime(bundles["alice"], bob.config, database)
    marker = f"ACCEPTANCE-PRIVATE-RUN-{run_number}"

    async def run():
        try:
            assert not alice.messages and not bob.messages
            await activate(alice, bob, passwords)
            await asyncio.gather(alice.send_chat(marker + " Alice"), bob.send_chat(marker + " Bob"))
            await wait_for(lambda: not alice.deliveries and not bob.deliveries)
            relationship = alice.guard.context.relationship_id
            old_epoch = alice.gate.connection.info.key_id

            async def induce():
                await wait_for(lambda: alice.guard.engine.score > 96, timeout=8)
                await alice.set_demo_mode("latency")
                await wait_for(lambda: alice.pending and bob.pending, timeout=8)
                assert alice.pending["code"] == bob.pending["code"]
                assert alice.guard.last_raw["rtt_ms"] >= 250
                assert alice.guard.last_decision.reason == "sudden_drop"
                await alice.set_demo_mode("normal")
                await wait_for(lambda: bob.mode == "normal")

            await induce()
            await asyncio.gather(alice.confirm(alice.pending["id"], "MATCH"),
                                 bob.confirm(bob.pending["id"], "MATCH"))
            await wait_for(lambda: alice.gate.state == bob.gate.state == State.ACTIVE)
            assert alice.gate.connection.info.key_id != old_epoch
            assert alice.guard.context.relationship_id == relationship
            assert len(alice.messages) == len(bob.messages) == 2
            await asyncio.gather(alice.send_chat(marker + " resumed"), bob.send_chat(marker + " resumed"))
            await wait_for(lambda: not alice.deliveries and not bob.deliveries)
            await induce()
            await bob.confirm(bob.pending["id"], "MISMATCH")
            await wait_for(lambda: alice.gate.state == bob.gate.state == State.RESTRICTED)
            for endpoint in (alice, bob):
                assert not endpoint.gate.connection.info.connected
                with pytest.raises(Exception):
                    await endpoint.send_chat(marker + " blocked")
            assert marker not in json.dumps(alice.telemetry())
            assert "observatory" not in bob.snapshot()
        finally:
            await asyncio.wait_for(alice.close(), 3)
            await asyncio.wait_for(bob.close(), 3)
        assert not alice.messages and not bob.messages

    with caplog.at_level(logging.INFO):
        asyncio.run(run())
    assert marker not in caplog.text
    for path in tmp_path.glob("alice.db*"):
        assert marker.encode() not in path.read_bytes()
