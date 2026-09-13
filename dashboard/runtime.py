import asyncio
from collections import deque
from dataclasses import replace
from dashboard.presentation import guard_snapshot
from pathlib import Path
import secrets
import tempfile
from time import perf_counter

from client.bob import echo
from config.settings import Settings
from crypto.identity import provision
from network.secure import SecureServer, connect
from network.snapshot import raw_snapshot
from storage.relationship_store import RelationshipStore, timestamp
from trust.signal_collector import ContextSignalCollector
from verification.session_guard import SessionGuard
from verification.verification import Outcome


class Runtime:
    def __init__(self, database=".state/dashboard.db"):
        self.database = database
        self.guard = None
        self.task = None
        self.answer = None
        self.history = deque(maxlen=300)
        self.error = None

    async def start(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="adaptive-dashboard-")
        self.passwords = {role: secrets.token_urlsafe(32).encode() for role in ("ca", "alice", "bob")}
        self.identities = provision(Path(self.temporary.name) / "identities", self.passwords)
        self.store = RelationshipStore(self.database)
        self.collector = ContextSignalCollector()
        self.server = await SecureServer.start(Settings(port=0), self.identities["bob"], lambda: self.passwords["bob"], echo)

    async def reconnect(self):
        return await connect(Settings(port=self.server.port), self.identities["alice"],
                             lambda: self.passwords["alice"], collector=self.collector)

    async def respond(self, request):
        self.answer = asyncio.get_running_loop().create_future()
        try:
            return await self.answer
        finally:
            self.answer = None

    def resolve(self, request_id, outcome):
        if not self.guard or not self.guard.pending or self.guard.pending.id != request_id or self.answer is None or self.answer.done():
            raise ValueError("verification request is no longer pending")
        self.answer.set_result(Outcome(outcome))

    async def begin(self):
        if self.task is not None and not self.task.done():
            raise ValueError("a session is already running")
        self.error = None
        self.guard = SessionGuard(await self.reconnect(), self.store, self.respond, reconnect=self.reconnect)
        # The live demonstration deliberately assesses on a 500-ms cadence.
        self.guard.baselines = replace(self.guard.baselines, timing_ms=500)
        self.task = asyncio.create_task(self.communicate())

    async def communicate(self):
        try:
            await self.guard.assess(raw_snapshot(self.guard.connection))
            while not self.guard.restricted:
                payload = secrets.token_bytes(32)
                start = perf_counter()
                await self.guard.connection.send(payload)
                if await self.guard.connection.receive() != payload:
                    raise RuntimeError("exchange failed")
                self.guard.connection.metrics.record_round_trip((perf_counter() - start) * 1000)
                await self.guard.assess(raw_snapshot(self.guard.connection))
                self.history.append({"timestamp": timestamp(), "score": self.guard.engine.score,
                                     "delta": self.guard.last_assessment.delta,
                                     "triggered": self.guard.last_decision.requires_verification})
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            raise
        except Exception:
            self.error = "Session stopped safely after a transport or storage error."
            await self.guard.restrict()
        finally:
            await self.guard.close()

    async def stop(self):
        if self.task is not None:
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)

    async def close(self):
        await self.stop()
        await self.server.close()
        self.store.close()
        self.temporary.cleanup()

    def snapshot(self):
        guard = self.guard
        return {"running": self.task is not None and not self.task.done(), "mode": "real",
                "verification_simulated": True, "error": self.error, "history": list(self.history),
                **guard_snapshot(guard)}
