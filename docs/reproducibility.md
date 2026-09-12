# Clean-environment reproduction — passed

Phase 30 completed on 2026-09-12 using a separate local Git clone and freshly installed
virtual environment under artifacts/repro. No .env, credentials or database was copied
from the original working environment. This validates a clean environment on the same
Windows PC, not portability to an independently configured machine.

## Evidence

- Cloned Phase 29 (4021bf6); created a fresh venv; installed all requirements.txt pins.
- Fresh-environment full suite: 68 passed in 9.10s.
- pip check: no broken requirements.
- client.demo: real mutual TLS 1.3, three encrypted echo round trips, DEMO_SUCCESS.
- experiments.sudden: score 69.6540 and delta -29.8517; immediate trigger above 50.
- Fast-forwarded the clean clone to completed Phase 31 (115f3da) without copying working files.
- client.final_demo: all 10 acceptance checks passed; 27 observations, 4 verifications,
  final trust 97.058775. Includes MISMATCH send rejection and fresh verified recovery.
- Clean-environment dashboard served on 127.0.0.1:8768: rendered controls, live pending
  comparison, MATCH/SUCCESS, new session ID, active messaging and Stop/Idle verified.
  Isolated sudden experiment visibly showed 99.51 -> 69.65, delta -29.85 and re-establishment.

## Historical Windows block and correction

The fresh cryptography _rust.pyd initially failed with an Application Control error,
even under approved execution. CodeIntegrity events 3077/3033 named policy
{0283ac0f-fff1-49ae-ada1-8a933130cad6}. Further event 3099 inspection identified
VerifiedAndReputableDesktop: Smart App Control, not an enterprise-specific allowlist.
The initial generic administrator-allowlist advice was therefore inapplicable.
Existing/fresh DLL SHA-256 hashes matched:
6C69EB01DEED404F8D16F4F23B176A1080745EA4B1C2DFD4C64E874E93782BF4.

The user personally addressed the block and reported IMPORT OK; the subsequent checks
above passed. The assistant did not modify security settings. This success does not
establish compatibility with every Smart App Control configuration. Prefer supported,
trusted dependencies and preserve OS protection; this prototype is not production-ready.

## Repeat from a clean checkout

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q --show-capture=no
.\.venv\Scripts\python.exe -m client.demo
.\.venv\Scripts\python.exe -m client.final_demo
.\.venv\Scripts\python.exe -m experiments.sudden
.\.venv\Scripts\python.exe -m dashboard.app
```

The dashboard defaults to port 8766. Metadata/results remain under ignored .state and
artifacts directories. No passwords or traffic keys are printed or committed.
