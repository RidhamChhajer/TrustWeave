# Clean-environment reproduction checkpoint

2026-09-12: cloned committed Phase 29 (`4021bf6`) locally into `artifacts/repro`
without copying untracked .env, identities, databases or artifacts. Created a new virtual
environment and installed every pinned dependency. `pip check` passed.

The fresh interpreter cannot import cryptography's `_rust.pyd`: Windows reports
“An Application Control policy has blocked this file.” Approved execution outside the
sandbox did not resolve it. The existing and fresh DLL SHA-256 hashes are identical:
`6C69EB01DEED404F8D16F4F23B176A1080745EA4B1C2DFD4C64E874E93782BF4`.
The existing environment still passes 68 tests. This does **not** establish clean-machine
reproducibility; Phase 30 remains incomplete and Phase 31 has not started.

Required external action: an authorized administrator approves the module/environment
through the organization's normal policy, or use another permitted clean machine.
Do not disable or bypass Application Control. Once permitted, from the clean clone run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --show-capture=no
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m client.demo
.\.venv\Scripts\python.exe -m experiments.sudden
.\.venv\Scripts\python.exe -m dashboard.app
```

Confirm dashboard access and the isolated sudden-drop control in a browser; existing
ASGI endpoint tests do not substitute for visual rendering validation. Then complete
Phase 31's combined new relationship/MATCH/learning/anomaly/MISMATCH/recovery demo.
