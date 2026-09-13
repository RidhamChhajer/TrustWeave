"""Timing-only measurements. Callers never pass message bytes to this module."""

from collections import deque
import math
from statistics import pstdev
from time import perf_counter

from network.session import SessionContext
from trust.signal_collector import ContextSignalCollector


class SessionMetrics:
    def __init__(self, session: SessionContext, collector: ContextSignalCollector,
                 handshake_ms: float | None, source: str):
        self.session = session
        self.collector = collector
        self._last_frame: dict[str, float] = {}
        self._rtts: deque[float] = deque(maxlen=32)
        if handshake_ms is not None:
            self._validate_duration(handshake_ms)
        collector.session_started(session)
        collector.record(session, "handshake_latency_ms", handshake_ms, source)
        collector.record(session, "rtt", None, "unavailable")

    @staticmethod
    def _validate_duration(value: float) -> None:
        if type(value) not in (float, int) or not math.isfinite(value) or value < 0:
            raise ValueError("duration must be nonnegative and finite")

    def frame(self, direction: str) -> None:
        if direction not in {"sent", "received"}:
            raise ValueError("invalid direction")
        now = perf_counter()
        previous = self._last_frame.get(direction)
        self._last_frame[direction] = now
        self.collector.record(self.session, "communication_timing",
                              {"direction": direction, "interval_ms": None if previous is None else (now - previous) * 1000},
                              "frame_completion")

    def record_round_trip(self, elapsed_ms: float, *, source="application_echo") -> None:
        """Application echo round trip, including peer processing; not kernel TCP RTT."""
        self._validate_duration(elapsed_ms)
        if source not in {"application_echo", "authenticated_heartbeat"}:
            raise ValueError("invalid round-trip source")
        self._rtts.append(elapsed_ms)
        self.collector.record(self.session, "rtt",
                              {"latest_ms": elapsed_ms, "variation_ms": pstdev(self._rtts) if len(self._rtts) > 1 else None,
                               "sample_count": len(self._rtts)}, source)
