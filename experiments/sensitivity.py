"""Predeclared one-factor-at-a-time sensitivity sweep; no automatic policy tuning."""
import asyncio
import csv
from dataclasses import replace
from pathlib import Path

from experiments.evaluation import summarize, SCENARIOS
from experiments.runner import run_trace, save
from trust.trust_engine import TrustPolicy
from verification.trigger_engine import TriggerPolicy


def variants():
    trust, trigger = TrustPolicy(), TriggerPolicy()
    yield "default", trust, trigger
    for alpha in (.15, .5):
        yield f"alpha_{alpha}", replace(trust, alpha=alpha), trigger
    for high in (70, 90):
        yield f"high_{high}", trust, replace(trigger, high=high)
    for low in (40, 60):
        yield f"low_{low}", trust, replace(trigger, low=low)
    for drop in (5, 20):
        yield f"drop_{drop}", trust, replace(trigger, sudden_drop=drop)
    for name, weights in (("continuity_heavy", (.15,.15,.4,.15,.15)),
                          ("latency_heavy", (.3,.3,.1,.15,.15))):
        yield name, replace(trust, weights=weights), trigger


async def run():
    rows = []
    for name, trust, trigger in variants():
        for scenario in ("normal", "gradual", "sudden"):
            result = await run_trace(SCENARIOS[scenario](), trust_policy=trust, trigger_policy=trigger)
            save(result, f"artifacts/sensitivity/{name}-{scenario}.json")
            metrics = summarize(result)
            rows.append(dict(variant=name, scenario=scenario, verifications=metrics["verifications"],
                             frequency=metrics["verifications_per_tls_session"],
                             false_rate=metrics["false_verifications_per_normal_session"],
                             detection=metrics["controlled_episode_detection_rate"],
                             delay_observations=metrics["episode_trigger_delay_observations"],
                             latency_ms=metrics["episode_trigger_latency_ms"]))
    target = Path("artifacts/sensitivity/table.csv")
    with target.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    save(rows, "artifacts/sensitivity/summary.json")
    print(f"SENSITIVITY_COMPLETE: {len(rows)} runs; table={target}")
    for row in rows:
        if row["scenario"] != "normal":
            print(f"{row['variant']} {row['scenario']}: requests={row['verifications']}, detected={row['detection']}, observation_delay={row['delay_observations']}")


if __name__ == "__main__":
    asyncio.run(run())
