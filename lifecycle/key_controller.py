from dataclasses import dataclass
import math

from verification.verification import Outcome


@dataclass(frozen=True)
class KeyPolicy:
    rotation_seconds: float = 300.0

    def __post_init__(self):
        if not math.isfinite(self.rotation_seconds) or self.rotation_seconds <= 0:
            raise ValueError("invalid rotation interval")


def key_action(decision, outcome=None, *, age_seconds=0, policy=KeyPolicy()):
    if decision.action == "RESTRICT":
        return "RESTRICT_SESSION"
    if decision.requires_verification:
        if outcome != Outcome.SUCCESS:
            return "RESTRICT_SESSION"
        return "REESTABLISH_KEY"
    return "STANDARD_ROTATION" if age_seconds >= policy.rotation_seconds else "KEEP_CURRENT_KEY"


async def reestablish(connection, reconnect):
    """Close the old channel; require a fresh authenticated TLS connection."""
    previous = connection.info.session_id
    await connection.close()
    replacement = await reconnect()
    if replacement.info.session_id == previous or replacement.info.protocol != "TLSv1.3":
        await replacement.close()
        raise RuntimeError("fresh authenticated session required")
    return replacement
