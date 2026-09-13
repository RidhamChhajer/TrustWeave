"""Strict version-one envelopes carried only inside authenticated TLS frames."""

from collections import OrderedDict
from datetime import datetime, timezone
import json
import re
import uuid


class ChatProtocolError(ValueError):
    def __init__(self):
        super().__init__("Invalid chat protocol message; session must close.")


FIELDS = {
    "chat": {"text"}, "chat_ack": {"chat_id"}, "ping": set(), "pong": {"ping_id"},
    "verify_request": {"request_id", "relationship", "reason", "recovery"},
    "verify_response": {"request_id", "relationship", "decision"},
    "verification_result": {"request_id", "relationship", "result", "recovery"},
    "demo_mode": {"mode"}, "session_notice": {"notice"},
}
BASE = {"version", "id", "type", "sender", "timestamp"}
MODES = {"normal", "latency", "reconnect_burst", "ip_change"}
REASONS = {"new_relationship", "sudden_drop", "low_trust", "manual", "rotation"}
MAX_ENVELOPE = 32768  # JSON escaping can expand 4 KiB text sixfold.


def _hex(value, length=32):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{%d}" % length, value) is not None


def validate(data):
    try:
        kind = data["type"]
        if not isinstance(data, dict) or not isinstance(kind, str) or kind not in FIELDS:
            raise ChatProtocolError()
        if set(data) != BASE | FIELDS[kind] or type(data["version"]) is not int or data["version"] != 1:
            raise ChatProtocolError()
        if not _hex(data["id"]) or data["sender"] not in {"alice", "bob"}:
            raise ChatProtocolError()
        stamp = data["timestamp"]
        if not isinstance(stamp, str) or len(stamp) > 40 or not stamp.endswith(("Z", "+00:00")):
            raise ChatProtocolError()
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        if parsed.utcoffset().total_seconds() != 0:
            raise ChatProtocolError()
        for field in ("chat_id", "ping_id", "request_id", "relationship"):
            if field in data and not _hex(data[field], 64 if field == "relationship" else 32):
                raise ChatProtocolError()
        if kind == "chat":
            value = data["text"]
            if not isinstance(value, str) or not value.strip() or len(value.encode("utf-8")) > 4096:
                raise ChatProtocolError()
        for field, allowed in (("decision", {"MATCH", "MISMATCH", "CANCEL"}),
            ("result", {"SUCCESS", "FAILURE"}), ("mode", MODES), ("reason", REASONS),
            ("notice", {"reconnect", "ready", "restricted", "shutdown"})):
            if field in data and data[field] not in allowed:
                raise ChatProtocolError()
        if "recovery" in data and type(data["recovery"]) is not bool:
            raise ChatProtocolError()
    except (KeyError, TypeError, ValueError, UnicodeError, AttributeError):
        raise ChatProtocolError() from None
    return data


def envelope(kind, sender, **fields):
    return validate({"version": 1, "id": uuid.uuid4().hex, "type": kind, "sender": sender,
                     "timestamp": datetime.now(timezone.utc).isoformat(), **fields})


def encode(data):
    validate(data)
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ChatProtocolError()
        result[key] = value
    return result


def decode(payload):
    try:
        if not isinstance(payload, bytes) or len(payload) > MAX_ENVELOPE:
            raise ChatProtocolError()
        return validate(json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_pairs,
                                   parse_constant=lambda _: (_ for _ in ()).throw(ChatProtocolError())))
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise ChatProtocolError() from None


class DuplicateCache:
    def __init__(self, capacity=2048):
        if type(capacity) is not int or not 1 <= capacity <= 16384:
            raise ValueError("invalid duplicate cache bound")
        self.capacity = capacity
        self.ids = OrderedDict()

    def accept(self, message_id):
        if not _hex(message_id) or message_id in self.ids:
            raise ChatProtocolError()
        self.ids[message_id] = None
        if len(self.ids) > self.capacity:
            self.ids.popitem(last=False)
