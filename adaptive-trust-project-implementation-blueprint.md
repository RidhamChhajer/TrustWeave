# Adaptive Trust-Triggered Cryptographic Verification
## Project Implementation Blueprint

### Purpose

This document defines the recommended scope, architecture, implementation boundaries, security rules, experiments, and AI-development rules for the Computer Network Technology project:

**Adaptive Trust-Triggered Cryptographic Verification and Key Lifecycle Management in End-to-End Encrypted Communication**

The project should be implemented as a working experimental prototype, not as a production-ready cryptographic protocol.

---

# 1. Core Project Concept

The system should demonstrate an adaptive security layer operating above an encrypted communication system.

The central idea is:

```text
Encrypted Communication
        ↓
Observable Session Metadata
        ↓
Context Signal Collector
        ↓
Trust Assessment Engine
        ↓
S(t) + ΔS
        ↓
Verification Trigger Engine
        ↓
Out-of-Band Identity Verification
        ↓
Key Lifecycle Controller
        ↓
Encrypted Communication
```

The five core functional modules are:

1. Context Signal Collector
2. Trust Assessment Engine
3. Relationship Memory Store
4. Verification Trigger Engine
5. Key Lifecycle Controller

The **Verification Trigger Engine is the centerpiece**. Trust computation and key lifecycle management are supporting infrastructure.

---

# 2. Project Scope

## Build

Build:

- Alice client
- Bob client
- Secure encrypted communication
- Cryptographic session/key establishment using established libraries
- Observable network/session metadata collection
- Contextual trust scoring
- Trust rate-of-change calculation
- Persistent relationship trust history
- Automatic verification triggering
- Out-of-band identity verification simulation
- Verification pass/fail handling
- Key lifecycle/re-establishment logic
- Dashboard
- Event logging
- Controlled experiments
- Quantitative evaluation
- Unit tests

## Do NOT build

Do not attempt to build:

- Signal Protocol from scratch
- WhatsApp-like production messaging
- A custom encryption algorithm
- A custom cryptographic key-exchange protocol
- Production-grade E2E messaging infrastructure
- Real interception of third-party communications
- An ML model merely for appearance
- Blockchain or other unrelated technologies

The project contribution is the adaptive verification decision layer, not a new encryption primitive.

---

# 3. High-Level Architecture

```text
                ┌──────────────────────────┐
                │   Encrypted Communication│
                │        Prototype         │
                └────────────┬─────────────┘
                             │
                             ▼
                 Observable Session Metadata
                             │
                             ▼
              ┌──────────────────────────┐
              │ Context Signal Collector │
              └────────────┬─────────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │ Trust Assessment Engine  │
              │                          │
              │ S(t) + ΔS                │
              └────────────┬─────────────┘
                           │
                 ┌─────────┴──────────┐
                 ▼                    ▼
       Relationship Memory      Current Session
              Store                  State
                 │                    │
                 └─────────┬──────────┘
                           ▼
              ┌──────────────────────────┐
              │ Verification Trigger     │
              │ Engine                   │
              └────────────┬─────────────┘
                           │
                   Verification?
                    /             \
                  YES              NO
                   │                │
                   ▼                ▼
             OOB verification   Continue
                   │
              ┌────┴────┐
              │         │
            PASS       FAIL
              │         │
              ▼         ▼
          Continue    Restrict/
          session     terminate
              │
              ▼
       Key Lifecycle Controller
              │
              ▼
       Cryptographic Key
       Establishment / Renewal
```

---

# 4. Secure Communication Layer

Use two simulated communicating parties:

```text
Alice Client
     │
     │ encrypted communication
     │
     ▼
Bob Client
```

The communication layer should provide:

- Session establishment
- Key establishment
- Encryption
- Decryption
- Session identifier
- Public identity information
- Connection state

## Cryptography rule

Never invent cryptography.

Use established cryptographic libraries and standard primitives.

The project is about adaptive security decisions, not about inventing AES, key exchange, hashing, or authentication algorithms.

---

# 5. Context Signal Collector

The collector must use observable transport/session metadata and must NOT inspect plaintext message content.

Recommended signals:

## 5.1 Handshake latency

Compare current key-establishment/connection timing against the historical baseline.

Example:

```text
Historical average = 42 ms
Current handshake = 46 ms
```

Normal.

Potential anomaly example:

```text
Historical average = 42 ms
Current handshake = 280 ms
```

Do not claim that this proves an attack.

---

## 5.2 RTT variation

Measure socket/network round-trip time.

Normal:

```text
40 ms
43 ms
41 ms
44 ms
```

Anomalous example:

```text
40 ms
190 ms
52 ms
230 ms
```

Again, an anomaly is not proof of an attack.

---

## 5.3 Session continuity

Track session/client continuity indicators.

Example:

```text
Session 1:
Device = A1
Network = N1

Session 2:
Device = A1
Network = N1

Session 3:
Device = A7
Network = N8
```

A significant unexpected change can reduce contextual trust.

---

## 5.4 Communication timing

Use metadata such as:

- Inter-message timing
- Burst frequency
- Session activity

Do not inspect the content of messages.

---

## 5.5 Key/session renegotiation behavior

Track the frequency of key establishment/session re-initiation within a rolling window.

Example:

```text
Normal:
1 establishment / 10 minutes

Suspicious:
14 establishments / 2 minutes
```

This is an input to the trust engine, not proof of malicious activity.

---

# 6. Trust Assessment Engine

Start with a transparent and explainable mathematical model.

Do not introduce ML unless specifically required later.

## 6.1 Normalize signals

Convert signal measurements into normalized scores.

Target range:

```text
0 → 100
```

Then combine them:

```text
current_signal_score =
    w1 × handshake_score
  + w2 × RTT_score
  + w3 × continuity_score
  + w4 × timing_score
  + w5 × renegotiation_score
```

Weights must be configurable.

Do not use unexplained random weights.

---

# 7. Trust Score

Use a weighted exponential moving average as the initial implementation:

```text
S(t) = α × current_score
     + (1 − α) × S(t−1)
```

Where:

- `S(t)` = current trust representation
- `current_score` = current contextual signal score
- `α` = configurable decay/smoothing factor
- `S(t−1)` = previous trust score

Example:

```text
α = 0.3
previous trust = 82
current score = 65

S(t) =
0.3 × 65 +
0.7 × 82

= 76.9
```

The mathematical formulation should remain configurable.

---

# 8. Trust Rate of Change — ΔS

This is one of the most important project components.

Calculate:

```text
ΔS = S(t) − S(t−1)
```

Example:

```text
Previous trust = 91
Current trust = 83

ΔS = -8
```

Suppose:

```text
δ = 7
```

Then:

```text
ΔS <= -δ

-8 <= -7

TRUE

→ VERIFY NOW
```

The system must evaluate this sudden negative change independently from the absolute trust score.

This allows a highly trusted session to trigger verification immediately after a sharp anomaly.

---

# 9. Relationship Memory Store

Do not treat every session as completely independent.

Persist relationship-level trust history.

Example:

```text
relationship_id:
Alice-Bob

trust_history:
91
90
92
89
91
```

Recommended stored information:

```text
relationship_id
last_verified
verification_count
successful_verifications
failed_verifications
baseline_rtt
baseline_handshake_time
known_device/session indicators
trust history
```

Do not store plaintext messages.

The store should contain security-relevant metadata and trust history, not communication content.

SQLite is sufficient for the prototype.

Recommended tables:

```text
relationships
sessions
trust_history
verification_events
key_events
```

---

# 10. Verification Trigger Engine

This is the star of the project.

Inputs:

```text
S(t)
ΔS
relationship history
verification status
security policy
```

Use a clear state/decision model.

## Trusted

```text
S >= T1
AND
ΔS > -δ
```

Action:

```text
ALLOW
```

## Normal

```text
T2 <= S < T1
```

Action:

```text
ALLOW
```

Continue monitoring.

## Low Trust

```text
S < T2
```

Action:

```text
VERIFY
```

## Sudden Trust Drop

```text
ΔS <= -δ
```

regardless of absolute trust.

Action:

```text
VERIFY IMMEDIATELY
```

---

# 11. Out-of-Band Identity Verification

The prototype should demonstrate an identity verification workflow.

Example:

```text
Security verification required

Reason:
Sudden trust decrease

Trust:
91 → 73

ΔS:
-18
```

Then show identity fingerprints/authentication values.

Example:

```text
Alice fingerprint:
A7C4...91F

Bob fingerprint:
A7C4...91F
```

User can select:

```text
MATCH
```

or:

```text
MISMATCH
```

## Successful verification

```text
Verification successful
→ Continue session
→ Update relationship memory
→ Apply key lifecycle policy
```

## Failed verification

```text
Verification failed
→ Restrict or terminate session
→ Alert communicating parties
→ Do not proceed with normal key lifecycle action
```

---

# 12. Key Lifecycle Controller

The Key Lifecycle Controller operates after the verification decision is resolved.

Possible actions:

| Condition | Action |
|---|---|
| High trust | Continue normal cryptographic lifecycle |
| Normal trust | Standard rotation policy |
| Low trust | Verify and re-establish key if verification succeeds |
| Sudden anomaly | Verify immediately and re-establish key after successful verification |
| Verification failure | Restrict/terminate |

## Important safety rule

Do not blindly implement:

```text
High trust → extend key lifetime indefinitely
```

High trust should not automatically weaken cryptographic hygiene.

A safer prototype policy is:

```text
High trust
→ normal cryptographic lifecycle

Elevated risk / successful verification
→ controlled key re-establishment
```

The project can study adaptive key actions without creating unnecessary security weaknesses.

---

# 13. Dashboard

Create a visual dashboard showing:

```text
ADAPTIVE TRUST SECURITY ENGINE

Alice ↔ Bob

Trust Score: 87
Trust Change: -3
Status: TRUSTED

SIGNALS
Handshake latency: 42 ms
RTT: 45 ms
Session continuity: NORMAL
Timing anomaly: LOW
Key renegotiations: 1

VERIFICATION
Last verification: ...
Status: VERIFIED

KEY LIFECYCLE
Current key: ...
Key age: ...
Next action: ...
```

The dashboard should update when signals and trust change.

---

# 14. Trust Graph

Display trust over time.

Example:

```text
Trust
100 |
 90 | █ █ █ █
 80 | █ █ █ █
 70 | █ █ █ █     █
 60 | █ █ █ █     █
    +-------------------
       t1 t2 t3 t4 t5
```

For an anomaly:

```text
92 → 90 → 91 → 89 → 65

ΔS = -24

VERIFICATION TRIGGERED
```

This should be one of the main visual demonstrations.

---

# 15. Real Network Mode and Experiment Mode

Use two modes.

## Real Network Mode

```text
Alice Client
     ↓
TCP/TLS network
     ↓
Bob Server

Real measurements
```

Collect actual networking/session measurements.

## Controlled Experiment Mode

Allow controlled injection of:

- Latency spikes
- RTT variation
- Session continuity changes
- Device changes
- Key/session renegotiation spikes
- Gradual anomalies
- Sudden anomalies

This gives reproducible experiments without requiring real attacks.

---

# 16. Experiments

At minimum implement these six scenarios.

## Experiment 1 — Normal Communication

Conditions:

- Stable network
- Stable device/session
- Normal handshake
- Normal communication

Expected:

```text
Trust remains high
No verification
```

---

## Experiment 2 — Gradual Degradation

Introduce small anomalies over multiple sessions.

Expected:

```text
Trust gradually decreases
```

Eventually:

```text
S < T2
→ verification
```

---

## Experiment 3 — Sudden Anomaly

Start:

```text
Trust = 92
```

Then introduce:

```text
Trust = 69
ΔS = -23
```

Expected:

```text
IMMEDIATE VERIFICATION
```

This is a primary experiment.

---

## Experiment 4 — New Relationship

Example:

```text
Alice ↔ Charlie
```

No historical trust.

Expected:

```text
Conservative starting trust
Earlier verification
```

---

## Experiment 5 — Established Relationship

Run several normal sessions:

```text
Alice ↔ Bob

82
87
91
93
```

Expected:

```text
Higher baseline trust
Fewer unnecessary verification events
```

---

## Experiment 6 — Verification Failure

Introduce anomaly:

```text
verification = FAIL
```

Expected:

```text
Session restricted/terminated
Alert generated
```

---

# 17. Quantitative Evaluation

Do not only show that the application runs.

Measure results.

## Verification frequency

```text
verification events / sessions
```

Compare adaptive behavior with a chosen baseline policy.

## Detection latency

Measure:

```text
anomaly occurrence
        ↓
trust update
        ↓
verification trigger
```

## False verification rate

For normal scenarios:

```text
unnecessary verifications / normal sessions
```

## Anomaly detection rate

For controlled injected anomalies:

```text
detected injected anomalies /
total injected anomalies
```

Do not call this real-world attack detection accuracy unless the methodology actually supports that claim.

---

# 18. Security Claims to Avoid

Do not write:

> "Our system detects man-in-the-middle attacks."

Prefer:

> "Our system detects contextual anomalies that may indicate elevated session risk and triggers high-assurance identity verification."

Reason:

```text
High RTT
```

can result from:

- poor Wi-Fi
- VPN
- mobile networks
- congestion
- server load
- routing changes

It does not prove an attack.

---

# 19. Critical Conceptual Distinctions

The implementation must distinguish:

```text
Contextual anomaly
        ≠
Confirmed attack

Elevated contextual risk
        ≠
Cryptographic identity proof

Trust score
        ≠
Identity verification
```

The intended architecture is:

```text
Context signals
      ↓
Trust assessment
      ↓
Something looks unusual
      ↓
Cryptographic identity verification
      ↓
Identity confirmed or rejected
```

---

# 20. Recommended Technology Stack

Recommended simple stack:

```text
Language:
Python

Networking:
asyncio / sockets

Cryptography:
Established Python cryptography library

Database:
SQLite

Backend:
FastAPI

Frontend:
HTML/CSS/JavaScript
```

A React frontend is optional. Do not add it if it increases unnecessary complexity.

---

# 21. Recommended Folder Structure

```text
adaptive-trust-engine/
│
├── client/
│   ├── alice.py
│   └── bob.py
│
├── crypto/
│   ├── key_exchange.py
│   ├── encryption.py
│   └── identity.py
│
├── network/
│   ├── connection.py
│   ├── metrics.py
│   └── session.py
│
├── trust/
│   ├── signal_collector.py
│   ├── trust_engine.py
│   ├── thresholds.py
│   └── anomaly.py
│
├── verification/
│   ├── trigger_engine.py
│   └── verification.py
│
├── lifecycle/
│   └── key_controller.py
│
├── storage/
│   ├── database.py
│   └── relationship_store.py
│
├── experiments/
│   ├── normal.py
│   ├── latency_spike.py
│   ├── sudden_drop.py
│   └── verification_failure.py
│
├── dashboard/
│
├── tests/
│
├── docs/
│
└── README.md
```

---

# 22. Event Logging

Implement an auditable event log.

Example:

```text
12:31:02 SESSION_STARTED
12:31:02 HANDSHAKE_COMPLETED
12:31:02 RTT=43ms
12:31:02 TRUST=91
12:31:05 TRUST=90
12:31:08 RTT_ANOMALY
12:31:08 TRUST=72
12:31:08 DELTA=-18
12:31:08 VERIFICATION_TRIGGERED
12:31:12 VERIFICATION_SUCCESS
12:31:12 NEW_KEY_ESTABLISHED
```

Never log:

- plaintext messages
- private keys
- secret material

---

# 23. Unit Tests

At minimum test:

## Trust engine

```text
Normal signals → expected trust
Bad/anomalous signals → reduced trust
```

## Delta

```text
90 → 88 = -2
90 → 60 = -30
```

## Trigger

```text
S=90, ΔS=-2 → NO VERIFY

S=40, ΔS=-2 → VERIFY

S=90, ΔS=-30 → VERIFY
```

## Verification

```text
PASS → continue
FAIL → restrict
```

## Relationship memory

```text
Session 1 trust
     ↓
Session 2
     ↓
History incorporated
```

---

# 24. Security Implementation Rules

Never:

- Store private keys in plaintext
- Hard-code cryptographic keys
- Use MD5/SHA-1 for security purposes
- Use passwords directly as encryption keys
- Send private keys over the network
- Log plaintext
- Log private keys
- Invent encryption
- Treat network anomalies as proof of attacks
- Claim production-grade security

Use proper key generation, storage, and cryptographic libraries.

---

# 25. Report Structure

Recommended report:

```text
1. Introduction
2. Problem Statement
3. Motivation
4. Existing Systems
5. Limitations of Existing Systems
6. Proposed System
7. Objectives
8. System Architecture
9. Network Architecture
10. Cryptographic Architecture
11. Context Signal Collection
12. Trust Assessment Algorithm
13. Relationship Memory
14. Verification Trigger Algorithm
15. Key Lifecycle Management
16. Implementation
17. Database Design
18. Experimental Methodology
19. Test Scenarios
20. Results
21. Performance Analysis
22. Security Analysis
23. Limitations
24. Future Scope
25. Conclusion
26. References
```

---

# 26. Required Architecture Diagrams

Create at least three diagrams.

## Diagram 1 — High-level architecture

Show:

```text
Alice
 ↓
Encrypted Session
 ↓
Context Collector
 ↓
Trust Engine
 ↓
Trigger Engine
 ↓
Verification
 ↓
Key Controller
 ↓
Encrypted Session
 ↓
Bob
```

## Diagram 2 — Trust engine

Show:

```text
RTT
Handshake
Continuity
Timing
Key Events
    ↓
Normalization
    ↓
Weighted Score
    ↓
EMA
   ↙ ↘
 S(t) ΔS
   ↘ ↙
 Trigger Engine
```

## Diagram 3 — Decision state machine

Show:

```text
START
  ↓
Collect Signals
  ↓
Calculate S(t)
  ↓
Calculate ΔS
  ↓
ΔS <= -δ?
 /       \
YES       NO
 |         |
VERIFY    S < T2?
          /   \
        YES    NO
         |      |
       VERIFY  CONTINUE
```

---

# 27. Final Demonstration Flow

The preferred final demo:

## Step 1 — Start Alice and Bob

```text
Connection established
Trust: 50
Verification: Required
```

## Step 2 — Verify identities

```text
Fingerprint match ✓
Verification successful
Trust: 75
```

## Step 3 — Run normal sessions

```text
Session 1 → 82
Session 2 → 87
Session 3 → 91
Session 4 → 93
```

Show:

```text
Relationship status: ESTABLISHED
```

## Step 4 — Inject sudden anomaly

Introduce:

```text
RTT spike
+
session continuity change
+
renegotiation spike
```

Result:

```text
93 → 71

ΔS = -22

HIGH-RISK CHANGE
OUT-OF-BAND VERIFICATION REQUIRED
```

## Step 5 — Show failed verification

```text
Fingerprint mismatch ✗
SESSION RESTRICTED
```

## Step 6 — Repeat with successful verification

```text
Fingerprint match ✓
Verification successful
New cryptographic key established
SESSION RESTORED
```

---

# 28. Development Order

Do NOT ask an AI to generate the entire project in one step.

Build incrementally:

```text
Phase 1  → Basic Alice ↔ Bob networking
Phase 2  → Cryptographic session establishment
Phase 3  → Encrypted communication
Phase 4  → Real metadata collection
Phase 5  → Trust scoring
Phase 6  → ΔS calculation
Phase 7  → Verification Trigger Engine
Phase 8  → Verification workflow
Phase 9  → Relationship Memory Store
Phase 10 → Key Lifecycle Controller
Phase 11 → Dashboard
Phase 12 → Experiment framework
Phase 13 → Experiments
Phase 14 → Quantitative results
Phase 15 → Documentation/report
Phase 16 → PPT/viva preparation
```

A separate phase-by-phase coding plan should be created later.

---

# 29. AI Developer Rules — MUST FOLLOW

When using Codex, Claude, or another coding AI, provide these rules.

1. Do not invent cryptographic algorithms.

2. Use established cryptographic libraries.

3. Never use plaintext message content for trust scoring.

4. Do not equate contextual anomalies with confirmed attacks.

5. Do not claim MITM detection unless experimentally demonstrated.

6. Do not introduce ML unless explicitly requested.

7. Do not create fake networking when real networking is required.

8. Keep the Verification Trigger Engine as the central decision component.

9. Keep trust score `S(t)` and rate-of-change `ΔS` as separate variables.

10. A sharp negative `ΔS` must be evaluated independently of the absolute trust threshold.

11. Relationship trust must persist across sessions.

12. When verification is required, do not silently continue normal communication before the verification decision is resolved.

13. Failed verification must result in restriction/termination according to the defined policy.

14. Key lifecycle actions must occur only after the verification decision is resolved.

15. Never hard-code cryptographic secrets.

16. Never log plaintext messages or private keys.

17. Every security-sensitive operation must be auditable.

18. Every threshold must be configurable.

19. Every important algorithm must have unit tests.

20. Do not add technologies merely to make the project look more advanced.

21. Do not change the core architecture without explaining why.

22. Do not silently replace the EMA model with an ML model.

23. Distinguish clearly between:
    - contextual anomaly
    - elevated risk
    - identity verification
    - confirmed attack

24. All experimental claims must be backed by measured results.

25. The prototype must be presented as an experimental security system, not a production-grade secure messenger.

26. Prefer simple, explainable implementations over unnecessary abstractions.

27. Do not generate large amounts of code before validating the current component.

28. Do not silently change requirements.

29. Do not remove security checks just to make tests pass.

30. Do not fabricate experimental results.

31. Do not fabricate citations, benchmarks, protocol capabilities, or security guarantees.

32. If an implementation choice has security implications, explicitly explain the trade-off before implementing it.

33. Keep networking, cryptography, trust assessment, verification, storage, and key lifecycle components modular and testable.

34. Every anomaly injection used in experiments must be clearly marked as controlled simulation, not a real attack.

35. Keep the core research/project contribution focused on adaptive automatic invocation of high-assurance identity verification.

---

# 30. Recommended Final Project Scope

The ideal finished project is:

```text
Python
+
TCP/TLS or equivalent secure communication
+
Established cryptographic library
+
SQLite
+
FastAPI/dashboard
+
5 contextual metadata signals
+
EMA trust score
+
Independent ΔS trigger
+
Relationship memory
+
Out-of-band fingerprint verification simulation
+
Adaptive key re-establishment
+
6 controlled experiments
+
Quantitative evaluation
+
Unit tests
+
Audit/event logging
```

This is already a substantial Computer Network Technology project.

Do not add AI, blockchain, LLMs, or unrelated technologies merely to increase the apparent complexity.

The quality of the networking implementation, trust model, trigger logic, experiments, measurements, security reasoning, and demonstration is more important than the number of technologies used.
