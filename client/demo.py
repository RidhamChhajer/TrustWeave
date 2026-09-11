"""Local socket demo; temporary encrypted credentials and no secret output."""

import asyncio
from dataclasses import replace
from pathlib import Path
import secrets
import tempfile

from client.alice import run as alice
from client.bob import echo
from config.settings import Settings
from crypto.identity import provision
from event_log import configure_logging, event
from network.secure import SecureServer


async def demonstrate() -> None:
    with tempfile.TemporaryDirectory(prefix="adaptive-trust-demo-") as temporary:
        passwords = {role: secrets.token_urlsafe(32).encode() for role in ("ca", "alice", "bob")}
        identities = provision(Path(temporary) / "credentials", passwords)
        settings = Settings(port=0)
        async with await SecureServer.start(settings, identities["bob"], lambda: passwords["bob"], echo) as server:
            await alice(replace(settings, port=server.port), identities["alice"], passwords["alice"])


def main() -> None:
    configure_logging()
    try:
        asyncio.run(demonstrate())
    except Exception:
        event("SESSION_FAILED")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
