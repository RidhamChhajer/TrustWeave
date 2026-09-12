import asyncio
import sqlite3
from time import monotonic
import pytest
from trust.normalization import Baselines, normalize_snapshot
from trust.signal_collector import ContextSignalCollector
from network.session import SessionContext
from verification.session_guard import SessionGuard
from verification.verification import Outcome
from storage.relationship_store import RelationshipStore
from network.secure import SecureServer, connect
from network.connection import ConnectionFailure
from config.settings import Settings
from client.bob import echo


def test_metadata_edge_boundaries():
    assert normalize_snapshot({})["rtt"] == 50
    assert normalize_snapshot({"rtt_ms": 1e300})["rtt"] == 0
    for raw in ({"verified": True}, {"rtt_ms": True}, {"timing_ms": float("nan")}, {"peer_ip": "message"}):
        with pytest.raises(ValueError):
            normalize_snapshot(raw)
    with pytest.raises(ValueError):
        Baselines(timing_ms=float("nan"))
    collector = ContextSignalCollector()
    session = SessionContext.create("1"*32, "a"*64, "b"*64, "127.0.0.1")
    now = monotonic()
    raw = {"latest_ms": 10, "variation_ms": 1, "sample_count": 2}
    collector.record(session, "rtt", raw, "application_echo", observed_at=now)
    collector.measurements[0].raw_value["latest_ms"] = 999
    assert collector.measurements[0].raw_value["latest_ms"] == 10
    for when in (now, now-1, now-31):
        with pytest.raises(ValueError):
            collector.record(session, "rtt", raw, "application_echo", observed_at=when)


def test_database_failure_closes_live_session(identities):
    creds, passwords = identities
    async def run():
        async with await SecureServer.start(Settings(port=0), creds["bob"], lambda: passwords["bob"], echo) as server:
            async def reconnect():
                return await connect(Settings(port=server.port), creds["alice"], lambda: passwords["alice"])
            async def respond(request):
                return Outcome.SUCCESS
            store = RelationshipStore(":memory:")
            guard = SessionGuard(await reconnect(), store, respond, reconnect=reconnect)
            store.close()
            with pytest.raises(sqlite3.Error):
                await guard.assess({})
            assert guard.restricted and not guard.connection.info.connected
            with pytest.raises(ConnectionFailure):
                await guard.connection.send(b"blocked")
    asyncio.run(run())
