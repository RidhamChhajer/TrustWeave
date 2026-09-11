"""Bounded in-memory stream of raw metadata. No normalization or scoring."""

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from time import monotonic
import ipaddress
import math

from network.session import SessionContext


@dataclass(frozen=True)
class Measurement:
    timestamp: str
    session_id: str
    relationship_id: str
    signal_name: str
    raw_value: float | dict | None
    normalized_value: None
    source: str


class ContextSignalCollector:
    def __init__(self, capacity: int = 1024):
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self._records: deque[Measurement] = deque(maxlen=capacity)
        self._establishments: deque[tuple[float, str]] = deque()

    @property
    def measurements(self) -> tuple[Measurement, ...]:
        return tuple(self._records)

    def record(self, session: SessionContext, signal: str, raw: float | dict | None, source: str) -> None:
        shapes = {
            "handshake_latency_ms": set(), "rtt": {"latest_ms", "variation_ms", "sample_count"},
            "session_establishments": {"count", "window_seconds"},
            "session_continuity": {"peer_ip"}, "communication_timing": {"direction", "interval_ms"},
        }
        if signal not in shapes or source not in {"session_events", "authenticated_transport", "unavailable",
                                                  "tcp_tls_connect", "tls_handshake", "frame_completion", "application_echo"}:
            raise ValueError("unknown metadata signal or source")
        if raw is not None:
            if signal == "handshake_latency_ms":
                fields = {"duration": raw}
            elif type(raw) is dict and raw.keys() == shapes[signal]:
                fields = raw
            else:
                raise ValueError("invalid metadata fields")
            for key, value in fields.items():
                if key == "peer_ip":
                    ipaddress.ip_address(value)
                elif key == "direction":
                    if value not in {"sent", "received"}:
                        raise ValueError("invalid metadata direction")
                elif value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value < 0):
                    raise ValueError("metadata must contain nonnegative measurements")
        if isinstance(raw, dict):
            raw = raw.copy()
        self._records.append(Measurement(datetime.now(timezone.utc).isoformat(), session.session_id,
                                         session.relationship_id, signal, raw, None, source))

    def session_started(self, session: SessionContext) -> None:
        now = monotonic()
        while self._establishments and self._establishments[0][0] <= now - 60:
            self._establishments.popleft()
        self._establishments.append((now, session.relationship_id))
        count = sum(relationship == session.relationship_id for _, relationship in self._establishments)
        self.record(session, "session_establishments", {"count": count, "window_seconds": 60}, "session_events")
        self.record(session, "session_continuity", {"peer_ip": session.peer_ip}, "authenticated_transport")
