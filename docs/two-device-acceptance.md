# Phase 13: physical two-laptop acceptance record

Status: **NOT RUN**. Local automated TLS checks do not satisfy this gate.
Use two Windows laptops on the same private Wi-Fi. Follow
[operation instructions](two-device-operation.md) for setup and trusted USB transfer.
Complete both columns from clean application starts. Do not record passwords,
private keys, safety-code screenshots containing conversations, or chat bodies here.

| Physical check | Run 1 | Run 2 |
|---|---|---|
| Date, Windows/Python versions on both laptops | Pending | Pending |
| Trusted provisioning; only Bob's bundle transferred by USB | Pending | Pending |
| Both applications restarted; conversation initially empty | Pending | Pending |
| Bob starts listener; record private Wi-Fi IPv4 and TLS port | Pending | Pending |
| Alice connects using that IPv4; TLS 1.3 shown | Pending | Pending |
| Both humans compare entire code and select MATCH | Pending | Pending |
| Simultaneous bidirectional messages delivered | Pending | Pending |
| Alice alone shows live RTT, timing, TLS and trust | Pending | Pending |
| Normal observations stabilize; induce latency; real RTT increases | Pending | Pending |
| Sharp-drop verification appears; both send boxes disabled | Pending | Pending |
| Restore normal using Alice's modal button; both select MATCH | Pending | Pending |
| Public key-epoch ID changes; relationship ID stays unchanged | Pending | Pending |
| Existing conversation remains visible; new messages delivered | Pending | Pending |
| Allow trust to stabilize; induce latency again | Pending | Pending |
| Verification appears; select MISMATCH on one laptop | Pending | Pending |
| Both sessions close; further sending is blocked | Pending | Pending |
| Alice audit timeline contains metadata only; no chat bodies | Pending | Pending |
| Local services exit cleanly | Pending | Pending |

Record only public session/epoch IDs and pass/fail observations if useful. For any
failure, record the step, sanitized symptom, and which endpoint observed it. Fix
the underlying issue and repeat the entire failed run from clean starts. Do not
mark a run passed merely because retrying an individual step worked.

Phase 13 passes only after both physical runs pass. At the user's explicit request,
Phase 14 documentation proceeds first; this physical gate remains at the end and
must pass before the overall two-device feature is declared fully accepted.
