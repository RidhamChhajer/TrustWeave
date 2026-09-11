"""Bob CLI: mutually authenticated, pinned TLS echo endpoint."""

import argparse
import asyncio
from dataclasses import replace
from pathlib import Path

from config.settings import Settings
from client.passwords import read_password
from crypto.identity import Credentials
from event_log import configure_logging, event
from network.connection import FramedConnection, PeerClosed
from network.secure import SecureServer


async def echo(connection: FramedConnection) -> None:
    try:
        while True:
            await connection.send(await connection.receive())
    except PeerClosed:
        pass


async def run(settings: Settings, credentials: Credentials, password: bytes) -> None:
    async with await SecureServer.start(settings, credentials, lambda: password, echo) as server:
        await server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Bob authenticated TLS server")
    parser.add_argument("--credentials", type=Path, default=Path(".credentials/bob"))
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    args = parser.parse_args()
    configure_logging()
    try:
        settings = Settings.from_env()
        settings = replace(settings, host=args.host or settings.host,
                           port=args.port if args.port is not None else settings.port)
        credentials = Credentials.from_directory(args.credentials)
        password = read_password("Bob identity password: ")
        asyncio.run(run(settings, credentials, password))
    except KeyboardInterrupt:
        pass
    except Exception:
        event("SESSION_FAILED")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
