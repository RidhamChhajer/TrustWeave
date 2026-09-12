"""Simulated out-of-band comparison, not proof of a separate trusted channel."""

import asyncio
from dataclasses import dataclass
from enum import Enum
import uuid
import math


class Outcome(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"


@dataclass(frozen=True)
class VerificationRequest:
    id: str
    session_id: str
    pair_fingerprint: str
    reason: str
    simulated: bool = True

    @classmethod
    def create(cls, session_id, relationship_id, reason):
        # Relationship ID already hashes both authenticated public identity credentials.
        display = " ".join(relationship_id[i:i+8].upper() for i in range(0, 64, 8))
        return cls(uuid.uuid4().hex, session_id, display, reason)


async def verify(request, responder, timeout=30.0):
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("verification timeout must be positive")
    try:
        result = await asyncio.wait_for(responder(request), timeout)
        return result if isinstance(result, Outcome) else Outcome.FAILURE
    except asyncio.TimeoutError:
        return Outcome.TIMEOUT
    except asyncio.CancelledError:
        raise
    except Exception:
        return Outcome.FAILURE
