# Local prototype security review

Scope: cryptographic provisioning/TLS, framed transport, metadata/trust, verification
gate/lifecycle, SQLite audit, dashboard and controlled experiment paths. This is a
source review plus executable checks, not a penetration test or certification.

## Reviewed controls and evidence

- TLS 1.3 only, client/server certificate validation and SPKI pins; hostname validation
  on Alice. P-256 identity keys are encrypted PKCS#8; ephemeral/traffic keys stay in TLS.
  Tests cover wrong passwords, missing/untrusted certificates, wrong pins and malformed input.
- Wire-proxy tests show application markers absent from encrypted captures and corrupted
  post-handshake records rejected. SSLKEYLOGFILE cannot enable key logging in explicit contexts.
- Bounded frames/read/write/handshake deadlines, concurrent receive rejection and serialized
  sends; shutdown owns incomplete handshakes. Secure CLI paths have no plaintext fallback.
- Raw metadata has an allowlist and finite numeric/IP checks. No payload enters scoring.
  Low score and negative delta are independent. Unknown verification results fail closed.
- Pending/failed verification gates sends and application delivery. Storage failure closes
  the connection. Successful verification requires a fresh authenticated TLS epoch.
- Audit numbers/enums are allowlisted. Review tightened key-event IDs to the exact public
  session epoch format, preventing arbitrary strings in that field.
- Dashboard binds loopback, validates Host and mutation Origin/custom header, uses textContent
  for dynamic fields and has no CORS allowance. Review removed unrestricted exception text
  from HTTP errors. Simulated observations are displayed separately from real measurements.

## Explicit limits

- Old Python 3.10.11 / OpenSSL 1.1.1t test environment: local experimental use only.
- TLS authenticates provisioned identities, not the safety of endpoint software. The adaptive
  guard is local cooperative policy; Bob's echo service itself authenticates TLS and does not
  run an independent distributed trust-consensus protocol. Low-level TLS demos omit the guard.
- The displayed OOB comparison is simulated, not a separate authenticated human channel.
  Local processes/users are trusted; dashboard has no multiuser login. Do not expose it remotely.
- Trusted setup distributes CA/pins. No revocation, production PKI, certificate renewal or
  file-permission hardening beyond the user's OS account. Certificates expire after 30 days.
- SQLite audit is not tamper-evident; IP addresses and timing are potentially identifying
  metadata. No encryption-at-rest database or retention policy. Protect .state and artifacts.
- Python cannot guarantee secret-memory zeroization. TLS keys are deliberately not exported.
- No Internet-facing rate limiting/resource-exhaustion defense. Handlers must cooperate with
  cancellation. Freshness/replay checks apply to bounded local metadata history, not an
  authenticated remote telemetry ingestion protocol.
- A high score cannot prove absence of interception. Synthetic results are not real attack
  detection accuracy. Continuous anomalies can cause repeated verification after MATCH.
