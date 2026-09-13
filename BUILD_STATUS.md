# Build checkpoint

## Current two-device chat checkpoint - 2026-09-13

- Branch: `codex/two-device-chat`.
- Two-device chat phases 0-12 and Phase 14 are complete with their recorded automated checks. Phase 13 physical acceptance remains deferred.
- The user explicitly authorized completing Phase 14 before the physical two-laptop tests. Those tests are now the final outstanding acceptance step.
- Next: Phase 13, physical two-laptop acceptance (two clean-start runs). Not performed or claimed by local TLS tests.
- Phase 14 handoff/presentation package is complete. The overall feature is not yet physically accepted.
- Latest full suite: **170 passed in 32.92s**. Existing final demo: all ten checks passed. `pip check`: clean.
- Environment: Windows, Python 3.10.11, OpenSSL 1.1.1t (7 Feb 2023); pinned requirements include websockets 15.0.1.
- Fresh virtual-environment setup launcher passed in `.state/phase12 setup smoke`, including dependency installation and `pip check`. Sandbox initially blocked network sockets; authorized retry succeeded.
- GitHub repository: https://github.com/RidhamChhajer/TrustWeave. Publication includes the source, tests, documentation and supplied plans; local credentials and generated data are excluded.
- Operation instructions: `docs/two-device-operation.md`. Trusted demo credentials have not been provisioned for the user.

## Historical local experimental prototype checkpoint

- Scope: all remaining phases authorized; proceed sequentially with focused checks.
- Current phase: all 31 phases complete for the local experimental prototype.
- Completed phases: 1–31. Phase 30's historical Windows block is resolved for this run.
- No unresolved implementation blockers. Not production-ready; security/measurement
  limitations remain documented. Reproduction used a separate clone/venv on the same PC.
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
- Phase 25: experiments/sensitivity.py, docs/evaluation.md.
  `.venv/Scripts/python.exe -m experiments.sensitivity`: 33 runs completed;
  raw traces, summary and table.csv in artifacts/sensitivity. Defaults unchanged.
  Gradual first-trigger delays ranged 15–22 observations; requests ranged 3–15.
  Every sudden scenario triggered at observation delay 0. High threshold only alters
  CONTINUE/MONITOR, so its unchanged verification count is expected and documented.
- Phase 26: trust/normalization.py, signal_collector.py, network/snapshot.py,
  verification/verification.py, session_guard.py, tests/test_robustness.py, test_metrics.py.
  Strict raw-field/finite-baseline validation; copied metadata views; stale/replayed
  explicit observations rejected; dynamic snapshots expire after 30 seconds;
  storage failure gates/closes transport; non-finite verification deadlines rejected.
  Initial regression: 6 failures exposed coarse Windows timestamp equality and clock-stub
  exhaustion. Corrected local-event ordering without weakening explicit replay rejection;
  revised fixture to model elapsed time rather than count internal clock calls.
  `.venv/Scripts/python.exe -m pytest -q --show-capture=no`: 68 passed in 5.46s.
- Phase 27: docs/security-review.md, storage/relationship_store.py, dashboard/app.py,
  tests/test_audit.py. Tightened public epoch IDs and sanitized HTTP error details.
  `.venv/Scripts/python.exe -m pytest -q tests/test_audit.py tests/test_dashboard.py tests/test_secure.py --show-capture=no`:
  15 passed in 1.80s. Source review records cooperative local guard, simulated OOB,
  legacy runtime, local trusted users, non-tamper-evident audit and no production DoS defenses.
- Phase 28: centralized metadata age/dashboard port in config/settings.py; configurable
  verified floor in TrustPolicy; guard type/doc cleanup; removed unused imports and stale
  handshake comment. Updated collector, snapshot, dashboard, crypto docs and demos.
  `.venv/Scripts/python.exe -m pytest -q tests/test_trust.py tests/test_robustness.py tests/test_dashboard.py --show-capture=no`:
  7 passed in 1.26s. `python -m pip check`: no broken requirements.
- Phase 29: refreshed README.md and docs/algorithms.md; added architecture.md,
  experiments.md and presentation.md. Includes run instructions, network/state diagrams,
  database schema, measured results, metric definitions, configuration and security boundaries.
  Removed stale foundation-only claims. Explicitly documents that .env is not auto-loaded.
  `git diff --check` passed; commands align with implemented module entry points.
- Phase 30 attempt: clean `git clone --no-local` at artifacts/repro, new `.venv`
  created there, `python -m pip install -r requirements.txt` installed all pins.
  `python -m pip check`: no broken requirements. No .env/credentials/database copied.
  Fresh clone commands `python -m pytest -q --show-capture=no`, `python -m client.demo`
  and `python -m experiments.sudden` failed importing cryptography's _rust.pyd:
  "An Application Control policy has blocked this file." This persists with approved
  execution outside the sandbox. No OS security policy was changed or bypassed.
  SHA256 of both existing/fresh _rust.pyd is identical:
  6C69EB01DEED404F8D16F4F23B176A1080745EA4B1C2DFD4C64E874E93782BF4.
  Existing environment regression still passes: `.venv/Scripts/python.exe -m pytest -q
  --show-capture=no`: 68 passed in 4.52s. Fresh-environment runtime validation is NOT passed.
  Blocker: Windows must permit the freshly installed native module through an authorized
  administrator-approved process, or reproduction must run on a permitted clean machine.
  Reproduction directory is retained (ignored by Git). Do not substitute the old environment
  and label that a clean reproduction. Phase 31 subsequently completed by user authorization.
- Phase 30 resolution (2026-09-12): user reported IMPORT OK after personally addressing
  the Windows block. Read-only diagnosis identified Smart App Control, not an enterprise
  administrator allowlist; the earlier generic allowlist suggestion was inapplicable.
  No OS settings were changed by the assistant. Clean clone/venv validation completed:
  `python -m pytest -q --show-capture=no`: 68 passed in 9.10s;
  `python -m pip check`: no broken requirements; `python -m client.demo`: DEMO_SUCCESS;
  `python -m experiments.sudden`: acceptance passed (69.6540, delta -29.8517).
  Fast-forwarded clean clone 4021bf6 -> 115f3da using fetch + merge --ff-only;
  `python -m client.final_demo`: 10 checks passed, 27 observations, 4 verifications,
  final trust 97.058775. No .env/credentials/database copied from the working environment.
  Clean dashboard at 127.0.0.1:8768 visually checked: live MATCH/SUCCESS/fresh session,
  active communication/Stop/Idle and isolated sudden-drop table all confirmed.
  This is clean-environment validation on the same OS, not independent-machine certification.
- Next action: none required for the requested phases; presentation/deployment are separate work.
- Follow-up: user authorized system diagnosis; computer-use instructions read and runtime
  initialized. Skill prohibits security UI/settings automation. Read-only CodeIntegrity
  events 3077/3033 confirm policy {0283ac0f-fff1-49ae-ada1-8a933130cad6} blocks fresh
  _rust.pyd; approved import retry still failed. No security settings changed.
- Phase 31: client/final_demo.py, README.md, docs/reproducibility.md and this checkpoint.
  `.venv/Scripts/python.exe -m client.final_demo`: FINAL_DEMO_SUCCESS; 10 acceptance
  checks passed; 27 observations, 4 verifications, final trust 97.058775.
  Demonstrates conservative bootstrap/MATCH/learning/sudden anomaly/MISMATCH with actual
  send rejection/fresh recovery/repeat anomaly MATCH/new TLS epoch/restored messaging.
  Raw metadata, decisions and audit saved in artifacts/final-demo.json; no payloads/secrets.
  `.venv/Scripts/python.exe -m pytest -q --show-capture=no`: 68 passed in 4.36s.
  Browser check on 127.0.0.1:8767: rendered layout, isolated sudden experiment result,
  live pending comparison, MATCH -> fresh session -> rising graph -> Stop/Idle verified.
  Local dashboard process started for handoff on port 8767; live messaging stopped.
- Git: phase 1 is 2074c5d. Writes require elevated execution and a command-local
  safe.directory for this exact workspace because sandbox/desktop owners differ.
- Git: phase 2 is 5e5f77b.
- Git: phase 3 is 9239af1.
- Git: phase 4 is 1204ba8.
- Latest Git commit: containing commit `phase-30-reproducibility`; resolve its
  hash with `git log -1 --format="%h %s"`. No self-referential hash is stored here.

## Two-device chat — Phase 0 (2026-09-12)
Branch: codex/two-device-chat. Tracked baseline clean; supplied untracked plan documents preserved. Baseline: 68 tests passed, final_demo passed all ten checks, pip check clean. Added inert chat package, bounded configuration, and shared metadata-only dashboard presentation. Phase gate: 77 tests passed; final_demo smoke passed. Physical two-laptop acceptance remains pending access to both devices.


## Two-device chat — Phase 1
Strict versioned envelopes, UTC timestamps, UTF-8/4 KiB bounds, field allowlists, duplicate JSON-key rejection, bounded replay cache, and sanitized errors implemented. All nine envelope types round-tripped over real mutual TLS. Full suite: 104 passed. Final demo smoke passed. Fixed Windows pytest environment overflow with explicit short parameter IDs; boundary inputs retained.


## Two-device chat — Phase 2
Implemented explicit terminal restriction, bounded chat queue, generation-based queue invalidation, inbound delivery gating, authenticated control path, and SessionGuard adapter. FramedConnection retains existing behavior with an optional write-boundary predicate. Real TLS tests prove controls pass while verifying and queued/racing chat does not. Full suite: 106 passed; final_demo smoke passed.


## Two-device chat — Phase 3
Provisioned organizer plus role-specific portable bundles, signed manifest validation, public inspection, overwrite/weak-password refusal. Tested isolated copies over mutual TLS to numeric IP with bob.local hostname, role swaps, missing/altered files, pins and signatures. Full suite: 115 passed; final_demo smoke passed. Trust anchor is the trusted USB provisioning transfer; replacing an entire bundle including its CA cannot be detected without an external anchor.


## Two-device chat — Phase 4
Loopback-only HTTP/WebSocket bridge with host and exact-origin checks, strict commands, bounded client/event queues, sanitized errors and local-only password submission. Added pinned websockets 15.0.1 backend. Full suite: 122 passed; final_demo and pip check passed. ASGI smoke verifies legitimate local browser commands and rejects foreign origins, hosts, and LAN clients without password leakage.


## Two-device chat — Phase 5
Bob endpoint, encrypted-key unlock, private IPv4 candidates, loopback browser chat layout, TLS listener and one-peer admission implemented. Conversation is bounded memory only; refresh reconstructs state. Full suite: 124 passed; final_demo smoke passed. Correct/wrong password, occupied port, second peer, refresh and shutdown covered. Sending stays locked pending Phase 7 dual verification and Phase 8 chat loops.


## Two-device chat — Phase 6
Alice private-IPv4 validation, pinned bob.local TLS connection, SessionGuard adapter integration, trust graph/metadata/session/epoch/timeline UI and separate metadata-only observatory added. Full suite: 134 passed; final_demo smoke passed. Numeric-loopback real TLS integration, public/invalid address rejection, Alice-only observability and SQLite/telemetry payload-leak checks passed. Phase 7 dual verification is next; physical acceptance remains pending.


## Two-device chat — Phase 7
Independent relationship-derived safety codes, correlated dual human decisions, timeout and stale/conflicting-response failure implemented. Existing SessionGuard defaults preserved; chat records real human comparison (simulated=false) and applies the verified floor without unnecessary initial rotation. Full suite: 151 passed; final_demo smoke passed. Focused tests cover all nine decision combinations plus real two-runtime initial success, one-approval gating, mismatch, timeout and browser closure.


## Two-device chat — Phase 8
Independent bidirectional chat, ordered bounded in-memory conversation, delivery acknowledgments, duplicate protection and authenticated heartbeat RTT/variation added. Trust timing uses genuine heartbeat cadence rather than human typing gaps. Full suite: 152 passed; final_demo smoke passed. Simultaneous/rapid/Unicode/4 KiB messages, idle metrics, refresh and log/SQLite/telemetry leakage checks passed. Fixed a shutdown race with a durable heartbeat stop flag and bounded shutdown assertions.


## Two-device chat — Phase 9
Dual approval now authorizes a bounded fresh mutual-TLS recovery with request/relationship correlation on the replacement channel. Bob reserves one recovery window; chat stays gated until readiness exchange. Conversation persists in memory, relationship remains fixed, and session/key epoch changes. Scheduled rotation also requests dual comparison for chat while preserving legacy defaults. Full suite: 157 passed; final_demo smoke passed. Success, mismatch, unavailable replacement, changed relationship and scheduled rotation covered.


## Two-device chat — Phase 10
Added mutually exclusive labeled latency, bounded real reconnect burst, continuity-only metadata simulation and restore-normal controls. Bob delays chat/pong work without blocking verification controls; Alice measures actual RTT and heartbeat completion cadence. Demo start/stop audit fields remain allowlisted and payload-free. Full suite: 159 passed; final_demo smoke passed. Real induced latency triggers sudden-drop dual verification; MATCH recovery works; burst produces three new TLS epochs and establishment count 4; continuity override leaves physical IP unchanged.


## Two-device chat — Phase 11
Security/failure regression complete. Added pre-handshake concurrency limits, verification-request replay cache, immediate persisted restriction on Alice transport/protocol failures, and bounded browser reconnects. Full suite: 166 passed; final_demo and pip check passed. Real WebSocket smoke, foreign-origin rejection, malformed/invalid-UTF8/role/replay/stale traffic, metadata leakage and pre-handshake flooding covered alongside existing CA/pin/hostname/TLS-corruption/framing regressions.

## Two-device chat - Phase 12

Implemented `setup-demo.cmd`, `provision-demo.cmd`, `start-bob.cmd`, and `start-alice.cmd`; loopback-only CLI service with automatic local-page opening; public preflight for Python/OpenSSL, role/integrity, private IPv4 candidates, and port availability. Alice performs bounded authenticated connection/reachability checks when connecting. Added Windows setup, trusted USB transfer, Private-network-only firewall guidance, condition labels, and recovery/troubleshooting instructions. No firewall settings are modified.

Validation:

- Full suite: **168 passed in 21.24s**; final_demo smoke passed all ten checks; dependency check clean.
- Focused launcher tests: valid preflight from a path containing spaces, wrong/missing bundle, occupied UI port, and unavailable Bob pass with sanitized diagnostics.
- Both Windows start launchers were exercised with missing default bundles and returned the expected sanitized failure without opening a service.
- Actual setup launcher created a separate fresh virtual environment in a path containing spaces, installed all pinned dependencies, and passed `pip check`. Network access required an authorized sandbox retry.
- Fresh-environment launcher/preflight and real loopback WebSocket smoke: 3 passed in 6.00s. Final `git diff --check` passed.
- Existing runtime tests cover bounded shutdown, correct/wrong identity password, occupied TLS port, real TLS messaging/recovery, and same-origin WebSocket operation.
- User-facing browser rendering and automatic browser opening were not manually exercised; real HTTP/WebSocket service behavior was tested. Physical Wi-Fi/firewall and two-laptop runs belong to Phase 13 and remain pending.

Historical stop after Phase 12 was superseded by the user's continuation request. Phase 13 and Phase 14 are not complete.

## Two-device chat - Phase 13 readiness; physical gate pending

Continuation authorized by the user. Added a complete local acceptance-sequence
regression, run twice with fresh endpoint runtimes and isolated identities/storage.
Both runs use real mutual TLS and real induced delay. Human decisions are automated
in these tests; heartbeat/delay timings are shortened for testing. These runs do
not claim physical Wi-Fi, USB transfer, browser rendering, or human comparison.

- Two complete local sequences passed: initial dual approval, simultaneous chat,
  stable measurements, induced latency/sudden-drop verification, MATCH/MATCH fresh
  TLS recovery, unchanged relationship, preserved conversation, resumed messages,
  a second induced verification, MISMATCH, both gates closed, and payload-leak checks.
- Focused readiness tests: 2 passed in 6.48s.
- Full suite: 170 passed in 34.97s. Existing final demo: all ten checks passed.
  Dependency check: no broken requirements. Whitespace diff check passed.
- Physical results sheet: `docs/two-device-acceptance.md`, both runs explicitly Pending.
- Required external step: user supplies the second Windows laptop on private Wi-Fi,
  performs trusted USB bundle transfer and both human comparisons, then records the
  two complete physical runs. No second laptop is accessible through current tools.
- Phase 13 is NOT complete. The initial hold on Phase 14 was subsequently superseded
  by the user's explicit instruction to do physical two-laptop testing at the end.

## Two-device chat - Phase 14 complete; physical acceptance deferred

The user explicitly changed the sequence: complete the remaining work now and do
physical two-laptop connection/acceptance tests at the end. Phase 13 has not been
marked passed or replaced with local tests.

Completed handoff:

- README now starts with the two-device workflow and links setup, architecture,
  presentation, and the pending acceptance record; legacy demos remain documented.
- `docs/two-device-architecture.md`: network diagram, component ownership, protocol/
  gating and dual-verification flow, fresh TLS recovery, data/measurement boundaries,
  configured bounds, security limitations, and remaining physical validation.
- `docs/two-device-presentation.md`: presenter script, exact condition labels,
  stabilization guidance, real-versus-simulated table, and recovery/failure guide.
- Existing architecture, security review and presentation pages now distinguish
  original echo/simulated demonstrations from the new two-device chat.
- Setup, trusted transfer, Private-network firewall and troubleshooting instructions
  remain in `docs/two-device-operation.md`; the physical results sheet reflects the
  authorized deferral and leaves both physical runs Pending.

Final verification:

- `.venv/Scripts/python.exe -m pytest -q`: **170 passed in 32.92s**.
- `.venv/Scripts/python.exe -m client.final_demo`: all ten checks passed.
- `.venv/Scripts/python.exe -m pip check`: no broken requirements found.
- Documentation link validation: 19 local links resolve.
- `git diff --check`: passed.
- Environment: Windows; Python 3.10.11; OpenSSL 1.1.1t (7 Feb 2023); exact package
  pins retained in `requirements.txt`, including websockets 15.0.1.

Remaining: Phase 13's two physical clean-start acceptance runs, including trusted
USB transfer, real private Wi-Fi/firewall behavior, actual launcher/browser use and
human code comparison on both laptops. Local tests cannot certify those observations.
No additional feature phases remain. Implementation was prepared on
`codex/two-device-chat`; no real user credential bundles were created for presentation.
