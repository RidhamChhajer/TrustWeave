import asyncio

import pytest

from chat.coordinator import Coordinator, State
from chat.protocol import envelope
from config.settings import Settings
from network.connection import ConnectionFailure
from network.secure import SecureServer, connect


def test_state_and_bounded_queue():
    from chat.config import ChatConfig
    gate = Coordinator("alice", ChatConfig(queue_size=1))
    message = envelope("chat", "alice", text="gated marker")
    with pytest.raises(ConnectionFailure):
        gate.queue_chat(message)
    gate.transition(State.CONNECTING)
    gate.transition(State.VERIFYING)
    gate.transition(State.ACTIVE)
    gate.queue_chat(message)
    with pytest.raises(ConnectionFailure):
        gate.queue_chat(message)
    gate.transition(State.VERIFYING)
    assert not gate.outbox
    gate.transition(State.RESTRICTED)
    with pytest.raises(ConnectionFailure):
        gate.transition(State.ACTIVE)


def test_real_tls_gate_and_send_race(identities):
    creds, passwords = identities
    async def run():
        bob = Coordinator("bob")
        accepted = asyncio.Event()
        stop = asyncio.Event()
        async def handler(connection):
            bob.transition(State.CONNECTING)
            bob.attach(connection)
            accepted.set()
            await stop.wait()
        async with await SecureServer.start(Settings(port=0), creds["bob"], lambda: passwords["bob"], handler) as server:
            alice = Coordinator("alice")
            alice.transition(State.CONNECTING)
            alice.attach(await connect(Settings(port=server.port), creds["alice"], lambda: passwords["alice"]))
            await accepted.wait()
            try:
                await alice.control(envelope("ping", "alice"))
                assert (await bob.receive())["type"] == "ping"
                alice.transition(State.ACTIVE)
                alice.queue_chat(envelope("chat", "alice", text="blocked inbound"))
                await alice.flush_one()
                assert await bob.receive() is None
                bob.transition(State.ACTIVE)
                await alice.connection._send_lock.acquire()
                alice.queue_chat(envelope("chat", "alice", text="must not cross gate"))
                pending = asyncio.create_task(alice.flush_one())
                await asyncio.sleep(0)
                alice.transition(State.VERIFYING)
                alice.connection._send_lock.release()
                with pytest.raises(ConnectionFailure):
                    await pending
                await alice.control(envelope("ping", "alice"))
                assert (await bob.receive())["type"] == "ping"
            finally:
                stop.set()
                await alice.connection.close()
    asyncio.run(run())
