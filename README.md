# Adaptive Trust-Triggered Cryptographic Verification

Experimental Computer Network Technology project. The three original specifications
define the later adaptive verification layer. This milestone implements phases 1–4
only: a tested, authenticated Alice–Bob communication foundation.

## Development setup (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m main
.\.venv\Scripts\python.exe -m pytest
```

Use Python 3.10 or newer with TLS 1.3 support. The currently available local runtime
is Python 3.10.11 with OpenSSL 1.1.1t; it is old and is used only for local experimental
validation. Use a maintained, patched Python/OpenSSL runtime before network deployment.

Configuration comes from shell environment variables documented in `.env.example`.
No `.env` file is loaded implicitly. Never put secrets in configuration or source.
FastAPI and Uvicorn are installed as specified, but no API/dashboard is implemented.

See `BUILD_STATUS.md` for phase checkpoints and exact test evidence.

## Phase-2 networking checkpoint

Run Bob with `python -m client.bob` and then Alice with `python -m client.alice`
using the virtual-environment interpreter. This checkpoint uses temporary plaintext
for socket validation only; the completed milestone will require mutual TLS.

## Cryptographic foundation

`crypto.identity` generates a local development CA and separate P-256 identities.
Private keys use encrypted PKCS#8 (cryptography BestAvailableEncryption). Both peers
receive CA trust and the other party's SHA-256 public-key fingerprint. Trust files
must be provisioned through a trusted local channel and protected from replacement.

`crypto.key_exchange` configures mutual TLS 1.3 with certificate validation, hostname
checking on Alice, peer identity pin checks, no key logging, and no session tickets.
OpenSSL derives independent directional traffic keys internally; application code
does not export them. Bidirectional authenticated decryption tests verify compatible
keys without printing them. Identity keys, public fingerprints, and TLS traffic keys
are separate concepts. No custom key exchange, cipher, or second encryption layer is used.

On this machine, Windows Application Control blocks cryptography's native DLL in the
Codex sandbox. Tests run successfully using approved execution outside that sandbox.
