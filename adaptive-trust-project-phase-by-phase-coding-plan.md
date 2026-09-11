# Adaptive Trust-Triggered Cryptographic Verification
# Phase-by-Phase Coding & Implementation Plan

## Purpose

This is the implementation plan for the project:

**Adaptive Trust-Triggered Cryptographic Verification and Key Lifecycle Management in End-to-End Encrypted Communication**

Use this document with Codex/Claude as the **coding roadmap**.

The implementation must be incremental. Do not ask the coding AI to build the whole project at once.

The project should be built, tested, committed, and validated phase by phase.

---

# 0. Non-Negotiable Development Rules

Before writing code, the coding AI must follow these rules.

1. Never invent cryptographic algorithms.
2. Use established cryptographic libraries.
3. Never use plaintext message content for trust scoring.
4. Do not claim that contextual anomalies prove MITM or another attack.
5. Use controlled anomaly simulation for experiments.
6. Keep `S(t)` and `ΔS` as separate concepts.
7. A sharp negative `ΔS` must be independently capable of triggering verification.
8. Relationship history must persist across sessions.
9. Verification must be resolved before security-sensitive continuation when the trigger fires.
10. Failed verification must restrict or terminate the session according to policy.
11. Key lifecycle actions happen only after the verification decision is resolved.
12. Never hard-code private keys or secrets.
13. Never log plaintext messages or private keys.
14. Do not fabricate experimental results.
15. Do not fabricate citations, benchmarks, or security guarantees.
16. Do not introduce ML unless explicitly requested.
17. Do not add blockchain or unrelated technologies.
18. Do not replace the proposed architecture silently.
19. Keep every major component modular and testable.
20. Write tests alongside implementation.
21. Do not proceed to the next phase if the current phase's acceptance criteria fail.
22. Prefer a simple working implementation over premature abstraction.
23. Make thresholds and weights configurable.
24. Every security-sensitive decision must be visible in logs.
25. Experimental attack/anomaly injection must be clearly identified as simulation.
26. Do not use random values to fake measured networking data in Real Network Mode.
27. Simulation Mode may inject controlled values, but those values must be explicitly labelled simulated.
28. Do not claim production readiness.
29. Do not expose secret material through the dashboard.
30. Do not make the trust score itself a replacement for cryptographic identity verification.

---

# 1. Recommended Stack

Use this stack unless there is a documented reason to change it.

```text
Language:
Python 3.x

Networking:
asyncio / sockets

Cryptography:
Python cryptography library

Database:
SQLite

Backend/API:
FastAPI

Frontend:
HTML/CSS/JavaScript initially

Testing:
pytest

Configuration:
environment variables + configuration module

Version control:
Git
```

Do not add React, Docker, Redis, PostgreSQL, Kubernetes, ML frameworks, etc. until they are actually necessary.

---

# 2. Target Repository Structure

Build toward this structure incrementally:

```text
adaptive-trust-engine/
│
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
│
├── config/
│   ├── __init__.py
│   └── settings.py
│
├── client/
│   ├── __init__.py
│   ├── alice.py
│   └── bob.py
│
├── crypto/
│   ├── __init__.py
│   ├── key_exchange.py
│   ├── encryption.py
│   └── identity.py
│
├── network/
│   ├── __init__.py
│   ├── connection.py
│   ├── metrics.py
│   └── session.py
│
├── trust/
│   ├── __init__.py
│   ├── signal_collector.py
│   ├── normalization.py
│   ├── trust_engine.py
│   ├── thresholds.py
│   └── anomaly.py
│
├── verification/
│   ├── __init__.py
│   ├── trigger_engine.py
│   └── verification.py
│
├── lifecycle/
│   ├── __init__.py
│   └── key_controller.py
│
├── storage/
│   ├── __init__.py
│   ├── database.py
│   └── relationship_store.py
│
├── dashboard/
│   ├── static/
│   ├── templates/
│   └── app.py
│
├── experiments/
│   ├── normal.py
│   ├── gradual_degradation.py
│   ├── sudden_drop.py
│   ├── new_relationship.py
│   ├── established_relationship.py
│   └── verification_failure.py
│
├── tests/
│   ├── test_crypto.py
│   ├── test_network.py
│   ├── test_trust.py
│   ├── test_trigger.py
│   ├── test_memory.py
│   └── test_lifecycle.py
│
└── docs/
    ├── architecture.md
    ├── algorithms.md
    └── experiments.md
```

Do not create every file immediately. Create files when their phase begins.

---

# PHASE 1 — Project Foundation

## Goal

Create a clean Python project with reproducible setup and Git.

## Tasks

1. Create repository.
2. Create Python virtual environment.
3. Create `requirements.txt`.
4. Create `.gitignore`.
5. Create initial package structure.
6. Create configuration module.
7. Add logging infrastructure.
8. Add basic README.
9. Initialize Git.
10. Make first commit.

## Expected dependencies

At minimum:

```text
cryptography
fastapi
uvicorn
pytest
```

Only install additional packages when required.

## Logging

Create a structured logger.

Every later module should use the same logging system.

Do not log:

- plaintext
- private keys
- secret values

## Acceptance Criteria

```text
python environment works
dependencies install
pytest runs
application starts
Git repository works
README explains project
```

Commit:

```text
phase-1-project-foundation
```

---

# PHASE 2 — Basic Alice ↔ Bob Networking

## Goal

Create real communication between two endpoints before adding adaptive trust.

Architecture:

```text
Alice Client
     │
     │ TCP connection
     ▼
Bob Server
```

## Implement

- Server startup
- Client connection
- Connection acceptance
- Session identifier
- Basic message transport
- Connection close
- Error handling
- Connection timing

## Important

This phase may temporarily use plaintext only to verify networking.

This plaintext communication is a development step and must NOT become the final security architecture.

## Tests

Test:

- server starts
- client connects
- message travels
- server responds
- disconnect handled correctly

## Acceptance Criteria

Alice and Bob can communicate reliably over a real network/socket connection.

Commit:

```text
phase-2-basic-networking
```

---

# PHASE 3 — Cryptographic Identity and Key Establishment

## Goal

Add proper cryptographic infrastructure.

Do not implement custom cryptography.

## Implement

- Identity key generation
- Public/private key handling
- Key establishment using an established cryptographic mechanism/library
- Session key derivation
- Key identifiers
- Secure key handling

## Important distinction

Separate:

```text
Identity key
```

from:

```text
Session key
```

and from:

```text
Verification fingerprint/authentication value
```

Do not mix these concepts.

## Tests

Test:

- key generation
- public key exchange
- shared secret agreement
- both sides derive equivalent session secret
- incorrect identity does not verify
- secrets are not printed

## Acceptance Criteria

Alice and Bob can establish a cryptographic session without hard-coded secrets.

Commit:

```text
phase-3-cryptographic-foundation
```

---

# PHASE 4 — Encrypted Communication

## Goal

Make the Alice ↔ Bob communication actually encrypted.

Architecture:

```text
Alice
  ↓
Plaintext locally
  ↓
Encryption
  ↓
Ciphertext over network
  ↓
Decryption
  ↓
Bob
```

The trust system must never need the plaintext.

## Implement

- Encryption
- Decryption
- Message framing
- Authentication/integrity
- Secure session handling

## Tests

Verify:

1. Alice encrypts.
2. Network receives ciphertext.
3. Bob decrypts.
4. Tampered ciphertext is rejected.
5. Trust engine has no access to plaintext.

## Acceptance Criteria

End-to-end encrypted communication works.

Commit:

```text
phase-4-encrypted-communication
```

---

# PHASE 5 — Network and Session Metadata Collection

## Goal

Collect observable metadata without inspecting plaintext.

Create:

```text
network/metrics.py
network/session.py
trust/signal_collector.py
```

## Signals

Start with five:

### Signal 1
Handshake latency.

### Signal 2
RTT / RTT variation.

### Signal 3
Session continuity.

### Signal 4
Communication timing.

### Signal 5
Key/session renegotiation frequency.

## Each measurement should have

```text
timestamp
session_id
relationship_id
signal_name
raw_value
normalized_value
source
```

## Important

Do not turn raw measurements directly into trust.

The collector collects.

Normalization and scoring happen later.

## Tests

Use controlled test fixtures to ensure:

- measurements are recorded
- timestamps exist
- session IDs are correct
- plaintext is never accessed
- missing measurements are handled safely

## Acceptance Criteria

A running session produces a stream of metadata signals.

Commit:

```text
phase-5-metadata-collection
```

---

# PHASE 6 — Signal Normalization

## Goal

Convert heterogeneous measurements into comparable scores.

Target:

```text
0 → 100
```

where higher score means better contextual consistency.

## Implement

Separate normalization functions.

Example conceptual structure:

```text
normalize_handshake_latency()
normalize_rtt()
normalize_continuity()
normalize_timing()
normalize_renegotiation()
```

## Important

Do not use arbitrary formulas without documenting them.

For each signal document:

```text
What it measures
Why it matters
Expected normal range
How anomaly affects score
What limitations it has
```

## Example

A high RTT should lower contextual consistency but must NOT be interpreted as proof of an attack.

## Tests

Boundary tests:

```text
normal value
slightly abnormal value
very abnormal value
missing value
```

## Acceptance Criteria

All signals can be converted into stable, explainable normalized scores.

Commit:

```text
phase-6-signal-normalization
```

---

# PHASE 7 — Trust Assessment Engine

## Goal

Implement the core trust score.

## Formula

Start with:

```text
current_score =
    w1*h
  + w2*r
  + w3*c
  + w4*t
  + w5*k
```

Then:

```text
S(t) =
    α × current_score
  + (1 − α) × S(t−1)
```

Where:

```text
S(t) = current trust
S(t−1) = previous trust
α = configurable smoothing parameter
```

## Implement

- weighted signal combination
- configurable weights
- EMA
- initial trust policy
- trust history output

## Important

Weights must be configurable.

Do not hard-code mysterious values.

## Tests

Test:

```text
all normal → high trust
bad signal → trust decreases
multiple anomalies → trust decreases
recovery → trust can recover according to policy
```

## Acceptance Criteria

The system generates a deterministic, explainable trust score from metadata.

Commit:

```text
phase-7-trust-engine
```

---

# PHASE 8 — Implement ΔS

## Goal

Implement independent trust rate-of-change.

Formula:

```text
ΔS = S(t) − S(t−1)
```

## Example

```text
S(t−1) = 91
S(t)   = 83

ΔS = -8
```

## Tests

At minimum:

```text
90 → 88 = -2
90 → 60 = -30
60 → 75 = +15
```

## Critical test

Make sure a sudden drop is detected even if:

```text
S(t) > T2
```

Example:

```text
S(t−1) = 93
S(t) = 71
T2 = 50
δ = 10

S(t) > T2
BUT
ΔS = -22 <= -10

→ trigger condition TRUE
```

This test is mandatory.

Commit:

```text
phase-8-trust-delta
```

---

# PHASE 9 — Relationship Memory Store

## Goal

Persist trust history across sessions.

## Database

Use SQLite.

Implement:

```text
relationships
sessions
trust_history
verification_events
key_events
```

## Relationship identity

Use a stable relationship identifier derived from appropriate public identity information.

Do not use plaintext usernames alone as the security identity if a cryptographic identity identifier is available.

## Store

At minimum:

```text
relationship_id
timestamp
trust_score
delta
verification result
baseline metrics
session information
```

## Tests

Test:

1. Create relationship.
2. Store trust.
3. End session.
4. Start new session.
5. Retrieve historical trust.
6. Confirm history affects subsequent trust state.

## Acceptance Criteria

History survives process restarts.

Commit:

```text
phase-9-relationship-memory
```

---

# PHASE 10 — Verification Trigger Engine

## Goal

Implement the central decision engine.

Inputs:

```text
S(t)
ΔS
T1
T2
δ
relationship state
verification state
```

## Decision logic

```text
IF ΔS <= -δ:
    VERIFY_IMMEDIATELY

ELIF S(t) < T2:
    VERIFY

ELIF S(t) >= T1:
    CONTINUE

ELSE:
    CONTINUE_WITH_MONITORING
```

The sudden negative delta condition must be independent.

## Output

Use explicit decision objects, e.g.:

```text
decision
reason
trust_score
delta
threshold
timestamp
```

Possible decisions:

```text
CONTINUE
MONITOR
VERIFY
VERIFY_IMMEDIATELY
RESTRICT
TERMINATE
```

## Important

The engine must not perform encryption itself.

It decides.

Other modules execute the resulting policy.

## Tests

Mandatory:

```text
High trust + stable → CONTINUE

Nominal trust → MONITOR/CONTINUE

Low trust → VERIFY

High trust + sudden negative ΔS → VERIFY_IMMEDIATELY
```

Commit:

```text
phase-10-trigger-engine
```

---

# PHASE 11 — Out-of-Band Verification Simulation

## Goal

Implement the actual verification workflow.

## UI/CLI flow

Example:

```text
SECURITY VERIFICATION REQUIRED

Reason:
Sudden trust decrease

Trust:
93 → 71

ΔS:
-22

Identity fingerprint:
Alice: ABCD...1234
Bob:   ABCD...1234

[ MATCH ]
[ MISMATCH ]
```

## Important

For the college prototype this can be a controlled simulation of an out-of-band verification mechanism.

Clearly label it as a simulation if it is not actually occurring over a physically separate trusted channel.

## Verification results

```text
SUCCESS
FAILURE
CANCELLED
TIMEOUT
```

## Policy

Success:

```text
continue
update relationship memory
allow key lifecycle action
```

Failure:

```text
restrict/terminate
record event
alert user
do not continue normally
```

## Tests

Test every result.

Commit:

```text
phase-11-verification
```

---

# PHASE 12 — Integrate Trigger + Verification

## Goal

Connect the trust decision to the actual session.

Flow:

```text
Collect metadata
       ↓
Calculate S(t)
       ↓
Calculate ΔS
       ↓
Trigger Engine
       ↓
VERIFY?
   /       \
 NO         YES
 |           |
continue   pause/restrict
             ↓
          verify
          /    \
       PASS    FAIL
        |        |
      continue  terminate
```

## Critical requirement

When verification is required, the system must not silently continue normal communication as if nothing happened.

## Tests

End-to-end tests:

```text
normal session → continues

low trust → verification → pass → continues

low trust → verification → fail → restricted

sudden ΔS → immediate verification
```

Commit:

```text
phase-12-adaptive-verification-integration
```

---

# PHASE 13 — Key Lifecycle Controller

## Goal

Connect trust/verification decisions to controlled key lifecycle actions.

## Implement

Possible actions:

```text
KEEP_CURRENT_KEY
STANDARD_ROTATION
REESTABLISH_KEY
RESTRICT_SESSION
```

## Recommended policy

```text
High trust:
    normal lifecycle

Normal:
    standard rotation

Low trust:
    verification first
    then key re-establishment if verification succeeds

Sudden anomaly:
    verification first
    then key re-establishment if verification succeeds

Verification failure:
    restrict/terminate
```

## Important

Do not implement arbitrary indefinite key lifetime extension because trust is high.

Do not allow key lifecycle logic to bypass identity verification.

## Tests

Test every policy branch.

Commit:

```text
phase-13-key-lifecycle
```

---

# PHASE 14 — Full System Integration

## Goal

Connect every component.

Final flow:

```text
                 Alice/Bob
                    │
                    ▼
            Secure Session
                    │
                    ▼
            Metadata Collector
                    │
                    ▼
            Signal Normalizer
                    │
                    ▼
             Trust Engine
               /       \
             S(t)      ΔS
                \       /
                 ▼     ▼
              Trigger
                 │
          ┌──────┴──────┐
          │             │
       Continue       Verify
          │             │
          │        ┌────┴────┐
          │       PASS      FAIL
          │        │          │
          │        ▼          ▼
          │      Key       Restrict
          │    Lifecycle   /Terminate
          │        │
          └────────┘
                 │
                 ▼
            Session State
                 │
                 ▼
        Relationship Memory
```

## Acceptance Criteria

All components operate together.

No module should contain duplicated business logic.

Commit:

```text
phase-14-full-integration
```

---

# PHASE 15 — Dashboard

## Goal

Build a dashboard that makes the system understandable during demonstration.

## Display

### Session

```text
Alice ↔ Bob
Session ID
Connection state
```

### Trust

```text
Trust score
ΔS
Trust state
```

### Signals

```text
Handshake latency
RTT
Session continuity
Communication timing
Renegotiation frequency
```

### Verification

```text
Last verification
Current verification status
Verification reason
```

### Key lifecycle

```text
Current key identifier
Key lifecycle state
Last key event
```

Never display actual private keys or secret values.

## Graphs

At minimum:

```text
Trust over time
```

and ideally:

```text
Trust score + trigger events
```

## Acceptance Criteria

The dashboard can visibly demonstrate the adaptive behavior.

Commit:

```text
phase-15-dashboard
```

---

# PHASE 16 — Event/Audit Logging

## Goal

Make security decisions traceable.

Example:

```text
SESSION_STARTED
HANDSHAKE_COMPLETED
SIGNAL_UPDATED
TRUST_UPDATED
DELTA_UPDATED
ANOMALY_DETECTED
VERIFICATION_TRIGGERED
VERIFICATION_SUCCESS
VERIFICATION_FAILURE
KEY_REESTABLISHED
SESSION_RESTRICTED
SESSION_TERMINATED
```

Each event should include:

```text
timestamp
session_id
relationship_id
event_type
relevant non-secret metadata
```

Do not include:

```text
plaintext
private keys
session secrets
```

## Acceptance Criteria

A complete demo session can be reconstructed from logs.

Commit:

```text
phase-16-audit-logging
```

---

# PHASE 17 — Controlled Anomaly Simulation

## Goal

Create reproducible experiments.

Create an experiment controller capable of injecting:

```text
latency spike
RTT variance
session continuity change
communication timing anomaly
key renegotiation spike
gradual degradation
sudden trust drop
```

## Important

These are controlled simulations.

Never describe them as real attacks.

## Experiment configuration

Example:

```text
scenario:
sudden_drop

baseline:
normal

anomaly:
latency × 5
continuity change
renegotiation spike

expected:
verification
```

## Acceptance Criteria

Every scenario can be run repeatedly with reproducible settings.

Commit:

```text
phase-17-experiment-framework
```

---

# PHASE 18 — Experiment 1: Normal Communication

## Scenario

```text
Stable device
Stable network
Normal timing
Normal handshake
Normal key behavior
```

## Expected

```text
Trust remains high
No unnecessary verification
Normal key lifecycle
```

## Record

```text
number of sessions
average trust
minimum trust
verification count
key events
```

Save raw experiment data.

---

# PHASE 19 — Experiment 2: Gradual Degradation

## Scenario

Introduce increasingly abnormal conditions.

Example conceptual sequence:

```text
Session 1 → normal
Session 2 → mild anomaly
Session 3 → mild anomaly
Session 4 → moderate anomaly
Session 5 → low trust
```

## Expected

Trust gradually decreases.

Eventually:

```text
S(t) < T2
→ VERIFY
```

Record:

```text
trust trajectory
verification point
number of sessions before verification
```

---

# PHASE 20 — Experiment 3: Sudden Trust Drop

## Goal

Demonstrate the most important property of the project.

Start:

```text
S = 92
```

Introduce a controlled anomaly.

Example:

```text
S = 68
ΔS = -24
```

Even if:

```text
T2 = 50
```

the absolute score is still above the low-trust threshold.

But:

```text
ΔS <= -δ
```

must trigger:

```text
VERIFY_IMMEDIATELY
```

This experiment must be clearly visible on the dashboard.

---

# PHASE 21 — Experiment 4: New Relationship

## Scenario

Create:

```text
Alice ↔ Charlie
```

with no relationship history.

Expected:

```text
conservative initial trust
earlier verification
```

Then verify and run normal sessions.

Show how relationship history evolves.

---

# PHASE 22 — Experiment 5: Established Relationship

## Scenario

Use:

```text
Alice ↔ Bob
```

after multiple successful normal sessions.

Expected:

```text
stable/higher baseline
fewer unnecessary verification events
```

Do not manipulate the results to achieve the expected outcome.

If the implementation does not produce this behavior, investigate the model rather than fabricating results.

---

# PHASE 23 — Experiment 6: Verification Failure

## Scenario

Trigger verification.

Return:

```text
MISMATCH
```

Expected:

```text
verification failure
session restricted/terminated
security event logged
normal communication does not continue
```

Then repeat with:

```text
MATCH
```

Expected:

```text
verification success
key lifecycle action
session restored/continued
```

---

# PHASE 24 — Quantitative Evaluation

## Metrics

Implement measurement for:

### 1. Verification frequency

```text
verification events / sessions
```

### 2. False verification rate

For controlled normal sessions:

```text
unnecessary verification /
normal sessions
```

### 3. Trigger latency

Measure:

```text
anomaly injection timestamp
        ↓
verification trigger timestamp
```

### 4. Anomaly detection rate

For controlled experiments:

```text
detected injected anomalies /
total injected anomalies
```

Be precise with terminology.

Do not call this "real-world attack detection accuracy."

### 5. Trust recovery

After successful verification and normal behavior:

```text
trust before anomaly
trust after anomaly
trust after recovery
```

### 6. Verification overhead

Measure:

```text
number of verification events
verification processing time
additional key establishment events
```

---

# PHASE 25 — Threshold and Sensitivity Analysis

## Goal

Demonstrate that results are not based on one arbitrary threshold.

Test multiple:

```text
T1
T2
δ
α
weights
```

Observe effects on:

```text
verification frequency
false verification rate
trigger latency
anomaly detection rate
```

Create graphs/tables.

## Important

Do not select thresholds after seeing results simply to make the system look better.

Document the selection methodology.

---

# PHASE 26 — Robustness Testing

Test edge cases.

## Cases

```text
Missing signal
Delayed signal
Extreme RTT
Network disconnect
Repeated reconnect
Duplicate events
Out-of-order events
Database unavailable
Verification timeout
Verification cancellation
Malformed network data
Invalid cryptographic input
```

The system should fail safely.

Examples:

```text
verification uncertainty
→ do not silently treat as verified
```

```text
cryptographic failure
→ reject/restrict
```

---

# PHASE 27 — Security Review

Before finalizing, inspect the entire project for:

## Cryptography

- established algorithms
- secure random generation
- proper key handling
- no hard-coded secrets
- no secret leakage

## Networking

- authentication
- message integrity
- secure session handling
- malformed input handling
- timeouts

## Trust engine

- no plaintext dependency
- explainable scoring
- configurable parameters
- clear distinction between anomaly and attack

## Verification

- failure is fail-safe
- no bypass
- verification state cannot be spoofed through ordinary metadata

## Storage

- no plaintext messages
- no private keys
- no session secrets
- appropriate database constraints

## Dashboard

- no secrets
- no private key display
- no sensitive debug information

---

# PHASE 28 — Code Quality Refactor

Only after the system works.

Clean:

- duplicate code
- unused imports
- dead code
- oversized functions
- unclear variable names
- hidden global state
- hard-coded configuration
- unnecessary dependencies

Add:

- type hints
- docstrings for important functions
- clear module boundaries
- error handling
- comments only where they explain non-obvious logic

Do not refactor the architecture into unnecessary abstractions.

Commit:

```text
phase-28-code-quality
```

---

# PHASE 29 — Documentation

Create:

```text
README.md
docs/architecture.md
docs/algorithms.md
docs/experiments.md
```

README should include:

```text
Project overview
Architecture
Technology stack
Installation
How to run Alice
How to run Bob
How to start dashboard
How to run experiments
Testing
Limitations
Security disclaimer
```

Algorithms document:

```text
Signal normalization
Trust score
EMA
ΔS
Trigger logic
Verification flow
Key lifecycle policy
```

Experiments document:

```text
Scenario
Setup
Variables
Expected behavior
Measured results
Limitations
```

---

# PHASE 30 — Reproducibility Check

A fresh machine/environment should be able to:

```text
clone repository
install dependencies
initialize database
start server
start client
run tests
run experiments
open dashboard
```

Do this from a clean environment.

Do not assume your development machine's hidden configuration exists.

---

# PHASE 31 — Final End-to-End Demo

The final demonstration should follow this sequence.

## Demo 1 — New relationship

```text
Alice ↔ Bob

No history

Trust: conservative
Verification required
```

## Demo 2 — Successful verification

```text
Fingerprint MATCH

Verification successful
Session continues
```

## Demo 3 — Relationship learning

Run normal sessions:

```text
82
87
91
93
```

Show relationship history.

## Demo 4 — Sudden anomaly

Inject:

```text
RTT spike
+
continuity change
+
renegotiation spike
```

Show:

```text
93 → 71
ΔS = -22
```

Then:

```text
VERIFY_IMMEDIATELY
```

## Demo 5 — Failed verification

```text
MISMATCH
↓
SESSION RESTRICTED
```

## Demo 6 — Successful recovery

Repeat anomaly.

```text
MATCH
↓
Verification successful
↓
Key re-establishment
↓
Session restored
```

This should be the main final demonstration.

---

# 32. Final Deliverables Checklist

Before declaring the project complete:

## Software

- [ ] Alice client
- [ ] Bob server/client
- [ ] Secure communication
- [ ] Cryptographic key establishment
- [ ] Encryption/decryption
- [ ] Metadata collection
- [ ] Signal normalization
- [ ] Trust engine
- [ ] ΔS
- [ ] Relationship memory
- [ ] Trigger engine
- [ ] Verification
- [ ] Key lifecycle
- [ ] Dashboard
- [ ] Audit logging
- [ ] Experiment framework

## Testing

- [ ] Unit tests
- [ ] Integration tests
- [ ] Security tests
- [ ] Edge-case tests
- [ ] Six experiment scenarios
- [ ] Quantitative evaluation
- [ ] Threshold sensitivity analysis

## Documentation

- [ ] README
- [ ] Architecture diagram
- [ ] Network diagram
- [ ] Trust algorithm
- [ ] State machine
- [ ] Database schema
- [ ] Experiment methodology
- [ ] Results
- [ ] Limitations
- [ ] References

## Presentation

- [ ] Problem
- [ ] Existing limitations
- [ ] Proposed architecture
- [ ] Core novelty
- [ ] Live demo
- [ ] Experimental results
- [ ] Security discussion
- [ ] Limitations
- [ ] Future scope

---

# 33. Things the Coding AI Must Never Do

These are explicit red flags.

## Never generate:

```python
encrypted = plaintext[::-1]
```

and call it encryption.

Never use:

```python
hash(message)
```

as encryption.

Never do:

```python
if "attack" in message:
    trust -= 20
```

Never do:

```python
trust = random.randint(0, 100)
```

in Real Network Mode.

Never do:

```python
if rtt > 100:
    attack_detected = True
```

unless the system explicitly describes this as a controlled anomaly rule rather than proof of an attack.

Never do:

```python
PRIVATE_KEY = "..."
```

Never print:

```text
private key
session secret
plaintext
```

Never create an ML model simply because the project title contains "adaptive."

Never add blockchain just to impress an evaluator.

Never fabricate experiment output.

Never write:

> "MITM attack detected"

when the system only observed an anomaly.

Prefer:

> "Contextual anomaly detected; identity verification triggered."

---

# 34. AI Coding Workflow

Use this exact workflow with Codex/Claude.

## Step 1

Give the AI:

```text
Project blueprint
+
this coding plan
```

## Step 2

Tell it:

```text
We are currently implementing PHASE X only.
Do not implement future phases.
```

## Step 3

Ask it to:

```text
1. Inspect existing repository.
2. Explain what currently exists.
3. Identify files to create/change.
4. Implement only this phase.
5. Write tests.
6. Run tests.
7. Report failures.
8. Do not fabricate successful results.
```

## Step 4

Review the implementation.

## Step 5

Only then move to:

```text
PHASE X+1
```

---

# 35. Recommended Prompt Template for Every Phase

Use this structure:

```text
We are building the project defined in the attached
Adaptive Trust project blueprint and phase-by-phase coding plan.

Current phase:
PHASE X — [PHASE NAME]

Rules:
- Implement ONLY this phase.
- Do not implement future phases.
- Do not change the core architecture without explaining why.
- Do not invent cryptography.
- Do not use plaintext for trust scoring.
- Do not fabricate results.
- Use established libraries.
- Write tests for the implementation.
- Keep secrets out of source code and logs.
- Keep the implementation modular.
- Prefer simple implementations over unnecessary abstractions.

Before coding:
1. Inspect the current repository.
2. Summarize the existing implementation.
3. Identify exactly what needs to be added/changed.
4. State any assumptions.

Then:
1. Implement the phase.
2. Add/update tests.
3. Run the tests.
4. Fix genuine failures.
5. Show the final files changed.
6. Explain how the implementation satisfies this phase.
7. Report any remaining limitations honestly.

Do not proceed to the next phase.
```

---

# 36. Stop Conditions

Stop coding and ask for clarification if:

- a requirement is ambiguous
- a cryptographic design choice is unsafe
- an established library does not support the planned operation
- the architecture must change
- a security assumption is invalid
- an experiment cannot measure what it claims to measure
- the implementation would require inspecting plaintext
- the AI is tempted to fabricate a result
- a future phase is required to complete the current phase

Do not guess silently.

---

# 37. Definition of Done

The project is complete only when:

```text
Real secure communication works
        +
Metadata is collected without plaintext inspection
        +
Trust score is explainable
        +
ΔS works independently
        +
Relationship memory persists
        +
Verification is automatically triggered
        +
Verification failure is handled safely
        +
Key lifecycle reacts appropriately
        +
Dashboard demonstrates behavior
        +
Experiments are reproducible
        +
Results are measured
        +
Tests pass
        +
Security review is complete
        +
Documentation is complete
```

The most important demonstration remains:

```text
High trust
   ↓
Sudden contextual anomaly
   ↓
Sharp negative ΔS
   ↓
Immediate verification
   ↓
PASS → controlled key lifecycle action → continue
FAIL → restrict/terminate
```

That is the behavior the implementation should make unmistakably visible.
