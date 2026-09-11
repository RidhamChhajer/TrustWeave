# Adaptive Trust-Triggered Cryptographic Verification

Experimental Computer Network Technology project. The three original specifications
define the later adaptive verification layer. This milestone implements phases 1–4
foundation is complete. Phase 5 now adds raw metadata collection above that transport.

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

## Run the completed milestone

For a noninteractive demonstration with temporary, freshly generated encrypted
credentials and real loopback TCP sockets:

```powershell
.\.venv\Scripts\python.exe -m client.demo
```

The output shows `TLSv1.3`, a negotiated authenticated cipher, the same session ID
at Alice and Bob, frame byte counts, `DEMO_SUCCESS`, and connection closure.
Three random binary messages make a round trip; messages/passwords/keys are never
printed. The temporary encrypted credential directory is removed after the demo.

For separate terminal processes, create persistent development identities first:

```powershell
.\.venv\Scripts\python.exe -m client.provision
```

Enter and confirm a separate password of at least 12 UTF-8 bytes for the CA, Alice,
and Bob. Input is hidden; an insecure terminal fallback is refused. Provisioning
refuses an existing output directory. Passwords are not saved and cannot be recovered.

In terminal 1:

```powershell
.\.venv\Scripts\python.exe -m client.bob
```

In terminal 2:

```powershell
.\.venv\Scripts\python.exe -m client.alice
```

Enter the corresponding identity password in each terminal. Alice verifies three
encrypted round trips and exits; Bob keeps listening until Ctrl+C. These CLI endpoints
demonstrate message transport, not an interactive chat UI. Use `--help` for credential,
host, port and server-name options. There is no plaintext fallback in either endpoint.
The temporary phase-2 plaintext connector was removed; raw framing tests remain test-only.

## Application interface

`network.secure.connect(settings, credentials, password_callback, server_hostname=...)`
returns an authenticated connection with `send(bytes)`, `receive() -> bytes`, `close()`,
and immutable `info`. `SecureServer.start(settings, credentials, password_callback, handler)`
invokes the asynchronous handler only after peer certificate and fingerprint validation.
Both objects support asynchronous context managers. Bob's handler implements an echo.

`info` exposes session ID, connection state, public peer fingerprint, TLS version and
cipher. Alice's elapsed time includes connection, TLS and encrypted session-ID receipt;
Bob's elapsed time is `None` because asyncio supplies the accepted stream after TLS.
`key_id` is a non-secret connection-epoch label for TLS traffic keys, not an actual key,
an exported TLS identifier, or a cryptographic fingerprint. A reconnect gets a fresh ID.

Frames use a 4-byte unsigned big-endian length and up to 1 MiB of bytes. The length and
payload are encrypted together inside TLS. Empty messages are supported. Invalid/truncated
frames, operation timeouts, and TLS failures close the connection; concurrent receives
are rejected, sends are serialized, and cleanup has a bounded per-writer deadline.
Bob owns accepted sockets before TLS starts, so shutdown cancels incomplete handshakes
as well as established sessions. Application handlers must cooperate with cancellation.

The metadata object and event logger never receive message bodies. The framing layer
necessarily handles bytes at the endpoints; future trust modules must consume metadata
only. No trust scoring or verification trigger is implemented yet.

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

## Verification and limitations

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

Tests cover actual TCP/TLS exchanges, a test-only relay capturing opaque TLS records,
post-handshake ciphertext corruption, certificate/pin/hostname failures, missing client
certificates, TLS-version rejection, malformed framing, timeouts, reconnects, concurrency,
metadata separation and log leakage. No TLS traffic key export is enabled, including
when `SSLKEYLOGFILE` is set. Tests and the demo generate new credentials; no cryptographic
secret is hard-coded. Test byte markers are message fixtures, not cryptographic keys.

This is an experimental local prototype. Its trusted bootstrap creates both endpoint
identities on one machine. For separate machines, transfer only the appropriate endpoint
directory securely; never distribute the CA private key or the other endpoint's key.
Protect public trust/pin files and encrypted key files with OS access controls. Default
Bob certificates cover localhost, 127.0.0.1 and bob.local; other names need properly
provisioned certificates. Do not disable hostname validation to bypass this requirement.
Identity certificates expire after 30 days; this milestone does not renew them, revoke
them, rotate keys adaptively, or implement human out-of-band verification. Python cannot
guarantee wiping all secret bytes from memory. Endpoint/OS compromise is outside scope.

## Phase 5 — Raw metadata

Each secure connection exposes `connection.metrics`. Read
`connection.metrics.collector.measurements` for its bounded in-memory signal stream.
Pass a shared `ContextSignalCollector` to `connect(..., collector=collector)` to count
reconnects in the same process; Bob shares one collector across its connections.

Records contain UTC timestamp, session ID, a symmetric SHA-256 relationship ID derived
from both public identity fingerprints, signal name, raw value, source and
`normalized_value=None`. There is no normalization, scoring or database yet.

- Handshake latency: Alice measures TCP + TLS connection time (before reading the
  session ID); Bob measures its accepted-socket TLS handshake. Sources distinguish them.
- RTT: Alice's sequential echo exchanges report measured application round trips,
  including processing/scheduling overhead. Variation is population standard deviation
  over the last 32 samples. Generic connections report RTT unavailable until an
  application records a matched round trip; no RTT is inferred from unrelated messages.
- Continuity: authenticated relationship ID and observed peer IP. IP is not proof of
  device identity or network-path continuity; port changes are deliberately excluded.
- Timing: intervals between completed frames, separately for each direction. The
  first interval is unavailable, not zero.
- Establishments: successful authenticated sessions for that relationship in the last
  60 seconds, including the initial session. This is not TLS 1.3 renegotiation or a
  count of failed handshakes. Counts are local to the collector and reset on restart.

Metadata hooks receive timestamps/descriptors only, never payloads. The collector
retains the latest 1,024 records by default and rejects unexpected fields. Missing
measurements remain `None`; metadata anomalies do not establish that an attack occurred.

Next: PHASE 6 — Signal Normalization.

Implementation references: [Python TLS](https://docs.python.org/3.10/library/ssl.html),
[accepted-socket TLS](https://docs.python.org/3.10/library/asyncio-eventloop.html#asyncio.loop.connect_accepted_socket),
and [cryptography X.509](https://cryptography.io/en/stable/x509/tutorial/).
