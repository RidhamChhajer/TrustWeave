import secrets

import pytest

from crypto.identity import provision


class Passwords(dict):
    def __repr__(self):
        return "<test passwords redacted>"


@pytest.fixture(scope="session")
def identities(tmp_path_factory):
    path = tmp_path_factory.mktemp("pki") / "credentials"
    passwords = Passwords({role: secrets.token_urlsafe(24).encode() for role in ("ca", "alice", "bob")})
    return provision(path, passwords), passwords
