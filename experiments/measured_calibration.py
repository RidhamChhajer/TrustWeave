"""Small measured loopback pilot; never installs a policy or claims attack accuracy."""
import asyncio
from dataclasses import asdict, replace
import json
from pathlib import Path
import secrets
import ssl
import sys
import tempfile
from time import perf_counter

from config.settings import Settings
from crypto.identity import provision
from network.connection import PeerClosed
from network.secure import SecureServer, connect
from network.snapshot import raw_snapshot
from trust.normalization import Baselines, normalize_snapshot
from trust.trust_engine import TrustEngine, TrustPolicy
from verification.trigger_engine import decide


def evaluate(sessions, policy):
    """Stop each replay at its first prompt, matching the live verification gate."""
    false_prompts = detected = 0
    normal = sum(not session["induced"] for session in sessions)
    for session in sessions:
        engine = TrustEngine(policy, initial=policy.verified_floor)
        for row in session["rows"]:
            assessment = engine.assess(normalize_snapshot(row["raw"],
                                      Baselines(timing_ms=50, peer_ip="127.0.0.1")))
            if decide(assessment.score, assessment.delta, verified=True).requires_verification:
                if row["induced"]:
                    detected += 1
                else:
                    false_prompts += 1
                break
    return {"sessions": len(sessions), "normal_sessions": normal,
            "induced_sessions": len(sessions) - normal,
            "sessions_with_false_prompt": false_prompts,
            "sessions_detecting_induced_delay": detected}


async def collect():
    sessions = []
    with tempfile.TemporaryDirectory(prefix="trust-measured-") as directory:
        passwords = {role: secrets.token_urlsafe(32).encode() for role in ("ca", "alice", "bob")}
        credentials = provision(Path(directory) / "identities", passwords)
        for split in ("training", "held_out"):
            for repetition in range(2):
                for induced in (False, True):
                    async def echo(connection):
                        try:
                            for tick in range(20):
                                payload = await connection.receive()
                                if induced and tick >= 15:
                                    await asyncio.sleep(0.25)
                                await connection.send(payload)
                        except PeerClosed:
                            pass
                    rows = []
                    async with await SecureServer.start(Settings(port=0), credentials["bob"],
                                                        lambda: passwords["bob"], echo) as server:
                        connection = await connect(Settings(port=server.port), credentials["alice"],
                                                   lambda: passwords["alice"])
                        previous = None
                        try:
                            for tick in range(20):
                                await asyncio.sleep(0.05)
                                started = perf_counter()
                                await connection.send(b"calibration heartbeat")
                                if await connection.receive() != b"calibration heartbeat":
                                    raise RuntimeError("TLS echo failed")
                                completed = perf_counter()
                                connection.metrics.record_round_trip((completed - started) * 1000,
                                                                     source="authenticated_heartbeat")
                                raw = raw_snapshot(connection)
                                raw["timing_ms"] = None if previous is None else (completed - previous) * 1000
                                previous = completed
                                rows.append({"raw": raw, "induced": induced and tick >= 15})
                        finally:
                            await connection.close()
                    sessions.append({"split": split, "repetition": repetition,
                                     "induced": induced, "rows": rows})
    return sessions


async def main():
    sessions = await collect()
    policies = {"default": TrustPolicy(), "slower_ema": replace(TrustPolicy(), alpha=0.15),
                "faster_ema": replace(TrustPolicy(), alpha=0.5)}
    training = {name: evaluate([s for s in sessions if s["split"] == "training"], policy)
                for name, policy in policies.items()}
    # Candidate list and ranking are fixed before looking at held-out sessions.
    selected = min(policies, key=lambda name: (training[name]["sessions_with_false_prompt"],
                   -training[name]["sessions_detecting_induced_delay"], name != "default"))
    report = {"runtime": sys.version.split()[0], "openssl": ssl.OPENSSL_VERSION,
              "scope": "8 independent loopback TLS sessions; real 250ms delay; offline verified-state replay",
              "limitations": "One machine, short sessions, no attack dataset or human verification. Weights remain uncalibrated. No live policy change.",
              "policies": {name: asdict(policy) for name, policy in policies.items()},
              "training": training, "selected_on_training": selected,
              "held_out": evaluate([s for s in sessions if s["split"] == "held_out"], policies[selected]),
              "sessions": sessions}
    target = Path("artifacts/measured-calibration.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "sessions"}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
