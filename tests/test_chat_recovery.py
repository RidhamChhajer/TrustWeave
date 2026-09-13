import asyncio
from dataclasses import replace

import pytest

from chat.alice import AliceRuntime
from chat.coordinator import State
from tests.test_chat_bob import make_bob
from tests.test_chat_messages import activate
from tests.test_chat_verification import wait_for


@pytest.mark.parametrize("outcome", ["MATCH", "MISMATCH", "unavailable", "changed", "rotation"])
def test_fresh_tls_recovery(tmp_path, outcome):
    bob, bundles, passwords = make_bob(tmp_path)
    bob.config = replace(bob.config, heartbeat_seconds=0.1)
    alice = AliceRuntime(bundles["alice"], bob.config, tmp_path / "alice.db")
    async def run():
        try:
            await activate(alice, bob, passwords)
            await alice.send_chat("conversation survives recovery")
            await wait_for(lambda: not alice.deliveries)
            old_session = alice.guard.context.session_id
            relationship = alice.guard.context.relationship_id
            original_input = alice.trust_input
            alice.trust_input = lambda: {"handshake_ms": 1000, "rtt_ms": 1000, "variation_ms": 1000,
                                        "timing_ms": 10000, "peer_ip": "192.0.2.1", "establishments": 8}
            if outcome == "rotation":
                alice.trust_input = original_input
                alice.guard.key_started -= 301
            await wait_for(lambda: alice.pending and bob.pending)
            alice.trust_input = original_input
            with pytest.raises(Exception):
                await bob.send_chat("blocked across recovery")
            if outcome == "unavailable":
                async def unavailable():
                    raise OSError("unavailable")
                alice.establish = unavailable
            if outcome == "changed":
                original_establish = alice.establish
                async def changed():
                    connection = await original_establish()
                    connection.metrics.session = replace(connection.metrics.session, relationship_id="0" * 64)
                    return connection
                alice.establish = changed
            await asyncio.gather(alice.confirm(alice.pending["id"], "MATCH"),
                                 bob.confirm(bob.pending["id"], "MISMATCH" if outcome == "MISMATCH" else "MATCH"))
            if outcome in {"MATCH", "rotation"}:
                await wait_for(lambda: alice.gate.state == bob.gate.state == State.ACTIVE)
                assert alice.guard.context.session_id != old_session
                assert alice.guard.context.relationship_id == relationship
                assert alice.gate.connection.info.key_id != old_session + ":tls-traffic"
                assert alice.messages[0]["text"] == bob.messages[0]["text"] == "conversation survives recovery"
                await bob.send_chat("after recovery")
                await wait_for(lambda: not bob.deliveries)
            else:
                await wait_for(lambda: alice.gate.state == State.RESTRICTED)
                assert not alice.gate.connection.info.connected
        finally:
            await asyncio.wait_for(alice.close(), 3)
            await asyncio.wait_for(bob.close(), 3)
    asyncio.run(run())
