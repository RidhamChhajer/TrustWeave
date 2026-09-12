"""Bounded in-memory stream of raw metadata. No normalization or scoring."""

from collections import deque
from dataclasses import dataclass, replace
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
    observed_at: float


class ContextSignalCollector:
    def __init__(self, capacity: int = 1024):
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self._records: deque[Measurement] = deque(maxlen=capacity)
        self._establishments: deque[tuple[float, str]] = deque()

    @property
    def measurements(self) -> tuple[Measurement, ...]:
        return tuple(replace(r, raw_value=r.raw_value.copy()) if isinstance(r.raw_value, dict) else r for r in self._records)

    def record(self, session: SessionContext, signal: str, raw: float | dict | None, source: str,
               *, observed_at: float | None = None) -> None:
        now = monotonic()
        explicit_time = observed_at is not None
        observed_at = now if observed_at is None else observed_at
        if not math.isfinite(observed_at) or observed_at > now or now - observed_at > 30:
            raise ValueError("stale or invalid observation time")
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
        direction = raw.get("direction") if isinstance(raw, dict) else None
        for previous in reversed(self._records):
            previous_direction = previous.raw_value.get("direction") if isinstance(previous.raw_value, dict) else None
            if (previous.session_id, previous.signal_name, previous_direction) == (session.session_id, signal, direction):
                # Windows monotonic clocks can assign equal times to distinct local events.
                # Explicit imported timestamps must still reject replayed observations.
                if observed_at < previous.observed_at or (explicit_time and observed_at == previous.observed_at):
                    raise ValueError("duplicate or out-of-order observation")
                break
        self._records.append(Measurement(datetime.now(timezone.utc).isoformat(), session.session_id,
                                         session.relationship_id, signal, raw, None, source, observed_at))

    def session_started(self, session: SessionContext) -> None:
        now = monotonic()
        while self._establishments and self._establishments[0][0] <= now - 60:
            self._establishments.popleft()
        self._establishments.append((now, session.relationship_id))
        count = sum(relationship == session.relationship_id for _, relationship in self._establishments)
        self.record(session, "session_establishments", {"count": count, "window_seconds": 60}, "session_events")
        self.record(session, "session_continuity", {"peer_ip": session.peer_ip}, "authenticated_transport")
