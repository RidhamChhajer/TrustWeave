import asyncio
from dataclasses import replace
import pytest

from client.bob import echo
from config.settings import Settings
from network.connection import ConnectionFailure
from network.secure import SecureServer, connect
from storage.relationship_store import RelationshipStore
from verification.session_guard import SessionGuard
from verification.verification import Outcome


def test_live_gate_pending_pass_and_failure(identities):
    creds, passwords = identities
    async def run():
        settings = Settings(port=0)
        async with await SecureServer.start(settings, creds["bob"], lambda: passwords["bob"], echo) as server:
            for outcome in (Outcome.SUCCESS, Outcome.FAILURE):
                with RelationshipStore(":memory:") as store:
                    async with await connect(replace(settings, port=server.port), creds["alice"], lambda: passwords["alice"]) as connection:
                        async def responder(request):
                            with pytest.raises(ConnectionFailure):
                                await connection.send(b"must stay blocked")
                            return outcome
                        async def reconnect():
                            return await connect(replace(settings, port=server.port), creds["alice"], lambda: passwords["alice"])
                        guard = SessionGuard(connection, store, responder, reconnect=reconnect)
                        with pytest.raises(ConnectionFailure):
                            await connection.send(b"not verified")
                        await guard.assess({})
                        if outcome == Outcome.SUCCESS:
                            assert guard.connection.info.session_id != connection.info.session_id
                            await guard.connection.send(b"allowed")
                            assert await guard.connection.receive() == b"allowed"
                            await guard.close()
                        else:
                            assert guard.restricted and not connection.info.connected
    asyncio.run(run())
