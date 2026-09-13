"""Metadata-only presentation shared by the existing dashboard and chat."""

from dataclasses import asdict


def guard_snapshot(guard):
    return {
        "session": asdict(guard.connection.info) if guard else None,
        "score": guard.engine.score if guard else None,
        "delta": guard.last_assessment.delta if guard and guard.last_assessment else None,
        "decision": asdict(guard.last_decision) if guard and guard.last_decision else None,
        "pending": asdict(guard.pending) if guard and guard.pending else None,
        "restricted": guard.restricted if guard else False,
        "outcome": guard.last_outcome if guard else None,
        "key_action": guard.last_key_action if guard else None,
        "key_id": guard.connection.info.key_id if guard else None,
        "signals": dict(guard.last_raw) if guard else {},
    }
