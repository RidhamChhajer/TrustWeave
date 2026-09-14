# Measured trust calibration pilot

Run `.venv314\Scripts\python.exe -m experiments.measured_calibration` from the repository root. It writes `artifacts/measured-calibration.json`, containing metadata observations and results, with no credentials or chat content. Temporary identities are generated for this experiment.

Unlike the deterministic metadata experiments, this pilot measures eight independent loopback TLS sessions. Each has 20 authenticated echoes at a nominal 50 ms cadence. Four sessions add a real 250 ms server delay during the final five observations. This accelerated cadence matches the replay baseline; it is not the normal chat's one-second cadence.

Four whole sessions form the training split; four different sessions are held out. The candidate list is fixed: EMA alpha 0.15, 0.30 and 0.50 with the existing equal weights and thresholds. Selection minimizes sessions with false prompts, then maximizes induced sessions detected; ties prefer the default. Replay starts at the post-verification trust floor and stops at the first prompt. Human decisions and recovery are outside this experiment.

Recorded on 2026-09-14, Windows / Python 3.14.7 / OpenSSL 3.5.7:

| EMA alpha | Training sessions with false prompts (4 total) | Induced sessions detected (2 total) |
|---|---:|---:|
| 0.15 | 0 | 0 |
| 0.30 (default) | 0 | 2 |
| 0.50 | 0 | 2 |

The selected default produced no false prompts across four held-out sessions and detected delay in both held-out induced sessions. Timing is machine-dependent, so reruns may differ.

This is a small engineering pilot on one machine, not a validated security model. It cannot estimate real-world false-positive rates or MITM detection accuracy. Equal weights and normalization thresholds remain uncalibrated; no live policy was changed. Meaningful tuning still needs consented metadata from multiple real networks, longer sessions, legitimate network changes and independently labelled attack scenarios, with evaluation separated by device/network/session.
