"""Persistence operations restricted to known metadata fields."""

from dataclasses import asdict
from datetime import datetime, timezone
import json
import re

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
        return relationship

    def assessment(self, session_id, assessment, reason="assessment"):
        if reason not in {"assessment", "verification_success", "verification_failure"}:
            raise ValueError("invalid history reason")
        with self.db:
            self.db.execute("INSERT INTO trust_history(session_id,timestamp,score,delta,reason) VALUES(?,?,?,?,?)",
                            (session_id, timestamp(), assessment.score, assessment.delta, reason))
            self.db.execute("UPDATE relationships SET trust=? WHERE id=(SELECT relationship_id FROM sessions WHERE id=?)",
                            (assessment.score, session_id))

    def set_baselines(self, relationship_id, baselines: Baselines):
        with self.db:
            self.db.execute("UPDATE relationships SET baselines=? WHERE id=? AND verified=1",
                            (json.dumps(asdict(baselines)), relationship_id))

    def finish_session(self, session_id, status="CLOSED"):
        if status not in {"CLOSED", "RESTRICTED", "FAILED"}:
            raise ValueError("invalid session status")
        with self.db:
            self.db.execute("UPDATE sessions SET ended=?,status=? WHERE id=?", (timestamp(), status, session_id))

    def verification(self, request, outcome):
        if outcome not in {"SUCCESS", "FAILURE", "CANCELLED", "TIMEOUT"}:
            raise ValueError("invalid verification outcome")
        success = outcome == "SUCCESS"
        with self.db:
            self.db.execute("INSERT INTO verification_events VALUES(?,?,?,?,?)",
                            (request.id, request.session_id, timestamp(), outcome, int(request.simulated)))
            self.db.execute("UPDATE relationships SET verified=?,successes=successes+?,failures=failures+?,last_verified=CASE WHEN ? THEN ? ELSE last_verified END WHERE id=(SELECT relationship_id FROM sessions WHERE id=?)",
                            (int(success), int(success), int(not success), int(success), timestamp(), request.session_id))

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
