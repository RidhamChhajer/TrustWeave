"""Integrated live TLS demo; human verification is explicitly simulated."""

import asyncio
from dataclasses import replace
from pathlib import Path
import secrets
import tempfile
from time import perf_counter

from client.bob import echo
from config.settings import Settings
from crypto.identity import provision
from event_log import configure_logging
from network.secure import SecureServer, connect
from network.snapshot import raw_snapshot
from storage.relationship_store import RelationshipStore
from trust.signal_collector import ContextSignalCollector
from verification.session_guard import SessionGuard
from verification.verification import Outcome


async def demonstrate():
    with tempfile.TemporaryDirectory(prefix="adaptive-full-demo-") as temporary:
        passwords = {role: secrets.token_urlsafe(32).encode() for role in ("ca", "alice", "bob")}
        creds = provision(Path(temporary) / "identities", passwords)
        collector = ContextSignalCollector()
        with RelationshipStore(Path(temporary) / "history.db") as store:
            async with await SecureServer.start(Settings(port=0), creds["bob"], lambda: passwords["bob"], echo) as server:
                async def reconnect():
                    return await connect(Settings(port=server.port), creds["alice"], lambda: passwords["alice"], collector=collector)
                async def response(request):
                    print("SIMULATED OOB comparison: MATCH; reason=" + request.reason)
                    return Outcome.SUCCESS
                guard = SessionGuard(await reconnect(), store, response, reconnect=reconnect)
                try:
                    await guard.assess(raw_snapshot(guard.connection))
                    for _ in range(4):
                        payload = secrets.token_bytes(32)
                        start = perf_counter()
                        await guard.connection.send(payload)
                        if await guard.connection.receive() != payload:
                            raise RuntimeError("exchange failed")
                        guard.connection.metrics.record_round_trip((perf_counter() - start) * 1000)
                        await guard.assess(raw_snapshot(guard.connection))
                        await asyncio.sleep(0.1)
                    print(f"ADAPTIVE_DEMO_SUCCESS trust={guard.engine.score:.2f}; TLS session active")
                finally:
                    await guard.close()


if __name__ == "__main__":
    configure_logging()
    asyncio.run(demonstrate())
