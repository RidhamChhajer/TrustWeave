import asyncio
from dataclasses import replace
from time import perf_counter

from chat.alice import AliceRuntime
from chat.coordinator import State
from tests.test_chat_bob import make_bob
from tests.test_chat_messages import activate
from tests.test_chat_verification import wait_for


def test_induced_latency_trigger_restore_and_recovery(tmp_path):
    bob, bundles, passwords = make_bob(tmp_path)
    bob.config = replace(bob.config, heartbeat_seconds=0.05)
    bob.latency_seconds = 0.3
    alice = AliceRuntime(bundles["alice"], bob.config, tmp_path / "alice.db")
    async def run():
        try:
            await activate(alice, bob, passwords)
            await wait_for(lambda: alice.guard.engine.score > 96)
            await alice.set_demo_mode("latency")
            await wait_for(lambda: bob.mode == "latency")
            started = perf_counter()
            await alice.send_chat("delayed real message")
            await wait_for(lambda: alice.pending and bob.pending)
            assert perf_counter() - started >= 0.25
            assert alice.guard.last_raw["rtt_ms"] >= 250
            assert alice.guard.last_decision.reason == "sudden_drop"
            assert alice.telemetry()["condition_label"] == "REAL INDUCED CONDITION"
            await alice.set_demo_mode("normal")
            await wait_for(lambda: bob.mode == "normal")
            await asyncio.gather(alice.confirm(alice.pending["id"], "MATCH"), bob.confirm(bob.pending["id"], "MATCH"))
            await wait_for(lambda: alice.gate.state == bob.gate.state == State.ACTIVE)
        finally:
            await asyncio.wait_for(alice.close(), 3)
            await asyncio.wait_for(bob.close(), 3)
    asyncio.run(run())


def test_continuity_only_input_and_real_bounded_burst(tmp_path):
    bob, bundles, passwords = make_bob(tmp_path)
    alice = AliceRuntime(bundles["alice"], bob.config, tmp_path / "alice.db")
    async def run():
        try:
            await activate(alice, bob, passwords)
            raw = alice.trust_input()
            await alice.set_demo_mode("ip_change")
            changed = alice.trust_input()
            assert changed["peer_ip"] == "192.0.2.1"
            assert {k: v for k, v in raw.items() if k != "peer_ip"} == {k: v for k, v in changed.items() if k != "peer_ip"}
            assert alice.gate.connection.metrics.session.peer_ip == "127.0.0.1"
            await alice.set_demo_mode("normal")
            assert alice.trust_input()["peer_ip"] == "127.0.0.1"
            await alice.set_demo_mode("reconnect_burst")
            await asyncio.wait_for(alice.demo_task, 5)
            assert alice.gate.state == bob.gate.state == State.ACTIVE
            assert alice.store.db.execute("SELECT count(*) FROM sessions").fetchone()[0] == 4
            assert alice.trust_input()["establishments"] == 4
            await alice.set_demo_mode("normal")
            assert alice.telemetry()["condition_label"] == "NORMAL OBSERVATION"
        finally:
            await asyncio.wait_for(alice.close(), 3)
            await asyncio.wait_for(bob.close(), 3)
    asyncio.run(run())
