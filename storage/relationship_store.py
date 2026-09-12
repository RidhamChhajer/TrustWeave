"""Persistence operations restricted to known metadata fields."""

from dataclasses import asdict
from datetime import datetime, timezone
import json
import re
import math

from storage.database import open_database
from trust.normalization import Baselines


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def identifier(value, length):
    if not re.fullmatch(r"[0-9a-f]{" + str(length) + "}", value):
        raise ValueError("invalid identity identifier")


class RelationshipStore:
    def __init__(self, path=".state/trust.db"):
        self.db = open_database(path)

    def audit(self, session_id, event, **metadata):
        allowed = {"SESSION_STARTED", "SESSION_TERMINATED", "SESSION_RESTRICTED",
                   "SIGNAL_UPDATED", "TRUST_UPDATED", "DELTA_UPDATED", "VERIFICATION_TRIGGERED",
                   "VERIFICATION_SUCCESS", "VERIFICATION_FAILURE", "KEY_UPDATED"}
        numeric = {"score", "delta", "previous", "handshake", "rtt", "continuity", "timing", "renegotiation"}
        enums = {"reason": {"assessment", "verification_success", "verification_failure", "sudden_drop", "new_relationship", "low_trust"},
                 "outcome": {"SUCCESS", "FAILURE", "CANCELLED", "TIMEOUT"},
                 "action": {"KEEP_CURRENT_KEY", "STANDARD_ROTATION", "REESTABLISH_KEY", "RESTRICT_SESSION"}}
        if event not in allowed:
            raise ValueError("invalid audit event")
        for key, value in metadata.items():
            if key in numeric:
                if type(value) not in (float, int) or not math.isfinite(value) or not -100 <= value <= 100:
                    raise ValueError("invalid audit number")
            elif key in enums and value in enums[key]:
                continue
            elif key == "simulated" and type(value) is bool:
                continue
            else:
                raise ValueError("unapproved audit field")
        row = self.db.execute("SELECT relationship_id,mode FROM sessions WHERE id=?", (session_id,)).fetchone()
        if row is None:
            raise ValueError("unknown audit session")
        metadata["mode"] = row["mode"]
        with self.db:
            self.db.execute("INSERT INTO audit_events(timestamp,session_id,relationship_id,event_type,metadata) VALUES(?,?,?,?,?)",
                            (timestamp(), session_id, row["relationship_id"], event, json.dumps(metadata, allow_nan=False)))

    def relationship(self, relationship_id, initial=45.0):
        identifier(relationship_id, 64)
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO relationships(id,trust,baselines) VALUES(?,?,?)",
                            (relationship_id, initial, json.dumps(asdict(Baselines()))))
        return dict(self.db.execute("SELECT * FROM relationships WHERE id=?", (relationship_id,)).fetchone())

    def start_session(self, session_id, relationship_id, mode="real", initial=45.0):
        identifier(session_id, 32)
        relationship = self.relationship(relationship_id, initial)
        with self.db:
            self.db.execute("INSERT INTO sessions VALUES(?,?,?,?,?,?)",
                            (session_id, relationship_id, timestamp(), None, mode, "ACTIVE"))
        self.audit(session_id, "SESSION_STARTED")
        return relationship

    def assessment(self, session_id, assessment, reason="assessment"):
        if reason not in {"assessment", "verification_success", "verification_failure"}:
            raise ValueError("invalid history reason")
        with self.db:
            self.db.execute("INSERT INTO trust_history(session_id,timestamp,score,delta,reason) VALUES(?,?,?,?,?)",
                            (session_id, timestamp(), assessment.score, assessment.delta, reason))
            self.db.execute("UPDATE relationships SET trust=? WHERE id=(SELECT relationship_id FROM sessions WHERE id=?)",
                            (assessment.score, session_id))
        self.audit(session_id, "TRUST_UPDATED", previous=assessment.previous, score=assessment.score, reason=reason)
        self.audit(session_id, "DELTA_UPDATED", delta=assessment.delta)

    def set_baselines(self, relationship_id, baselines: Baselines):
        with self.db:
            self.db.execute("UPDATE relationships SET baselines=? WHERE id=? AND verified=1",
                            (json.dumps(asdict(baselines)), relationship_id))

    def finish_session(self, session_id, status="CLOSED"):
        if status not in {"CLOSED", "RESTRICTED", "FAILED"}:
            raise ValueError("invalid session status")
        with self.db:
            changed = self.db.execute("UPDATE sessions SET ended=?,status=? WHERE id=? AND ended IS NULL", (timestamp(), status, session_id)).rowcount
        if changed:
            self.audit(session_id, "SESSION_RESTRICTED" if status == "RESTRICTED" else "SESSION_TERMINATED")

    def verification(self, request, outcome):
        if outcome not in {"SUCCESS", "FAILURE", "CANCELLED", "TIMEOUT"}:
            raise ValueError("invalid verification outcome")
        success = outcome == "SUCCESS"
        with self.db:
            self.db.execute("INSERT INTO verification_events VALUES(?,?,?,?,?)",
                            (request.id, request.session_id, timestamp(), outcome, int(request.simulated)))
            self.db.execute("UPDATE relationships SET verified=?,successes=successes+?,failures=failures+?,last_verified=CASE WHEN ? THEN ? ELSE last_verified END WHERE id=(SELECT relationship_id FROM sessions WHERE id=?)",
                            (int(success), int(success), int(not success), int(success), timestamp(), request.session_id))
        self.audit(request.session_id, "VERIFICATION_SUCCESS" if success else "VERIFICATION_FAILURE",
                   outcome=outcome, simulated=request.simulated)

    def key_event(self, session_id, action, key_id):
        identifier(session_id, 32)
        if key_id != session_id + ":tls-traffic":
            raise ValueError("invalid public key epoch identifier")
        if action not in {"KEEP_CURRENT_KEY", "STANDARD_ROTATION", "REESTABLISH_KEY", "RESTRICT_SESSION"}:
            raise ValueError("invalid lifecycle action")
        with self.db:
            self.db.execute("INSERT INTO key_events(session_id,timestamp,action,key_id) VALUES(?,?,?,?)",
                            (session_id, timestamp(), action, key_id))
        self.audit(session_id, "KEY_UPDATED", action=action)

    def restrict_relationship(self, relationship_id):
        with self.db:
            self.db.execute("UPDATE relationships SET verified=0 WHERE id=?", (relationship_id,))

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
