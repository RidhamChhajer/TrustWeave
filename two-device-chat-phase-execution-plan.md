# Two-Device Adaptive-Trust Chat: Phase Execution Plan

## Execution contract

- Create `codex/two-device-chat` only when implementation begins.
- Start from a clean worktree and record the existing 68-test baseline.
- Complete phases in order; a phase is not complete until focused tests, the full suite, a smoke test, and its `BUILD_STATUS.md` checkpoint pass.
- Preserve all current CLIs, demos, experiments, dashboard behavior, and security invariants.
- Never log or persist chat bodies, passwords, private keys, or TLS secrets.
- Alice owns trust/dashboard behavior; Bob remains a normal chat interface with verification prompts.

## Phase 0 - Baseline and skeleton

**Implement**

- Run the full existing suite, final demo, and dependency check.
- Create the `chat` package without import-time side effects.
- Add validated configuration for TLS port `8765`, loopback UI port `8766`, 4 KiB chat limit, heartbeat cadence, queue bounds, reconnect bounds, and verification timeout.
- Extract reusable dashboard presentation/state helpers without changing the existing dashboard.

**Verify**

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m client.final_demo
.\.venv\Scripts\python.exe -m pip check
```

**Exit gate:** baseline remains green and importing `chat` starts no service or state.

## Phase 1 - Versioned protocol

**Implement**

- Strict JSON envelope models for `chat`, `chat_ack`, `ping`, `pong`, `verify_request`, `verify_response`, `verification_result`, `demo_mode`, and `session_notice`.
- UTF-8 encoding/decoding, 4 KiB chat limit, UTC timestamps, unique IDs, strict fields, and a bounded duplicate-ID cache.
- Sanitized protocol exceptions that never repeat untrusted payloads.

**Verify**

- Round-trip every envelope type over real TLS test peers.
- Test Unicode, boundary sizes, empty text, invalid UTF-8/JSON, unknown versions/types/fields, and duplicate IDs.
- Search captured logs/errors for test payload markers.

**Exit gate:** valid typed traffic works; invalid protocol traffic fails closed without leakage.

## Phase 2 - State machine and chat gate

**Implement**

- States: `LOCKED`, `CONNECTING`, `VERIFYING`, `ACTIVE`, `RECONNECTING`, `RESTRICTED`, `CLOSED`.
- A coordinator above `FramedConnection` that permits trusted controls while blocking user chat outside `ACTIVE`.
- Bidirectional gate, bounded queues, race-safe state transitions, and dropping of queued chat when verification starts.
- Compatibility adapter so existing `SessionGuard` callers retain their current behavior.

**Verify**

- Chat cannot pass before verification or after restriction.
- Ping and verification controls work while chat is locked.
- A send/trigger race cannot deliver a blocked message.
- Existing guard and transport tests pass.

**Exit gate:** bidirectional gating is deterministic and current demos are unchanged.

## Phase 3 - Portable credential bundles

**Implement**

- Trusted provisioning outputs organizer, Alice bundle, and Bob bundle directories.
- Device bundle manifest with role and non-secret defaults.
- Bundle inspection and validation without private-key disclosure.
- Refusal of overwrites, wrong roles, invalid pins, missing files, and weak passwords.

**Verify**

- Copy bundles into isolated directories and establish mutual TLS.
- Assert neither bundle contains `ca.key` or the peer's private key.
- Test swapped, altered, and incomplete bundles.
- Connect to Bob's numeric IP using `bob.local` as TLS server name.

**Exit gate:** USB-copyable bundles authenticate correctly and contain only endpoint material.

## Phase 4 - Loopback browser bridge

**Implement**

- FastAPI service bound only to `127.0.0.1:8766` on each device.
- Same-origin WebSocket commands for unlock, start/connect, send, verify, demo mode, and disconnect.
- Server events for state, chat, verification, session, trust, and sanitized errors.
- Bounded WebSocket queues and strict command validation.

**Verify**

- Same-origin browser clients connect; foreign origins and LAN requests fail.
- Invalid commands cannot crash the runtime.
- Password markers never appear in emitted state, logs, or exceptions.

**Exit gate:** a test browser can operate its local runtime, while other devices cannot access the UI service.

## Phase 5 - Bob application

**Implement**

- Bob runtime: unlock bundle, start TLS listener on `0.0.0.0:8765`, list private IPv4 addresses, accept one Alice, and reject additional peers.
- Bob UI: chat bubbles, timestamps, send state, connection badge, safety-code modal, demo-condition notice, and sanitized recovery errors.
- In-memory state reconstruction after browser refresh and preservation through verified TLS reconnects.

**Verify**

- Correct/wrong password, occupied port, one-peer limit, refresh, disconnect, and shutdown cases.
- Confirm Bob UI/state exposes no trust score, graph, audit history, or anomaly controls.

**Exit gate:** Bob launches, displays a usable address, and behaves as a clean chat endpoint.

## Phase 6 - Alice application and dashboard

**Implement**

- Alice runtime: unlock bundle, validate private IPv4 input, connect to the IP with TLS name `bob.local`, and manage `SessionGuard`.
- Combined chat/observatory UI with trust score, delta, graph, raw/normalized signals, session/TLS details, key epoch, verification state, and metadata-only timeline.
- Strict separation between the in-memory conversation and dashboard/audit snapshots.

**Verify**

- Valid LAN address, invalid/public address, unavailable host, wrong CA/pin/hostname, and reconnect cases.
- Search SQLite, emitted telemetry, logs, and artifacts for message markers.
- Run existing dashboard tests.

**Exit gate:** Alice connects securely and is the only side with trust observability.

## Phase 7 - Dual safety-code verification

**Implement**

- Independently derive the same grouped code from the authenticated relationship ID on both devices.
- Correlate both decisions by request ID and relationship.
- Require MATCH/MATCH; fail on mismatch, cancel, timeout, disconnect, stale response, or conflicting response.
- Apply verified trust floor on success; restrict and close on failure.

**Verify**

- Test every two-user response combination.
- Test stale/duplicate responses and different relationships.
- Prove chat remains blocked until both approvals arrive.
- Prove neither side treats a peer-supplied display code as authoritative.

**Exit gate:** both humans must approve the locally calculated code before chat activates.

## Phase 8 - Real bidirectional chat and measurement

**Implement**

- Independent Alice/Bob send and receive loops instead of echo behavior.
- Ordered in-memory messages, acknowledgments, and duplicate-display prevention.
- Periodic ping/pong feeding genuine RTT and variation into Alice's collector.
- Continue handshake, timing, continuity, and establishment measurements.
- Clear conversation/sensitive runtime state on process exit.

**Verify**

- Both directions, simultaneous sends, rapid sends, Unicode, maximum size, refresh, and disconnect-during-send.
- Confirm idle periods do not create false anomalies solely because nobody is typing.
- Repeat payload-leak searches across logs, SQLite, UI telemetry, and artifacts.

**Exit gate:** two users can sustain a real encrypted conversation while Alice observes live metadata.

## Phase 9 - Reverification and fresh TLS recovery

**Implement**

- Pause chat immediately on a verification decision.
- Complete dual verification using permitted control envelopes.
- Notify Bob before closing the old session, reconnect with mutual TLS, and verify the relationship ID is unchanged.
- Display the new session/key-epoch identifier and preserve in-memory conversation display.
- Restrict on changed identity or failed recovery.

**Verify**

- Successful reverification changes session/key epoch but not relationship.
- No chat crosses the reconnect boundary while gated.
- Wrong replacement identity and reconnect failure close safely.
- MISMATCH prevents recovery.

**Exit gate:** trigger, pause, compare, reconnect, and resume works as one reliable flow.

## Phase 10 - Controlled anomalies

**Implement**

- `Induce latency`: Bob delays pong/chat handling; label `REAL INDUCED CONDITION`.
- `Reconnect burst`: bounded real TLS reconnects; label `REAL CONNECTION EVENT`.
- `Simulate IP continuity change`: alter only trust metadata; label `SIMULATED METADATA`.
- `Restore normal`: remove every active condition.
- Allow only one active condition, prevent infinite reconnects, and audit start/stop without payloads.

**Verify**

- Latency changes genuine RTT and visible delivery time.
- Reconnect burst changes session IDs and establishment count.
- Continuity simulation changes only its declared trust input.
- A sharp drop triggers dual verification; restore removes the condition.

**Exit gate:** the presenter can reproduce the complete security response with honest real/simulated labels.

## Phase 11 - Failure handling and security regression

**Implement**

- Actionable sanitized handling for wrong IP/password, firewall rejection, Wi-Fi loss, shutdown, browser closure, timeout, malformed traffic, and failed reconnect.
- Bounded manual retry, queue limits, one-peer enforcement, replay protection, and single active verification.
- Loopback/trusted-host/origin protections for both local web services.

**Verify**

- Re-run TLS corruption, CA/pin/hostname, framing, timeout, concurrency, and log-leak tests.
- Inspect all persistent schemas and browser snapshots for prohibited data.
- Run the complete suite.

**Exit gate:** ordinary failures are recoverable where safe, and security failures always close without leakage.

## Phase 12 - One-click Windows operation

**Implement**

- `setup-demo.cmd`, `provision-demo.cmd`, `start-bob.cmd`, and `start-alice.cmd`.
- Preflight checks for environment, OpenSSL, credentials, ports, private addresses, and reachability.
- Automatic opening of the correct local page, but no automatic Windows Firewall modification.
- Documentation for allowing Python on Private networks only.

**Verify**

- Test fresh setup, paths containing spaces, missing bundles, occupied ports, unavailable Bob, and clean shutdown.

**Exit gate:** each participant starts the demo by double-clicking one launcher.

## Phase 13 - Physical two-laptop acceptance

Run twice from clean starts:

1. Provision and transfer Bob's bundle by USB.
2. Start Bob and record the displayed LAN IPv4 address.
3. Start Alice, enter the address, and connect.
4. Compare the safety code and select MATCH on both laptops.
5. Exchange simultaneous messages.
6. Show Alice's live TLS, RTT, timing, and trust values.
7. Induce latency and show real measurement changes.
8. Trigger MATCH/MATCH reverification and show the fresh TLS epoch.
9. Resume the existing in-memory conversation.
10. Trigger another verification and select MISMATCH.
11. Confirm both sides close and cannot send.
12. Inspect the audit trail and confirm message text is absent.

**Exit gate:** both complete runs succeed with no unlabelled simulation.

## Phase 14 - Handoff and presentation package

**Implement**

- Update README, architecture, setup, security limitations, and troubleshooting.
- Add a two-device network diagram, real-versus-simulated table, recovery guide, and short presenter script.
- Record exact final environment and test evidence in `BUILD_STATUS.md`.

**Final verification**

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m client.final_demo
.\.venv\Scripts\python.exe -m pip check
git diff --check
```

**Definition of done:** two Windows laptops exchange real encrypted messages; both users control safety-code verification; Alice alone displays the live adaptive-trust observatory and anomaly controls; Bob retains a normal chat UI; MATCH produces a fresh authenticated TLS session; MISMATCH fails closed; and no chat content or secrets enter persistent telemetry.
