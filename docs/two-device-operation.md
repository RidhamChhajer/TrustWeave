# Two-device Windows operation

The chat implementation has automated local TLS coverage. Two physical Windows
laptops and the two clean-start acceptance runs must still be checked by the presenter.

## Setup and trusted transfer

1. Install Python 3.14 with OpenSSL 3.5 or newer on each laptop. The pinned
   dependencies were tested with Python 3.14.7 / OpenSSL 3.5.7 on Windows. Double-click
   `setup-demo.cmd` in the project folder on each device. Keep the project code
   together; do not copy a virtual environment between laptops.
2. On the trusted provisioning laptop only, run `provision-demo.cmd`. Choose three
   different passwords of at least 16 bytes and eight distinct characters. A long
   random password or passphrase is preferable. Never put passwords in commands.
3. Provisioning creates `demo-identities/organizer`, `alice-bundle`, and `bob-bundle`.
   Keep the organizer on the trusted laptop. Copy only Bob's bundle by trusted USB
   into `demo-identities/bob-bundle` on Bob's laptop. Alice receives only Alice's
   bundle. Communicate each password separately. Do not transfer another endpoint's
   key, the organizer, or the entire provisioning output directory.
4. Signed manifests detect partial bundle alteration. The trusted USB transfer is
   the trust anchor: replacing an entire bundle including its CA requires external
   fingerprint comparison to detect. Inspection prints only role and public pins:
   `.venv314\Scripts\python.exe -m chat.bundles inspect demo-identities\bob-bundle`.
5. Both laptops join the same **private Wi-Fi**. If Windows Firewall prompts, allow
   Python on **Private networks only**. These scripts never modify the firewall.
   Do not enable Public-network access. Guest Wi-Fi/client isolation may prevent
   peer connectivity; use a private network that permits laptop-to-laptop traffic.

## Start and compare

- Bob double-clicks `start-bob.cmd`, unlocks his identity in the local page, and
  clicks **Start server**. He gives Alice the Wi-Fi adapter's private IPv4 from the
  displayed candidates. Only Bob's TLS listener uses `0.0.0.0:8765`.
- Alice double-clicks `start-alice.cmd`, unlocks her identity, enters that IPv4, and
  clicks **Connect to Bob**. The numeric address routes the connection; `bob.local`
  remains the authenticated TLS hostname. No DNS/hosts-file edit is needed.
- Both compare the complete displayed safety code directly and choose MATCH.
  One approval is insufficient. MISMATCH, CANCEL, stale responses, timeout, or
  browser closure during comparison closes the session.
- Exchange messages. Alice alone sees trust, metadata, key epoch and audit events.
  Bob has a normal chat view. Conversation is held in bounded memory (500 recent
  messages by default); it is not written to SQLite or browser storage. It survives
  refresh and successful TLS recovery. Exiting the local service clears it.
- A bundle outside the default folder can be supplied as the launcher's first
  argument, with the path in quotes. Paths containing spaces are supported.

## Controlled conditions and recovery

| Control | What really changes | Display label |
|---|---|---|
| Induce latency | Bob delays chat/pong work by 3.2 seconds | REAL INDUCED CONDITION |
| Reconnect burst | At most three fresh pinned TLS connections | REAL CONNECTION EVENT |
| Simulate IP continuity change | Only Alice's trust input becomes 192.0.2.1 | SIMULATED METADATA |
| Restore normal | Removes the active induced/simulated condition | NORMAL OBSERVATION |

Only one condition is active. Let normal heartbeat observations stabilize before
inducing latency; the trigger uses the actual score delta, so it does not promise
an immediate trigger at every starting score. IP simulation alone may lower trust
without crossing a verification threshold. Raw frame events remain measured, while
trust timing uses heartbeat completion cadence so human typing silence is harmless.

On a sharp-drop prompt, select Restore normal on Alice if accessible before the
prompt, or complete comparison and restore when the dialog closes. MATCH/MATCH
closes the old TLS session and establishes a fresh one; the key-epoch ID changes,
the relationship ID stays fixed, and existing chat remains visible. For a clean
recovery while the modal is open, use its **Restore normal condition** button.
If recovery fails or either person rejects the code, both gates close. Bob stops
and restarts the listener; Alice explicitly reconnects and both compare again.

## Troubleshooting and preflight

- Run `.venv314\Scripts\python.exe -m chat.app bob --bundle demo-identities\bob-bundle --check`
  (substitute Alice's role/path for Alice) for public preflight output.
- **Wrong password/bundle:** retry locally with the correct password; inspect or
  replace an altered/expired bundle through trusted provisioning. Never disable
  certificate, hostname or pin checks.
- **Port occupied:** close another chat instance or the existing dashboard. Both
  use loopback UI port 8766 by default. For same-machine testing only, use different
  `--ui-port` values. Bob's TLS port and Alice's `--tls-port` must agree.
- **Bob unavailable:** check his Start server state, private IPv4, shared Wi-Fi,
  Private-network firewall permission, and guest-network isolation. Connection
  attempts time out; retries are explicit or bounded during verified recovery.
- **No private IPv4:** join private Wi-Fi and check the adapter address. Candidate
  addresses may include VPN/virtual adapters; select the shared Wi-Fi adapter.
- **Refresh/closure:** refresh reconstructs in-memory chat. Closing the last browser
  during verification restricts the session; closing the browser does not exit the
  local Python service. Use Disconnect/stop and then Ctrl+C in the launcher window
  to stop the service and clear sensitive runtime state.
- **Local UI unavailable:** auto-reconnect is bounded. Restart the launcher if
  needed, then refresh. Both browser services must stay on `127.0.0.1`.

This is a LAN demonstration, not an internet messenger. No cloud relay, account,
discovery, attachment, persistent chat history, or protection from a compromised
endpoint is provided. Python cannot guarantee secure erasure of immutable secrets
or OS paging/crash dumps; keys remain encrypted on disk and passwords are never
persisted by the application.
