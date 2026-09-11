"""Alice CLI: mutually authenticated, pinned TLS client."""

import argparse
import asyncio
from dataclasses import replace
from pathlib import Path
import secrets
from time import perf_counter

from config.settings import Settings
from client.passwords import read_password
from crypto.identity import Credentials
from event_log import configure_logging, event
from network.secure import connect


async def run(settings: Settings, credentials: Credentials, password: bytes,
              hostname: str = "localhost") -> None:
    async with await connect(settings, credentials, lambda: password, server_hostname=hostname) as connection:
        for _ in range(3):
            payload = secrets.token_bytes(96)
            started = perf_counter()
            await connection.send(payload)
            response = await connection.receive()
            elapsed_ms = (perf_counter() - started) * 1000
            if response != payload:
                raise RuntimeError("bidirectional exchange failed")
            connection.metrics.record_round_trip(elapsed_ms)
        event("DEMO_SUCCESS", session_id=connection.info.session_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Alice encrypted exchange (never prints messages)")
    parser.add_argument("--credentials", type=Path, default=Path(".credentials/alice"))
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--server-name", default="localhost")
    args = parser.parse_args()
    configure_logging()
    try:
        settings = Settings.from_env()
        settings = replace(settings, host=args.host or settings.host,
                           port=args.port if args.port is not None else settings.port)
        credentials = Credentials.from_directory(args.credentials)
        password = read_password("Alice identity password: ")
        asyncio.run(run(settings, credentials, password, args.server_name))
    except KeyboardInterrupt:
        pass
    except Exception:
        event("SESSION_FAILED")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
