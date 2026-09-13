# Two-device presenter script

Use [operation instructions](two-device-operation.md) for setup. Physical acceptance
is still pending; complete [both recorded runs](two-device-acceptance.md) before
describing the demo as validated on two laptops. Allow several minutes for startup,
comparison, trust stabilization, recovery, and discussion; timing depends on the LAN.

## Before presenting

Prepare both device bundles through trusted provisioning and USB transfer. Keep
passwords separate. Use the same private Wi-Fi and allow Python on Private networks
only. Close any legacy dashboard using UI port 8766. Start both local services from
clean application starts and arrange the two screens so the code can be compared.
Do not project passwords or capture chat contents in saved presentation evidence.

## Spoken walkthrough

1. **Introduce the boundary.** “TLS provides encryption and authenticated identities.
   Our adaptive layer observes connection metadata and decides when to ask the two
   people to verify again. It does not read message contents to calculate trust.”
2. **Connect.** Bob unlocks and starts his listener. Alice unlocks, enters Bob's
   displayed private Wi-Fi IPv4, and connects. “Alice has the trust observatory;
   Bob has a normal chat interface. Neither local browser service is exposed to Wi-Fi.”
3. **Compare.** Read the complete grouped safety code directly on both screens.
   Select MATCH on one side first and point out that sending remains disabled.
   Select MATCH on the other side within the 30-second window. “Both independent
   decisions are needed. Neither endpoint copies the other endpoint's display code.”
4. **Chat.** Send short messages simultaneously from both devices. Show delivery
   status, TLS 1.3 and live RTT. Leave typing idle while heartbeat observations continue.
   “Conversation is in memory; the audit records metadata.”
5. **Induce latency.** Let normal trust stabilize, preferably above 96. Click Induce
   latency on Alice. “This is REAL INDUCED CONDITION: Bob actually delays pong/chat
   handling by 3.2 seconds. It is controlled delay, not a claim of a real attacker.”
   Show RTT and trust/delta changes. Trigger timing depends on actual measurements;
   never describe a prompt as guaranteed at an arbitrary starting score.
6. **Recover.** When verification appears, show that both send boxes are locked.
   Use Alice's **Restore normal condition** button inside the modal, compare again,
   and choose MATCH on both. Record the public epoch before/after if desired.
   “The relationship stays the same, but the TLS session and traffic-key epoch are
   fresh. The existing in-memory conversation remains visible.” Send another message.
7. **Reject.** Allow observations to stabilize again, induce latency, and select
   MISMATCH on one device at the next prompt. “Uncertainty closes the session.”
   Show both connection states and disabled sending. Do not claim silent recovery.
8. **Inspect the boundary.** Show Alice's audit timeline without exporting a full
   browser snapshot. “These are signal, trust, verification and lifecycle events;
   no message bodies are written here.” End both local services with Ctrl+C.

## Explain the controls accurately

| Control | Mechanism | Exact label |
|---|---|---|
| Induce latency | Bob delays actual chat/pong work | REAL INDUCED CONDITION |
| Reconnect burst | Up to three real fresh pinned TLS sessions | REAL CONNECTION EVENT |
| Simulate IP continuity change | Only the trust input changes to a documentation IP | SIMULATED METADATA |
| Restore normal | Removes the active condition; past observations may still affect history | NORMAL OBSERVATION |

Only one mode runs at a time. IP simulation or a bounded reconnect burst may reduce
trust without independently crossing a verification threshold. A bounded burst must
finish before another mode is selected. These are demonstrations of response to
controlled conditions, not measured detection rates for real attacks.

## If a step fails

- Wrong password/bundle: retry locally or restore the intact matching bundle.
- No connection: check Bob's listener, private Wi-Fi IPv4, adapter choice, firewall
  Private-network permission, occupied ports and guest-network client isolation.
- Comparison expires or someone cancels/rejects: restart Bob's listener, explicitly
  reconnect Alice, and compare again. Do not bypass the gate.
- Recovery fails: show the closed state honestly, retain only sanitized failure
  observations, fix the cause and repeat the physical acceptance run from the start.
- Repeated anomaly prompts: restore normal and let genuine measurements stabilize.
  Do not alter the displayed score or disable TLS checks to finish a presentation.

For questions about limitations, explain trusted provisioning, trusted local
endpoints, metadata retention, the recorded older runtime, and pending physical
acceptance. The original dashboard's comparisons and experiment metadata remain
explicitly simulated; they are a separate demonstration path.
