# Controlled evaluation methodology

Run `python -m experiments.evaluation`. JSON raw traces and summaries are saved under
`artifacts/evaluation/`. These runs use real mutually authenticated TLS, but synthetic
contextual inputs and automatic simulated OOB answers. They are not real attacks.

- Verification frequency divides requests by every actual TLS epoch, including post-verification reconnects.
- False verification frequency divides non-bootstrap requests on wholly normal observed sessions by those sessions.
  Epochs containing any anomalous sample are excluded from this denominator. A required cold-start request is not false.
- An anomaly episode is a contiguous run of labelled anomalous observations. Detection means at least one verification
  request within that episode, not successful identification of an attacker. No episodes produces null, not 100%.
- Trigger latency starts at the first episode input injection and ends at responder dispatch. It includes local
  assessment/audit work. Observation delay is also reported because this accelerated runner has no realistic sampling cadence.
- Verification overhead measures responder dispatch through completion of assessment, including database writes and TLS
  re-establishment. It excludes real human response time; it must not be presented as real-world OOB latency.
- Recovery reports pre-episode score, final anomalous pre-verification score, and last subsequent normal post-verification
  score, or null when no recovery window exists. The configured successful-verification floor of 75 is not hidden.

Thresholds remain the declared defaults (80/50, delta 10, alpha .3, equal weights).
Repeated verification during persistent degradation is retained in raw results, not filtered out.

## Sensitivity protocol

`python -m experiments.sensitivity` runs an explicitly predeclared, one-factor-at-a-time
sweep across normal, gradual and sudden traces. Variants: alpha .15/.30/.50; high threshold
70/80/90; low threshold 40/50/60; drop threshold 5/10/20; equal, continuity-heavy and
latency-heavy weights. Eleven distinct configurations, 33 runs. No result is used to
automatically change defaults. All raw traces and the CSV comparison table are retained.
This small sweep exposes sensitivity, not an optimized or statistically validated policy.
The high threshold currently changes CONTINUE versus MONITOR only; both retain the same
low/drop verification rules, so identical verification counts for that factor are expected.
