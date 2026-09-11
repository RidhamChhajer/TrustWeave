# Build checkpoint

- Milestone: 1 — phases 1–4 only.
- Current phase: 2 — Basic Alice ↔ Bob Networking (complete).
- Completed phases: 1, 2.
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
- Limitations: phase-2 networking is temporarily plaintext; TLS follows in phases 3–4.
  Local Python/OpenSSL is old.
- Blockers: none.
- Next phase: PHASE 3 — Cryptographic Identity and Key Establishment.
- Git: phase 1 is 2074c5d. Writes require elevated execution and a command-local
  safe.directory for this exact workspace because sandbox/desktop owners differ.
- Latest Git commit: containing commit `phase-2-basic-networking`; resolve using `git log -1`.
