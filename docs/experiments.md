# Experiment scenarios and measured results

Setup: local Python 3.10.11/OpenSSL 1.1.1t, actual mutual TLS echo exchanges, independently
generated identities, temporary SQLite stores, deterministic synthetic raw metadata and
automatic simulated verification. Defaults: alpha .3, equal weights, thresholds 80/50/-10.
TLS epochs/timing vary across executions; contextual score trajectories are deterministic.

| Command suffix (`python -m experiments.<name>`) | Scenario and measured outcome |
|---|---|
| normal | 12 observations, one required bootstrap verification, zero unnecessary requests; final 99.5057 |
| gradual | 12 normal then 30 increasing-severity observations; first low-score trigger tick 30, score 47.5204, delta -3.8516; 13 total requests |
| sudden | Warm history then combined latency/continuity/timing/establishment anomaly: 99.5057 -> 69.6540, delta -29.8517; immediate trigger above 50; recovery 97.0588 |
| new_relationship | Same Alice, distinct Charlie: initial 45, conservative verification, learning to 97.9411; Bob history isolated |
| established | Equal eight-observation cold/established windows: 1 versus 0 requests; later sudden drop still triggers |
| failure | MISMATCH closes transport and rejects an actual send; MATCH on a fresh session restores delivery; final 78.7578 |

All commands save raw inputs, before/after scores, decisions, identifiers, timestamps,
outcomes and audit to artifacts. No plaintext or TLS secrets are exported.

`evaluation` reruns all six and saves aggregate metrics; see evaluation.md for exact
denominators. One measured run: sudden request dispatch 5.2486ms; gradual trigger delay
18 observations. These accelerated local timings do not model human/network attack latency.

`sensitivity` runs 11 predeclared configurations across three traces. Gradual delay
varied 15–22 observations and requests 3–15; all tested sudden episodes triggered on
the first anomalous observation. High-threshold variation affected state labels, not
verification counts. Tables/raw results are in artifacts/sensitivity; defaults were not tuned.

Limitations: small deterministic scenario set, no real attacks or statistical generalization,
no realistic human OOB delays, arbitrary initial calibration, repeated prompts under
persistent anomaly, and no numerical-baseline learning. These results demonstrate behavior,
not improved security over a production messaging system.
