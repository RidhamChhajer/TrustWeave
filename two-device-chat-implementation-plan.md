# Two-Device Adaptive-Trust Chat: Implementation Plan

## 1. Locked demo outcome

Build a live, two-person encrypted chat demonstration on top of the existing adaptive-trust engine.

- Alice and Bob use two Windows laptops on the same private Wi-Fi network.
- Bob runs the TLS chat server and a clean local chat UI.
- Alice connects by entering Bob's LAN IPv4 address.
- Alice sees the chat UI plus the complete adaptive-trust dashboard.
- Bob sees a normal chat UI, a connection indicator, and safety-code prompts only.
- Both users must confirm the same independently calculated safety code before chat is enabled.
- Chat messages use the existing mutual TLS 1.3 transport.
- Controlled anomalies demonstrate trust changes, verification, restriction, and fresh TLS recovery.
- Chat history exists in memory for the current application run only.

This is a LAN demonstration, not an internet chat product. Accounts, cloud relays, NAT traversal, automatic discovery, mobile support, groups, attachments, and permanent message storage are out of scope.

## 2. Current foundation to preserve

The repository already provides:

- mutually authenticated TLS 1.3 with certificate validation, hostname validation, and peer pinning;
- encrypted framed byte transport;
- metadata collection for handshake time, RTT, timing, peer IP, and recent establishments;
- metadata normalization, weighted EMA trust, and sudden-drop detection;
- relationship/session history and metadata-only audit records in SQLite;
- `SessionGuard` verification gating, restriction, and fresh TLS reconnection;
- a local dashboard and deterministic experiments;
- standalone Alice/Bob CLIs and 68 passing tests at the planning baseline.

All existing demos, experiments, public transport behavior, and tests must remain operational.

## 3. Target architecture

```text
Alice browser (127.0.0.1:8766)
             |
       local WebSocket
             |
Alice Python chat runtime + SessionGuard + dashboard
             |
      mutual TLS 1.3 over Wi-Fi
             |
Bob Python chat runtime + TLS listener (0.0.0.0:8765)
             |
       local WebSocket
             |
Bob browser (127.0.0.1:8766)
```

Only Bob's TLS port is exposed to the LAN. Both browser services remain bound to loopback. Bob accepts one Alice chat session at a time for the demo.

Alice connects to Bob's numeric LAN address while passing `bob.local` as the authenticated TLS server name. This preserves hostname verification even if Bob's Wi-Fi address changes.

## 4. Application protocol

Add a versioned JSON protocol encoded as UTF-8 inside the existing encrypted frames. Every envelope contains:

- `version`: protocol version, initially `1`;
- `id`: unique message identifier;
- `type`: one of the allowed message types;
- `sender`: `alice` or `bob`;
- `timestamp`: UTC timestamp;
- type-specific fields from a strict allowlist.

Required message types:

| Type | Purpose |
|---|---|
| `chat` | User-visible text message |
| `chat_ack` | Delivery status for a chat message ID |
| `ping` / `pong` | Periodic RTT measurement |
| `verify_request` | Start dual safety-code comparison |
| `verify_response` | MATCH, MISMATCH, or CANCEL from one user |
| `verification_result` | Final combined verification result |
| `demo_mode` | Authenticated controlled-condition instruction |
| `session_notice` | Reconnect, restriction, or shutdown notification |

Protocol rules:

- Chat text is limited to 4 KiB after UTF-8 encoding.
- Empty and whitespace-only chat messages are rejected.
- Unsupported versions, unknown types/fields, duplicate IDs, invalid roles, invalid UTF-8, and malformed JSON fail safely.
- Maintain a bounded in-memory duplicate-ID cache.
- Protocol and transport errors must not include message contents in logs or UI diagnostics.
- System controls may pass while verification is pending; user chat envelopes may not.

## 5. Runtime state and gating

Use an explicit state machine:

```text
LOCKED -> CONNECTING -> VERIFYING -> ACTIVE
                         |             |
                         v             v
                    RESTRICTED    RECONNECTING
                         |             |
                         +----------> CLOSED
```

The chat coordinator sits above `FramedConnection` and distinguishes user messages from internal controls. It must gate chat in both directions:

- outbound chat is rejected while not `ACTIVE`;
- inbound chat is not delivered to the browser while not `ACTIVE`;
- queued chat is discarded if verification starts before delivery;
- verification, ping/pong, session, and shutdown controls remain available;
- restriction is fail-closed and cannot silently return to `ACTIVE`.

Preserve the existing `SessionGuard` interface for current demos through an adapter. Alice remains authoritative for trust assessment and lifecycle decisions. Bob mirrors the chat gate based on authenticated verification/session controls.

## 6. Identity provisioning and device transfer

Trusted provisioning creates three outputs:

1. an organizer directory containing the CA certificate and encrypted CA private key;
2. `alice-bundle`, containing only Alice's encrypted key, certificate, CA certificate, Bob pin, role, and non-secret defaults;
3. `bob-bundle`, containing only Bob's encrypted key, certificate, CA certificate, Alice pin, role, and non-secret defaults.

The CA private key and the other endpoint's private key must never appear in a device bundle. Provisioning refuses existing targets, weak passwords, missing files, wrong roles, invalid pins, and altered bundles. A read-only inspection command may display role and public fingerprints but never private material.

The recommended transfer method is USB from the trusted provisioning laptop. Passwords are communicated separately and are never stored by the application.

## 7. Local browser APIs

Each device runs a loopback-only FastAPI application and a same-origin WebSocket. The browser sends commands such as:

- `unlock`;
- `start_server` or `connect`;
- `send_chat`;
- `confirm_verification`;
- `set_demo_mode`;
- `disconnect`.

The Python runtime emits:

- complete sanitized state snapshots;
- incoming/outgoing chat events;
- verification prompts and results;
- connection/session changes;
- trust and signal changes on Alice only;
- sanitized recoverable errors.

WebSocket queues are bounded. Invalid commands are rejected without terminating the service. Identity passwords are used locally to load encrypted keys, retained only as long as needed in process memory, and never echoed to the browser after submission.

## 8. Bob experience

Bob's page contains:

- identity unlock form;
- server start/stop state;
- candidate private LAN IPv4 addresses and TLS port;
- connection/security badge;
- conversation area with Alice/Bob message bubbles and timestamps;
- send box and delivery status;
- safety-code modal with MATCH, MISMATCH, and CANCEL;
- small banner when an induced demo condition is active;
- sanitized connection and recovery messages.

Bob must not see trust scores, graphs, normalized signals, audit records, key-lifecycle details, or anomaly controls.

## 9. Alice experience

Alice's page contains:

- identity unlock form;
- Bob IPv4 entry and connect/disconnect controls;
- the same chat experience as Bob;
- live trust score and delta;
- trust graph with verification markers;
- raw connection metadata and normalized signals;
- session state, TLS version/cipher, relationship ID, and key-epoch ID;
- verification reason, safety code, and result;
- metadata-only event timeline;
- controlled anomaly buttons and prominent real/simulated labels.

Message bodies must exist only in the in-memory chat model and browser chat events. They must not be included in dashboard telemetry, trust snapshots, SQLite, audit events, application logs, or experiment artifacts.

## 10. Dual safety-code verification

Both devices independently calculate a grouped, human-readable safety code from the authenticated symmetric relationship ID. Neither device trusts a code received from its peer as its local source of truth.

Verification behavior:

1. Alice's trust policy triggers a verification request.
2. Both devices enter `VERIFYING` and disable chat.
3. Both display the locally calculated code and the request reason.
4. Alice and Bob independently answer MATCH, MISMATCH, or CANCEL.
5. Success requires MATCH/MATCH for the same request ID and relationship before timeout.
6. Any mismatch, cancellation, timeout, disconnect, stale response, or conflicting response restricts and closes the session.
7. Successful initial verification applies the existing verified trust floor and enables chat.
8. Successful anomaly reverification closes the old TLS connection and establishes a fresh pinned TLS session.
9. The relationship ID must remain unchanged after reconnect; otherwise the replacement is rejected.

The conversation remains visible in memory through a successful TLS reconnect. It is cleared when the local application exits.

## 11. Live measurements

Chat is independent in both directions; Bob is no longer an echo server in the chat application. A periodic authenticated ping/pong runs even when neither person is typing so Alice can measure RTT and variation continuously.

Feed genuine transport observations into the existing collector:

- TLS handshake latency;
- heartbeat RTT and variation;
- outbound/inbound frame timing;
- authenticated peer IP;
- recent authenticated session establishments.

Absence of user chat alone must not be treated as an anomaly.

## 12. Controlled anomaly demonstration

Alice receives four controls:

| Control | Mechanism | Required label |
|---|---|---|
| Induce latency | Bob intentionally delays pong/chat handling | `REAL INDUCED CONDITION` |
| Reconnect burst | Alice performs bounded real TLS reconnects | `REAL CONNECTION EVENT` |
| Simulate IP continuity change | Override only the trust input, without changing the physical IP | `SIMULATED METADATA` |
| Restore normal | Remove all active conditions | `NORMAL OBSERVATION` |

Only one anomaly mode may run at once. Reconnects are bounded and never retry forever. Bob displays only a small notice when latency is intentionally induced. Start/stop actions are audited without message content.

## 13. Failure and security requirements

Handle wrong IP, wrong identity password, wrong certificate/pin/hostname, occupied ports, Windows Firewall rejection, Wi-Fi loss, Bob shutdown, browser refresh/closure, malformed protocol input, verification timeout, and failed reconnect.

- Errors shown to users are actionable but sanitized.
- No traceback, filesystem path, password, key, certificate secret, or message content is exposed.
- Browser services enforce loopback binding, trusted hosts, and same-origin WebSocket requests.
- Queues, message sizes, duplicate caches, retries, and concurrent sessions are bounded.
- A second Alice connection is rejected while Bob is occupied.
- TLS validation and pinning are never disabled to make the demo work.

## 14. One-click Windows workflow

Provide:

- `setup-demo.cmd`: create the virtual environment and install pinned requirements;
- `provision-demo.cmd`: trusted creation of organizer, Alice, and Bob outputs;
- `start-bob.cmd`: start Bob's local service and open the browser;
- `start-alice.cmd`: start Alice's local service and open the browser.

The applications run preflight checks for Python/OpenSSL, bundle role/integrity, required ports, private IPv4 addresses, and reachability. They must not modify Windows Firewall automatically. Documentation instructs the presenter to allow Python on Private networks only.

## 15. Acceptance scenario

The feature is complete when this sequence succeeds twice from clean application starts on two Windows laptops:

1. Provision identities on a trusted laptop and transfer Bob's bundle by USB.
2. Connect both laptops to the same private Wi-Fi.
3. Start Bob and note the displayed IPv4 address.
4. Start Alice, enter Bob's address, and connect.
5. Compare the safety code and choose MATCH on both devices.
6. Exchange messages simultaneously in both directions.
7. Show stable live measurements on Alice.
8. Induce latency and show real RTT/message-delay changes.
9. Trigger verification, choose MATCH on both devices, and show a fresh TLS session/key epoch.
10. Continue the existing in-memory conversation.
11. Trigger verification again and choose MISMATCH.
12. Show that both sides close and further sending is impossible.
13. Inspect Alice's audit timeline and confirm that it contains no chat text.

Final automated acceptance retains all existing tests and adds protocol, state-machine, dual-verification, UI-origin, cross-runtime TLS, anomaly, reconnect, and leakage coverage.
