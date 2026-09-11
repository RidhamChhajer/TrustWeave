# Build checkpoint

- Milestone: 1 — phases 1–4 only.
- Current phase: 3 — Cryptographic Identity and Key Establishment (complete).
- Completed phases: 1, 2, 3.
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
- Limitations: phase-2 CLI remains temporarily plaintext until phase-4 integration.
  TLS foundation is tested directly with OpenSSL MemoryBIO; traffic keys are not exported.
  Development CA/pin provisioning is trusted local setup, not an OOB workflow.
  Local Python/OpenSSL is old.
- Blockers: none.
- Next phase: PHASE 4 — Encrypted Communication.
- Git: phase 1 is 2074c5d. Writes require elevated execution and a command-local
  safe.directory for this exact workspace because sandbox/desktop owners differ.
- Git: phase 2 is 5e5f77b.
- Latest Git commit: containing commit `phase-3-cryptographic-foundation`; resolve using `git log -1`.
