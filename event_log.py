"""Small event API: fixed event names and strictly typed, non-secret fields."""

from datetime import datetime, timezone
import json
import logging
import re

LOGGER = logging.getLogger("adaptive_trust")
EVENTS = {
    "APPLICATION_READY", "SERVER_STARTED", "SESSION_STARTED", "SESSION_CLOSED",
    "CONNECTION_REJECTED", "FRAME_SENT", "FRAME_RECEIVED", "SESSION_FAILED",
    "HANDSHAKE_COMPLETED", "IDENTITY_CREATED", "DEMO_SUCCESS",
}
FIELDS = {"session_id", "byte_count", "elapsed_ms", "port", "protocol", "cipher"}


def configure_logging() -> None:
    if not LOGGER.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)


def event(name: str, **fields: object) -> None:
    if name not in EVENTS or fields.keys() - FIELDS:
        raise ValueError("unsupported event or field")
    for key, value in fields.items():
        if key in {"byte_count", "port"}:
            valid = type(value) is int and value >= 0
        elif key == "elapsed_ms":
            import math
            valid = type(value) in (int, float) and math.isfinite(value) and value >= 0
        elif key == "session_id":
            valid = isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{32}", value))
        elif key == "protocol":
            valid = value == "TLSv1.3"
        else:
            valid = value in {"TLS_AES_256_GCM_SHA384", "TLS_AES_128_GCM_SHA256", "TLS_CHACHA20_POLY1305_SHA256"}
        if not valid:
            raise ValueError("invalid event field")
    LOGGER.info(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), "event": name, **fields}))
