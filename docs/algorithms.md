# Algorithms and initial calibration

Phase 6 normalizes each of five consistency signals into 0–100. Values at or below
1.5 times the reference receive 100; a linear ramp reaches 0 at 4 times the reference.
Timing uses the larger of observed/reference and reference/observed, catching both
bursts and gaps. RTT uses the lower score of latency and available variation.
Continuity is 100 for the known peer IP, 0 for a changed IP, and 50 if no baseline exists.
Establishment counts score 100 through one per minute, declining to 0 at eight.
Missing inputs score 50 explicitly, rather than silently appearing healthy.

Initial references are handshake 50 ms, echo RTT 50 ms, variation 10 ms and inter-frame
timing 100 ms. These are declared prototype starting values, not universal network
constants. `Baselines` and `NormalizationPolicy` make them replaceable. Peer IP is not
device authentication; latency includes scheduling/congestion. All scores describe
contextual consistency, never proof of an attack. Raw measurements remain unchanged.

Phase 7 combines all five normalized inputs with equal 0.2 weights initially, because
no empirical evidence justifies favoring a signal yet. Weights must sum to one.
EMA: S = alpha * current + (1-alpha) * previous, with alpha=0.3 and initial S=45.
Policy objects validate values; missing raw signals already map to 50 in normalization.
New relationships will require verification independently of improvements in metadata.

Phase 8 exposes delta = current S - previous S separately from S. It is a difference
per assessment, not a derivative per second; assessment cadence must be fixed in
comparisons. A 93→71 drop yields -22 even though 71 exceeds a low threshold of 50.

## Trigger and state transitions

Evaluate in order: restricted -> RESTRICT; delta <= -10 -> VERIFY_IMMEDIATELY;
unverified relationship -> VERIFY; score < 50 -> VERIFY; score >= 80 -> CONTINUE;
otherwise MONITOR. Thus a good absolute score never masks a sufficiently sharp drop.

```
authenticated TLS -> unverified/gated -> simulated comparison
MATCH -> verified -> fresh TLS -> allowed
MISMATCH / cancel / timeout / storage uncertainty -> restricted -> closed
verified -> context trigger -> gated -> comparison
```

Verification outcomes are typed, not read from contextual metadata. Pending request IDs
prevent stale dashboard responses. Success raises trust to max(current, verified_floor=75)
and updates the authenticated peer-IP baseline. It does not erase an ongoing anomaly.
Numerical baseline learning is not implemented; persisted defaults remain explicit.

## Key lifecycle

Successful required verification closes the old channel and establishes a new mutual-TLS
session with the same pinned relationship. Normal sessions rotate when an assessment
finds an age >= 300 seconds. High trust never extends this limit. The deadline is assessed
at observation boundaries, not by a separate hard real-time timer. Failure closes the
session; recovery requires a new verified connection. Identity keys remain unchanged.

## Signal interpretation

The historical “renegotiation” input is actually successful TLS connection establishments
per relationship in a rolling 60-second collector window; TLS 1.3 does not renegotiate.
It includes legitimate verification-induced reconnects. That feedback can lower contextual
scores under frequent reconnects. Experiment counts are deliberately controlled metadata,
not claims about observed live counts. The live dashboard assesses every 500ms and uses
a corresponding 500ms timing baseline. Controlled experiments use the declared 100ms baseline.
