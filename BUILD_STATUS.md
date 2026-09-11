# Build checkpoint

- Milestone: 2 — phase 5 authorized and completed.
- Current phase: 10 — Verification Trigger Engine (complete).
- Completed phases: 1, 2, 3, 4, 5. No phase-6-or-later implementation.
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
- Next phase: PHASE 11 — Out-of-Band Verification Simulation.
- Git: phase 1 is 2074c5d. Writes require elevated execution and a command-local
  safe.directory for this exact workspace because sandbox/desktop owners differ.
- Git: phase 2 is 5e5f77b.
- Git: phase 3 is 9239af1.
- Git: phase 4 is 1204ba8.
- Latest Git commit: containing commit `phase-5-metadata-collection`; resolve its
  hash with `git log -1 --format="%h %s"`. No self-referential hash is stored here.
