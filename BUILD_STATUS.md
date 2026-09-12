# Build checkpoint

- Scope: all remaining phases authorized; proceed sequentially with focused checks.
- Current phase: 24 — Quantitative Evaluation (complete).
- Completed phases: 1–24.
- Working preference: concise updates; focused new tests and a single relevant regression run.
- Files: configuration, event logger, smoke entry point, foundation tests, README,
  pytest settings, environment example and ignore rules.
- Decision: mutual TLS 1.3 using Python ssl/OpenSSL; cryptography provisions identities.
- Commands: workspace inspection; `python -m venv .venv`; dependency installation.
- Dependency download initially blocked by sandbox; retried with authorized network access.
- Validation: `.venv/Scripts/python -m pytest -q`: 14 passed in 0.06s;
  `python -m pip check`: no broken requirements; `python -m main`: APPLICATION_READY.
- Commands also completed: `git init`.
- Phase 2 files: client/alice.py, client/bob.py, network/connection.py,
  network/plain.py, package initializers, tests/test_network.py.
- Phase 2 validation: `.venv/Scripts/python -m pytest -q`: 23 passed in 0.43s.
  Real loopback bidirectional exchanges/reconnects, fragmented/coalesced frames,
  oversized/truncated frames, timeouts, concurrent receives and serialized sends passed.
- Phase 3 files: crypto/identity.py, crypto/key_exchange.py, crypto/__init__.py,
  tests/test_crypto.py, tests/tls_helpers.py, tests/__init__.py.
- Phase 3 validation: `.venv/Scripts/python -m pytest -q`: 32 passed in 6.02s.
  Encrypted PKCS#8, distinct P-256 identities, TLS 1.3 mutual certificate validation,
  wrong peer/CA/hostname, missing certificate, malformed crypto input, encrypted
  bidirectional BIO exchanges, and disabled key logging/tickets passed.
- Environment: cryptography's native DLL was blocked inside the Windows sandbox;
  the exact test command passed with approved desktop execution.
- Phase 4 files: network/secure.py and connection.py; client/alice.py, bob.py,
  provision.py, passwords.py, demo.py; tests/conftest.py, test_secure.py, test_cli.py,
  wire_proxy.py; existing framing/crypto tests; README, pytest.ini and this checkpoint.
  Removed network/plain.py (the temporary development connector, recoverable from phase 2).
- Phase 4 validation: `.venv/Scripts/python.exe -m pytest -q`: **50 passed in 2.73s**.
  Includes real TLS wire capture, post-handshake ciphertext corruption rejected before
  delivery, no plaintext/password/private-key markers in application logs, identical
  public session IDs, separate directions, empty/1-MiB frames, reconnects, invalid
  pins/plaintext/TLS1.2, operation/handshake deadlines, active and incomplete-handshake
  shutdown, CLI help/error sanitization, and refusal of echoed password input.
- Regression fixed: closing asyncio.start_server alone left incomplete TLS handshakes
  alive until their timeout. The server now owns raw accepted sockets and TLS tasks via
  loop.connect_accepted_socket; shutdown cancels pending handshakes as well as sessions.
  The new shutdown test first failed, then passed after this correction.
- Final demo: `.venv/Scripts/python.exe -m client.demo` exited 0; actual local sockets
  negotiated TLSv1.3 / TLS_AES_256_GCM_SHA384, exchanged three 96-byte messages in both
  directions, emitted DEMO_SUCCESS, and closed both endpoints. No payload/key output.
- Final dependency check: `.venv/Scripts/python.exe -m pip check`: no broken requirements.
- Final source check: `git diff --check` passed. An earlier elevated invocation omitted
  the repository ownership exception and failed; rerunning under the sandbox owner passed.
- Limitations: experimental local demo, old Python/OpenSSL runtime, trusted local
  development CA/pin provisioning, no production PKI/revocation or human OOB workflow.
  Certificates expire after 30 days. TLS traffic keys remain inside OpenSSL, so key
  compatibility is verified through authenticated decryption, not raw key extraction.
  key_id is a non-secret connection-epoch label, not an exported TLS key identifier.
  Python does not guarantee zeroization; OS permissions must protect credential/pin files.
  Application handlers must cooperate with asyncio cancellation.
- Blockers: none.
- Phase 5: added network/metrics.py, network/session.py, trust/signal_collector.py,
  trust/__init__.py, tests/test_metrics.py; integrated secure connection/frames and Alice
  echo timing. Updated README and this checkpoint.
- Phase 5 evidence: three focused tests added; one complete regression run:
  `.venv/Scripts/python.exe -m pytest -q` — **53 passed in 2.99s**.
- Phase 5 decisions: metadata only, normalized_value=None; symmetric public-identity
  relationship IDs; bounded record stream; peer-IP continuity descriptors; per-direction
  frame timing; measured application-echo RTT/32-sample variation; 60-second successful
  establishment count. Reuse an explicit collector across Alice reconnects; Bob shares
  a collector. Missing readings are None. Counts/history do not persist across restarts.
- Phase 6: trust/normalization.py and docs/algorithms.md; configurable bounded ramps,
  missing-value policy, five-input adapter. Focused check: 1 passed in 0.04s.
- Phase 7: deterministic configurable five-weight EMA; focused checks: 2 passed in 0.04s.
- Phase 8: independent delta property and sharp-drop check; focused checks: 3 passed.
- Phase 9: SQLite relationships, sessions, trust/verification/key histories;
  reopen/identity isolation test passed. Metadata only; .state ignored by Git.
- Phase 10: configurable 80/50/-10 trigger thresholds, explicit decision reasons,
  new-relationship and failed-verification handling; branch check passed.
- Phase 11: identity-pair comparison request, success/failure/cancel/timeout outcomes;
  simulation explicitly labelled; outcome/timeout check passed.
- Phase 12: SessionGuard binds EMA/history/trigger to a transport gate; pending
  verification blocks send/delivery; failure closes session. Live/security checks: 13 passed.
- Phase 13: bounded 300-second lifecycle policy; fresh authenticated reconnect
  helper; no high-trust lifetime extension. Policy check passed.
- Phase 14: metadata→normalization→EMA/delta→trigger→live gate→verification→fresh TLS
  reconnect→history. Two focused checks passed; adaptive live demo succeeded (trust 90.80).
- Phase 15: dashboard/runtime.py, app.py, index.html and tests/test_dashboard.py.
  Loopback-only UI controls real TLS messaging with explicitly simulated human verification;
  displays metadata, trust history, trigger markers and public key epoch identifiers.
  Command: `.venv/Scripts/python.exe -m pytest -q tests/test_dashboard.py`:
  1 passed in 0.23s. No deployment or external services.
- Phase 16: storage/database.py, relationship_store.py, verification/session_guard.py,
  tests/test_audit.py. Ordered persistent audit records tie normalized signals, EMA/delta,
  trigger, simulated verification, key actions and teardown to session/relationship IDs.
  Strict numeric/enum whitelist rejects payload fields; repeated close is idempotent.
  Command: `.venv/Scripts/python.exe -m pytest -q tests/test_audit.py tests/test_dashboard.py`:
  2 passed in 0.30s. Audit is local SQLite, not tamper-evident or remotely replicated.
- Phase 17: experiments/controller.py, runner.py, package and tests/test_experiments.py.
  Deterministic raw-metadata perturbations cover all seven requested anomaly types.
  Runner uses actual mutually authenticated TLS, simulated metadata/OOB labels, real
  reconnects and persisted audit; JSON retains raw inputs, timing and decisions.
  Command: `.venv/Scripts/python.exe -m pytest -q tests/test_experiments.py`: 1 passed in 0.19s.
  Settings/score trajectories are reproducible; randomized identities and wall timings are not.
- Phase 18: experiments/normal.py; raw results artifacts/normal.json (generated, ignored).
  Command: `.venv/Scripts/python.exe -m experiments.normal`: acceptance passed.
  12 session observations, 1 required new-relationship verification, 0 unnecessary
  verifications; minimum 58.5 at bootstrap, final trust 99.50566831424997.
  Each observation starts a session; successful bootstrap adds a fresh TLS epoch.
- Phase 19: experiments/gradual.py; raw results artifacts/gradual.json.
  Command: `.venv/Scripts/python.exe -m experiments.gradual`: acceptance passed.
  42 observations; first degradation trigger tick 30 (zero-based), trust 47.5204,
  delta -3.8516: absolute low threshold, not sudden-drop trigger.
  13 total verifications: bootstrap plus repeated prompts while abnormal inputs persist.
  Successful verification's trust floor does not remove the abnormal condition; no bypass cooldown.
- Phase 20: experiments/sudden.py, dashboard/app.py, index.html, experiment.js,
  tests/test_dashboard.py. Separate labelled dashboard experiment preserves live data.
  `.venv/Scripts/python.exe -m experiments.sudden`: acceptance passed, 19 observations,
  2 verifications; anomaly 99.5057 -> 69.6540, delta -29.8517, immediate trigger above 50;
  successful MATCH caused fresh TLS epoch; recovery reached 97.058775.
  Raw data: artifacts/sudden.json; dashboard runs save artifacts/dashboard-sudden.json.
  `.venv/Scripts/python.exe -m pytest -q tests/test_dashboard.py`: 2 passed in 1.18s,
  including ASGI endpoint and cross-origin rejection. Browser rendering not inspected.
- User renamed .env.example to .env; preserve ignored .env without reading/logging it.
  The tracked .env.example deletion is a user change, excluded from phase commits.
- Phase 21: crypto/identity.py permits explicit Bob/Charlie development certificates;
  experiments/runner.py supports separate pinned peers using the same Alice identity/store;
  experiments/new_relationship.py saves artifacts/new-relationship.json.
  `.venv/Scripts/python.exe -m experiments.new_relationship`: acceptance passed;
  20 observations, 2 bootstrap verifications; Charlie initial 45, final 97.9411425.
  `.venv/Scripts/python.exe -m pytest -q tests/test_crypto.py tests/test_experiments.py`:
  10 passed in 0.30s. Bob trust is not inherited by Charlie.
- Phase 22: experiments/established.py, artifacts/established.json (raw generated data).
  `.venv/Scripts/python.exe -m experiments.established`: acceptance passed;
  equal eight-observation windows: cold 1 required verification, established 0;
  established scores start above 95; independent sudden-drop protection still triggers.
  This measures bootstrap avoidance, not a claim of improved real-world attack detection.
- Phase 23: experiments/failure.py, runner.py and verification/session_guard.py.
  Restriction now also updates the displayed lifecycle state (previously stale).
  `.venv/Scripts/python.exe -m experiments.failure`: acceptance passed; real send
  rejected after MISMATCH; same relationship recovers with MATCH and a fresh TLS epoch.
  14 observations, 3 verifications; failure/restriction retained in ordered audit.
  `.venv/Scripts/python.exe -m pytest -q tests/test_guard.py`: 1 passed in 0.14s.
  Raw data: artifacts/failure.json. Recovery requires a new connection, not reopening a failed one.
- Phase 24: experiments/evaluation.py, tests/test_evaluation.py, docs/evaluation.md.
  `.venv/Scripts/python.exe -m pytest -q tests/test_evaluation.py`: 1 passed in 0.10s.
  `.venv/Scripts/python.exe -m experiments.evaluation`: six real-TLS/synthetic-context
  scenarios saved under artifacts/evaluation with raw traces and summary.json.
  Verification counts normal/gradual/sudden/new/established/failure: 1/13/2/2/2/3.
  Zero unnecessary requests on wholly normal observed sessions under these inputs.
  Four injected episodes triggered; gradual delay 18 observations, abrupt cases 0.
  Sudden dispatch latency 5.2486ms this run; automatic responses are not human OOB latency.
  Definitions include actual TLS-epoch denominators and exclude required bootstrap from false requests.
- Next phase: PHASE 25 — Threshold and Sensitivity Analysis.
- Git: phase 1 is 2074c5d. Writes require elevated execution and a command-local
  safe.directory for this exact workspace because sandbox/desktop owners differ.
- Git: phase 2 is 5e5f77b.
- Git: phase 3 is 9239af1.
- Git: phase 4 is 1204ba8.
- Latest Git commit: containing commit `phase-24-quantitative-evaluation`; resolve its
  hash with `git log -1 --format="%h %s"`. No self-referential hash is stored here.
