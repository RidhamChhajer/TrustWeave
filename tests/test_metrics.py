import asyncio
from dataclasses import replace
from datetime import datetime
from time import perf_counter

import pytest

from client.bob import echo
from config.settings import Settings
from network.metrics import SessionMetrics
from network.secure import SecureServer, connect
from network.session import SessionContext
from trust.signal_collector import ContextSignalCollector


def test_raw_measurements_missing_values_and_rolling_window(monkeypatch):
    clock = [0]
    monkeypatch.setattr("trust.signal_collector.monotonic", lambda: clock[0])
    session = SessionContext.create("1" * 32, "a" * 64, "b" * 64, "127.0.0.1")
    reverse = SessionContext.create("2" * 32, "b" * 64, "a" * 64, "127.0.0.1")
    assert session.relationship_id == reverse.relationship_id
    collector = ContextSignalCollector(capacity=20)
    metrics = SessionMetrics(session, collector, None, "unavailable")
    assert collector.measurements[-1].raw_value is None
    metrics.record_round_trip(10)
    assert collector.measurements[-1].raw_value["variation_ms"] is None
    metrics.record_round_trip(20)
    assert collector.measurements[-1].raw_value["variation_ms"] == 5
    metrics.frame("sent")
    assert collector.measurements[-1].raw_value["interval_ms"] is None
    metrics.frame("sent")
    assert collector.measurements[-1].raw_value["interval_ms"] >= 0
    clock[0] = 1
    collector.session_started(reverse)
    assert collector.measurements[-2].raw_value["count"] == 2
    clock[0] = 61
    collector.session_started(reverse)
    assert collector.measurements[-2].raw_value["count"] == 1
    for item in collector.measurements:
        assert datetime.fromisoformat(item.timestamp).tzinfo is not None
        assert item.normalized_value is None
        assert item.relationship_id == session.relationship_id


def test_collection_rejects_payloads_and_invalid_durations():
    session = SessionContext.create("1" * 32, "a" * 64, "b" * 64, "127.0.0.1")
    collector = ContextSignalCollector(capacity=2)
    metrics = SessionMetrics(session, collector, 1.0, "tls_handshake")
    assert len(collector.measurements) == 2
    for value in (b"private message", -1, float("nan")):
        with pytest.raises(ValueError):
            metrics.record_round_trip(value)
    with pytest.raises(ValueError):
        collector.record(session, "rtt", {"payload": b"private message"}, "application_echo")


def test_live_tls_metadata_stream_and_reconnect(identities):
    creds, passwords = identities
    collector = ContextSignalCollector()
    marker = b"payload must not enter metadata"
    async def run():
        settings = Settings(port=0)
        async with await SecureServer.start(settings, creds["bob"], lambda: passwords["bob"], echo) as server:
            for _ in range(2):
                async with await connect(replace(settings, port=server.port), creds["alice"],
                                         lambda: passwords["alice"], collector=collector) as connection:
                    for _ in range(2):
                        start = perf_counter()
                        await connection.send(marker)
                        assert await connection.receive() == marker
                        connection.metrics.record_round_trip((perf_counter() - start) * 1000)
                    assert connection.metrics.session.session_id == connection.info.session_id
            server_ids = {r.relationship_id for r in server.collector.measurements}
            assert server_ids == {r.relationship_id for r in collector.measurements}
    asyncio.run(run())
    records = collector.measurements
    assert {r.signal_name for r in records} == {"handshake_latency_ms", "rtt", "session_continuity",
                                               "communication_timing", "session_establishments"}
    assert len({r.session_id for r in records}) == 2
    assert [r.raw_value["count"] for r in records if r.signal_name == "session_establishments"] == [1, 2]
    assert marker.decode() not in repr(records)
    assert all(r.normalized_value is None for r in records)
