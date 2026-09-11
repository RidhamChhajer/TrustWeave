"""Independent per-assessment trust change (not a time derivative)."""

import math


def trust_delta(current: float, previous: float) -> float:
    if any(not math.isfinite(x) or not 0 <= x <= 100 for x in (current, previous)):
        raise ValueError("trust scores must be finite and bounded")
    return current - previous
