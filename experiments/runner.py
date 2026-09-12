"""Real loopback TLS with reproducible simulated metadata and OOB decisions."""

import asyncio
from dataclasses import asdict, replace
from contextlib import AsyncExitStack
import json
from pathlib import Path
import secrets
import tempfile
from time import perf_counter_ns

from client.bob import echo
from config.settings import Settings
from crypto.identity import provision, fingerprint
from cryptography import x509
from network.secure import SecureServer, connect
from storage.relationship_store import RelationshipStore
from trust.trust_engine import TrustPolicy
from verification.session_guard import SessionGuard
from verification.trigger_engine import TriggerPolicy
from verification.verification import Outcome


async def run_trace(trace, *, trust_policy=TrustPolicy(), trigger_policy=TriggerPolicy()):
    """Trace entries: kind, raw, anomaly, optional outcome/new_session. No score overrides."""
    rows = []
    trace = list(trace)
    peers = tuple(dict.fromkeys(["bob"] + [entry.get("peer", "bob") for entry in trace]))
    with tempfile.TemporaryDirectory(prefix="trust-experiment-") as temporary:
        passwords = {role: secrets.token_urlsafe(32).encode() for role in ("ca", "alice", *peers)}
        credentials = provision(Path(temporary) / "identities", passwords, server_names=peers)
        with RelationshipStore(Path(temporary) / "history.db") as store:
            async with AsyncExitStack() as stack:
                servers, clients = {}, {}
                for peer in peers:
                    servers[peer] = await stack.enter_async_context(await SecureServer.start(
                        Settings(port=0), credentials[peer], lambda peer=peer: passwords[peer], echo))
                    clients[peer] = replace(credentials["alice"], expected_peer_pin=fingerprint(
                        x509.load_pem_x509_certificate(credentials[peer].certificate.read_bytes())))
                active_peer = "bob"
                async def reconnect():
                    return await connect(Settings(port=servers[active_peer].port), clients[active_peer], lambda: passwords["alice"])
                entry = {}
                trigger_ns = None
                async def response(request):
                    nonlocal trigger_ns
                    trigger_ns = perf_counter_ns()
                    return Outcome(entry.get("outcome", "SUCCESS"))
                def wrap(connection):
                    return SessionGuard(connection, store, response, reconnect=reconnect, mode="simulated",
                                        trust_policy=trust_policy, trigger_policy=trigger_policy)
                guard = wrap(await reconnect())
                try:
                    for tick, entry in enumerate(trace):
                        requested_peer = entry.get("peer", "bob")
                        if entry.get("new_session") or requested_peer != active_peer:
                            await guard.close()
                            active_peer = requested_peer
                            guard = wrap(await reconnect())
                        if guard.restricted:
                            break
                        sid = guard.context.session_id
                        relationship_id = guard.context.relationship_id
                        before = guard.engine.score
                        trigger_ns = None
                        injection_ns = perf_counter_ns()
                        decision = await guard.assess(entry["raw"])
                        assessed_ns = perf_counter_ns()
                        delivered = False
                        if not guard.restricted:
                            payload = secrets.token_bytes(32)
                            await guard.connection.send(payload)
                            delivered = await guard.connection.receive() == payload
                            if not delivered:
                                raise RuntimeError("encrypted exchange failed")
                        rows.append(dict(tick=tick, kind=entry["kind"], anomaly=entry["anomaly"],
                                         peer=active_peer, relationship_id=relationship_id,
                                         raw=entry["raw"], session_id=sid, resulting_session_id=guard.context.session_id,
                                         before=before, score=decision.score, after=guard.engine.score,
                                         delta=decision.delta, action=decision.action, reason=decision.reason,
                                         outcome=guard.last_outcome.value if decision.requires_verification else None,
                                         restricted=guard.restricted, delivered=delivered,
                                         key_action=guard.last_key_action if not guard.restricted else "RESTRICT_SESSION",
                                         injection_ns=injection_ns, trigger_ns=trigger_ns,
                                         assessment_ms=(assessed_ns-injection_ns)/1e6,
                                         verification_ms=None if trigger_ns is None else (assessed_ns-trigger_ns)/1e6))
                finally:
                    await guard.close()
                audit = [dict(row) for row in store.db.execute("SELECT * FROM audit_events ORDER BY id")]
    return dict(simulated_metadata=True, simulated_oob=True, transport="mutual TLS 1.3",
                policies=dict(trust=asdict(trust_policy), trigger=asdict(trigger_policy)), rows=rows, audit=audit)


def save(result, path):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")


def execute(trace, path):
    result = asyncio.run(run_trace(trace))
    save(result, path)
    rows = result["rows"]
    print(json.dumps(dict(samples=len(rows), verifications=sum(r["trigger_ns"] is not None for r in rows),
                          minimum_trust=min(r["score"] for r in rows), final_trust=rows[-1]["after"])))
    return result
