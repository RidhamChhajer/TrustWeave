"""Phase-2 development transport. Removed from public entry points in phase 4."""

import asyncio
from time import perf_counter

from config.settings import Settings
from network.connection import FramedConnection, SessionInfo
import uuid


async def connect(settings: Settings) -> FramedConnection:
    start = perf_counter()
    reader, writer = await asyncio.wait_for(
        asyncio.open_connection(settings.host, settings.port), settings.connect_timeout)
    return FramedConnection(reader, writer, settings,
                            SessionInfo(uuid.uuid4().hex, elapsed_ms=(perf_counter() - start) * 1000))
