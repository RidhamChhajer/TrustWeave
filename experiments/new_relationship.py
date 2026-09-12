"""Same Alice, genuinely distinct Charlie identity, shared persistent relationship store."""
from experiments.normal import trace as warmup
from experiments.controller import sample
from experiments.runner import execute


def trace():
    return warmup() + [dict(kind="new_relationship" if i == 0 else "learning", peer="charlie",
                            raw=sample(), anomaly=False, new_session=True) for i in range(8)]


if __name__ == "__main__":
    result = execute(trace(), "artifacts/new-relationship.json")
    rows = result["rows"]
    first = rows[12]
    assert first["relationship_id"] != rows[11]["relationship_id"]
    assert first["before"] == 45 and first["reason"] == "new_relationship"
    assert first["outcome"] == "SUCCESS" and all(r["delivered"] for r in rows)
    assert rows[-1]["after"] > 95
    print(f"NEW_RELATIONSHIP_ACCEPTANCE_PASSED: Charlie starts at {first['before']}; final trust={rows[-1]['after']:.4f}; Bob history isolated")
