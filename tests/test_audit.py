import json
import pytest
from storage.relationship_store import RelationshipStore
from trust.trust_engine import Assessment


def test_audit_chronology_and_field_boundary(tmp_path):
    path = tmp_path / "audit.db"
    sid, rid = "a" * 32, "b" * 64
    with RelationshipStore(path) as store:
        store.start_session(sid, rid, "simulated")
        store.assessment(sid, Assessment(90, 0, 63))
        store.audit(sid, "VERIFICATION_TRIGGERED", reason="sudden_drop", score=63, delta=-27, simulated=True)
        with pytest.raises(ValueError):
            store.audit(sid, "TRUST_UPDATED", plaintext="PRIVATE_MARKER")
        with pytest.raises(ValueError):
            store.key_event(sid, "KEEP_CURRENT_KEY", "PRIVATE_MARKER")
        store.finish_session(sid, "RESTRICTED")
        store.finish_session(sid)
    with RelationshipStore(path) as store:
        rows = store.db.execute("SELECT * FROM audit_events ORDER BY id").fetchall()
        assert [r["event_type"] for r in rows] == ["SESSION_STARTED", "TRUST_UPDATED", "DELTA_UPDATED", "VERIFICATION_TRIGGERED", "SESSION_RESTRICTED"]
        assert all(r["relationship_id"] == rid and json.loads(r["metadata"])["mode"] == "simulated" for r in rows)
        assert "PRIVATE_MARKER" not in str([dict(r) for r in rows])
