import pytest
import sqlite3

from storage.relationship_store import RelationshipStore
from trust.trust_engine import SIGNALS, TrustEngine


def test_relationship_survives_reopen_and_isolated_sessions(tmp_path):
    path = tmp_path / "history.db"
    with RelationshipStore(path) as store:
        row = store.start_session("1" * 32, "a" * 64)
        engine = TrustEngine(initial=row["trust"])
        result = engine.assess(dict.fromkeys(SIGNALS, 100))
        store.assessment("1" * 32, result)
        store.finish_session("1" * 32)
    with RelationshipStore(path) as store:
        row = store.start_session("2" * 32, "a" * 64)
        assert row["trust"] == result.score
        assert TrustEngine(initial=row["trust"]).score == result.score
        assert store.relationship("b" * 64)["trust"] == 45
        with pytest.raises(sqlite3.IntegrityError):
            store.start_session("2" * 32, "a" * 64)
