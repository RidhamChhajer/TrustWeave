"""Fail-closed bridge between contextual assessment, verification, and transport."""

import asyncio
from dataclasses import replace
import json

from trust.normalization import Baselines, NormalizationPolicy, normalize_snapshot
from trust.trust_engine import Assessment, TrustEngine, TrustPolicy
from verification.trigger_engine import TriggerPolicy, decide
from verification.verification import Outcome, VerificationRequest, verify


class SessionGuard:
    def __init__(self, connection, store, responder, *, mode="real", trust_policy=TrustPolicy(),
                 trigger_policy=TriggerPolicy(), normalization_policy=NormalizationPolicy(), timeout=30):
        self.connection = connection
        self.store = store
        self.responder = responder
        self.mode = mode
        self.trigger_policy = trigger_policy
        self.normalization_policy = normalization_policy
        self.timeout = timeout
        self.context = connection.metrics.session
        row = store.start_session(self.context.session_id, self.context.relationship_id, mode, trust_policy.initial_trust)
        self.engine = TrustEngine(trust_policy, row["trust"])
        self.baselines = Baselines(**json.loads(row["baselines"]))
        self.verified = bool(row["verified"])
        self.restricted = False
        self.pending = None
        self.last_decision = None
        self.last_outcome = None
        self.last_assessment = None
        self.last_raw = {}
        self._lock = asyncio.Lock()
        connection.require_verification(not self.verified)

    async def assess(self, raw):
        async with self._lock:
            if self.restricted:
                return decide(self.engine.score, 0, verified=False, restricted=True)
            try:
                self.last_raw = dict(raw)
                assessment = self.engine.assess(normalize_snapshot(raw, self.baselines, self.normalization_policy))
                self.last_assessment = assessment
                self.store.assessment(self.context.session_id, assessment)
                decision = decide(assessment.score, assessment.delta, verified=self.verified, policy=self.trigger_policy)
                self.last_decision = decision
                if decision.requires_verification:
                    self.connection.require_verification(True)
                    request = VerificationRequest.create(self.context.session_id, self.context.relationship_id, decision.reason)
                    self.pending = request
                    outcome = await verify(request, self.responder, self.timeout)
                    self.store.verification(request, outcome.value)
                    self.last_outcome = outcome
                    self.pending = None
                    if outcome != Outcome.SUCCESS:
                        await self.restrict()
                        return decision
                    self.verified = True
                    previous = self.engine.score
                    self.engine.score = max(previous, 75.0)
                    self.store.assessment(self.context.session_id, Assessment(previous, self.engine.score, self.engine.score), "verification_success")
                    self.baselines = replace(self.baselines, peer_ip=self.context.peer_ip)
                    self.store.set_baselines(self.context.relationship_id, self.baselines)
                    self.connection.require_verification(False)
                return decision
            except BaseException:
                await self.restrict()
                raise

    async def restrict(self):
        self.restricted = True
        self.verified = False
        self.pending = None
        self.connection.require_verification(True)
        try:
            self.store.finish_session(self.context.session_id, "RESTRICTED")
        finally:
            await self.connection.close()
