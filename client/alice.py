"""Phase-2 local socket smoke client."""

import asyncio
from config.settings import Settings
from event_log import configure_logging, event
from network.plain import connect


async def run() -> None:
    async with await connect(Settings.from_env()) as connection:
        await connection.send(b"phase-2-network-check")
        if await connection.receive() != b"phase-2-network-check":
            raise RuntimeError("exchange failed")
        event("DEMO_SUCCESS")


if __name__ == "__main__":
    configure_logging()
    asyncio.run(run())
