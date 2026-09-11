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
