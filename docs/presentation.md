# Presentation outline

1. Problem: fixed verification schedules ignore changing communication context.
2. Existing limitation: a high historical score can hide a sharp recent deterioration.
3. Architecture: show architecture.md; TLS provides authentication/confidentiality independently.
4. Core project idea: independent delta trigger plus relationship history and a gated verification workflow.
   Describe it as the project's proposed mechanism, not a legally established novelty claim.
5. Demo: dashboard live session and simulated MATCH; isolated sudden experiment shows
   99.51 -> 69.65, delta -29.85, immediate verification above 50 and fresh TLS after success.
6. Failure/recovery: run experiments.failure; show blocked send followed by verified reconnect.
7. Results: six scenarios, precise metrics and 33-case sensitivity table; include repeated prompts.
8. Security: maintained crypto primitives, pins, encrypted framing, fail-closed uncertainty, no secret logging.
9. Limits: simulated OOB/metadata, local prototype, old runtime, no real attack accuracy claim.
10. Future work: actual trusted-channel verification, empirical calibration, independent peer-side policy,
    production PKI/renewal, audit protection and broader real-network evaluation.
