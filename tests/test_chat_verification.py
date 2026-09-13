import asyncio
from itertools import product

import pytest

from chat.alice import AliceRuntime
from chat.coordinator import State
from chat.protocol import ChatProtocolError
from chat.verification import DualVerification, safety_code
from tests.test_chat_bob import make_bob


async def wait_for(predicate, timeout=3):
    async def wait():
        while not predicate():
            await asyncio.sleep(0.005)
    await asyncio.wait_for(wait(), timeout)


@pytest.mark.parametrize("first,second", list(product(["MATCH", "MISMATCH", "CANCEL"], repeat=2)))
def test_all_human_combinations(first, second):
    async def run():
        dual = DualVerification("a" * 32, "b" * 64, "new_relationship")
        dual.decide("alice", dual.id, dual.relationship, first)
        dual.decide("bob", dual.id, dual.relationship, second)
        assert await dual.ready == (first == second == "MATCH")
    asyncio.run(run())


@pytest.mark.parametrize("error", ["stale", "relationship", "duplicate", "conflicting"])
def test_stale_conflicting_decisions(error):
    async def run():
        dual = DualVerification("a" * 32, "b" * 64, "new_relationship")
        dual.decide("alice", dual.id, dual.relationship, "MATCH")
        with pytest.raises(ChatProtocolError):
            dual.decide("alice" if error in {"duplicate", "conflicting"} else "bob",
                        "c" * 32 if error == "stale" else dual.id,
                        "d" * 64 if error == "relationship" else dual.relationship,
                        "MISMATCH" if error == "conflicting" else "MATCH")
        assert not await dual.ready
    asyncio.run(run())


def test_dual_real_runtimes_initial_match(tmp_path):
    bob, bundles, passwords = make_bob(tmp_path)
    alice = AliceRuntime(bundles["alice"], bob.config, tmp_path / "alice.db")
    async def run():
        try:
            await bob.unlock(passwords["bob"].decode())
            await bob.start_server()
            await alice.unlock(passwords["alice"].decode())
            await alice._connect("127.0.0.1")
            await wait_for(lambda: bob.pending and alice.pending)
            assert alice.pending["code"] == bob.pending["code"] == safety_code(alice.guard.context.relationship_id)
            await alice.confirm(alice.pending["id"], "MATCH")
            await asyncio.sleep(0.02)
            assert alice.gate.state == bob.gate.state == State.VERIFYING
            await bob.confirm(bob.pending["id"], "MATCH")
            await wait_for(lambda: alice.gate.state == bob.gate.state == State.ACTIVE)
            assert alice.guard.engine.score >= alice.guard.engine.policy.verified_floor
            assert not alice.pending and not bob.pending
            assert alice.store.db.execute("SELECT simulated FROM verification_events").fetchone()[0] == 0
        finally:
            await alice.close()
            await bob.close()
    asyncio.run(run())


@pytest.mark.parametrize("action", ["mismatch", "timeout", "disconnect"])
def test_real_verification_failure(tmp_path, action):
    from dataclasses import replace
    bob, bundles, passwords = make_bob(tmp_path)
    bob.config = replace(bob.config, verification_timeout=0.2)
    alice = AliceRuntime(bundles["alice"], bob.config, tmp_path / "alice.db")
    async def run():
        try:
            await bob.unlock(passwords["bob"].decode())
            await bob.start_server()
            await alice.unlock(passwords["alice"].decode())
            await alice._connect("127.0.0.1")
            await wait_for(lambda: bob.pending and alice.pending)
            if action == "mismatch":
                await bob.confirm(bob.pending["id"], "MISMATCH")
            elif action == "disconnect":
                await bob.browser_closed()
            await wait_for(lambda: alice.gate.state == bob.gate.state == State.RESTRICTED)
        finally:
            await alice.close()
            await bob.close()
    asyncio.run(run())
