# Architecture and network boundaries

```
Alice application <== framed bytes inside mutual TLS 1.3 ==> Bob echo application
       |                                                   |
       +--> timing/identity/IP/count metadata <-------------+
                 |
           normalization -> weighted EMA + delta
                 |                 |
          SQLite relationship <-> trigger decision
                                   |
                          SessionGuard (Alice-side)
                          /                     \
               continue/monitor            gate communication
                                                 |
                                      simulated OOB comparison
                                      /                     \
                                   MATCH                  uncertainty
                              fresh pinned TLS             close/restrict
```

TLS terminates at Alice and Bob only. The test relay observes ciphertext without TLS
termination. Long-term P-256 identity keys authenticate certificates; SHA-256 SPKI pins
select the expected peer; OpenSSL manages ephemeral agreement and directional traffic keys.
The public session epoch ID is not a key. Both frame length and message are inside TLS.

## Components

| Directory | Responsibility |
|---|---|
| config | Transport defaults and validated configuration |
| crypto | Encrypted-key development PKI, TLS context and pin checks |
| network | Secure connection/server, framing, raw measurements and snapshot |
| trust | Metadata boundary, normalization, EMA, independent delta |
| verification | Trigger policy, simulated comparison, gated session coordinator |
| lifecycle | Keep/rotate/re-establish/restrict decisions |
| storage | SQLite relationships, histories and ordered typed audit |
| dashboard | Loopback UI, manual simulated answers and isolated controlled experiment |
| experiments | Deterministic synthetic inputs over real TLS, raw results and metrics |

Relationship ID hashes a domain prefix and sorted public identity fingerprints, so it is
symmetric and independent of source ports. Charlie has a separate certificate/key but
shares Alice and the development CA; his relationship cannot inherit Bob's trust.

## Database schema

`relationships(id, trust, verified, successes, failures, last_verified, baselines)` owns
`sessions(id, relationship_id, started, ended, mode, status)`. Session foreign keys link
`trust_history(score, delta, reason)`, `verification_events(outcome, simulated)` and
`key_events(action, key_id)`. `audit_events(id, timestamp, session_id, relationship_id,
event_type, metadata)` provides ordered reconstruction. IDs/timestamps omitted in this
short schema description remain in actual tables. WAL/foreign keys are enabled.

No message bodies, passwords or private/traffic keys belong in these tables. Stores are
local and not tamper-evident. See security-review.md for boundaries and limitations.
