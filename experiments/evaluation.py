"""Metrics with explicit observation, TLS-session and anomaly-episode denominators."""
import asyncio
import json
from statistics import mean

from experiments import normal, gradual, sudden, new_relationship, established, failure
from experiments.runner import run_trace, save

SCENARIOS = dict(normal=normal.trace, gradual=gradual.trace, sudden=sudden.trace,
                 new_relationship=new_relationship.trace, established=established.trace, failure=failure.trace)


def summarize(result):
    rows = result["rows"]
    triggered = [r for r in rows if r["trigger_ns"] is not None]
    sessions = {r["session_id"] for r in result["audit"] if r["event_type"] == "SESSION_STARTED"}
    # Session-level false-trigger denominator excludes any session with anomalous observations.
    anomalous_sessions = {r["session_id"] for r in rows if r["anomaly"]}
    normal_sessions = {r["session_id"] for r in rows if not r["anomaly"]} - anomalous_sessions
    unnecessary = [r for r in triggered if r["session_id"] in normal_sessions and r["reason"] != "new_relationship"]
    episodes = []
    for row in rows:
        if row["anomaly"]:
            if not episodes or episodes[-1][-1]["tick"] != row["tick"] - 1:
                episodes.append([])
            episodes[-1].append(row)
    detections = [next((r for r in episode if r["trigger_ns"] is not None), None) for episode in episodes]
    latencies = [(detected["trigger_ns"] - episode[0]["injection_ns"]) / 1e6
                 for episode, detected in zip(episodes, detections) if detected is not None]
    recovery = []
    for episode in episodes:
        later = [r for r in rows if r["tick"] > episode[-1]["tick"] and not r["anomaly"]]
        recovery.append(dict(before=episode[0]["before"], after_anomaly=episode[-1]["score"],
                             after_recovery=later[-1]["after"] if later else None))
    return dict(observations=len(rows), tls_sessions=len(sessions),
                average_trust=mean(r["score"] for r in rows), minimum_trust=min(r["score"] for r in rows),
                verifications=len(triggered), verifications_per_tls_session=len(triggered)/len(sessions),
                normal_observed_sessions=len(normal_sessions), unnecessary_verifications=len(unnecessary),
                false_verifications_per_normal_session=len(unnecessary)/len(normal_sessions) if normal_sessions else None,
                injected_episodes=len(episodes), detected_episodes=sum(d is not None for d in detections),
                controlled_episode_detection_rate=sum(d is not None for d in detections)/len(episodes) if episodes else None,
                episode_trigger_latency_ms=latencies,
                episode_trigger_delay_observations=[d["tick"]-e[0]["tick"] if d else None for e,d in zip(episodes,detections)],
                verification_and_rekey_ms=sum(r["verification_ms"] for r in triggered),
                additional_key_establishments=sum(r["key_action"] in {"REESTABLISH_KEY", "STANDARD_ROTATION"} for r in rows),
                recovery=recovery)


async def evaluate():
    summaries = {}
    for name, trace in SCENARIOS.items():
        result = await run_trace(trace())
        save(result, f"artifacts/evaluation/{name}.json")
        summaries[name] = summarize(result)
    save(summaries, "artifacts/evaluation/summary.json")
    print(json.dumps(summaries, indent=2))
    return summaries


if __name__ == "__main__":
    asyncio.run(evaluate())
