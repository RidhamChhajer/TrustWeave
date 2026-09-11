"""Provision fresh local-demo credentials; refuses existing output directories."""

import argparse
from pathlib import Path

from crypto.identity import provision
from client.passwords import read_password
from event_log import configure_logging, event


def main() -> None:
    parser = argparse.ArgumentParser(description="Trusted local development PKI bootstrap")
    parser.add_argument("--directory", type=Path, default=Path(".credentials"))
    args = parser.parse_args()
    configure_logging()
    try:
        if args.directory.exists():
            raise FileExistsError("credentials already exist")
        passwords = {}
        for role in ("ca", "alice", "bob"):
            value = read_password(f"New {role} password (at least 12 bytes): ")
            confirmation = read_password(f"Confirm {role} password: ")
            if value != confirmation:
                raise ValueError("password confirmation mismatch")
            passwords[role] = value
        provision(args.directory, passwords)
        event("IDENTITY_CREATED")
    except KeyboardInterrupt:
        pass
    except Exception:
        event("SESSION_FAILED")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
