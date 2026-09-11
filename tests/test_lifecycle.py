from lifecycle.key_controller import key_action
from verification.trigger_engine import decide
from verification.verification import Outcome


def test_lifecycle_cannot_bypass_verification():
    risk = decide(71, -22, verified=True)
    assert key_action(risk) == "RESTRICT_SESSION"
    assert key_action(risk, Outcome.FAILURE) == "RESTRICT_SESSION"
    assert key_action(risk, Outcome.SUCCESS) == "REESTABLISH_KEY"
    normal = decide(90, 0, verified=True)
    assert key_action(normal, age_seconds=0) == "KEEP_CURRENT_KEY"
    assert key_action(normal, age_seconds=301) == "STANDARD_ROTATION"
