import asyncio
import json
import secrets
import shutil

import pytest

from chat.bundles import BundleError, credentials_from_bundle, inspect_bundle, provision_bundles
from config.settings import Settings
from network.secure import SecureServer, connect


@pytest.fixture
def bundles(tmp_path):
    passwords = {role: secrets.token_urlsafe(24).encode() for role in ("ca", "alice", "bob")}
    return provision_bundles(tmp_path / "provisioned", passwords), passwords


def test_isolated_usb_copies_and_numeric_tls(bundles, tmp_path):
    paths, passwords = bundles
    copied = {}
    for role in paths:
        destination = tmp_path / (role + " laptop")
        shutil.copytree(paths[role], destination)
        assert not list(destination.rglob("ca.key"))
        assert len(list(destination.rglob("*.key"))) == 1
        assert inspect_bundle(destination)["role"] == role
        copied[role] = credentials_from_bundle(destination, role)
    async def run():
        async def handler(connection):
            await connection.send(b"portable")
        async with await SecureServer.start(Settings(port=0), copied["bob"], lambda: passwords["bob"], handler) as server:
            async with await connect(Settings(host="127.0.0.1", port=server.port), copied["alice"],
                                     lambda: passwords["alice"], server_hostname="bob.local") as connection:
                assert await connection.receive() == b"portable"
    asyncio.run(run())


@pytest.mark.parametrize("damage", ["role", "key", "pin", "missing", "manifest", "signature", "extra"])
def test_reject_altered(bundles, damage):
    paths, _ = bundles
    alice = paths["alice"]
    if damage == "role":
        with pytest.raises(BundleError):
            credentials_from_bundle(alice, "bob")
        return
    if damage == "missing":
        (alice / "identity.pem").unlink()
    elif damage == "manifest":
        manifest = json.loads((alice / "manifest.json").read_bytes())
        manifest["sha256"]["peer.sha256"] = "0" * 64
        (alice / "manifest.json").write_text(json.dumps(manifest))
    else:
        name = {"key": "identity.key", "pin": "peer.sha256", "signature": "manifest.sig", "extra": "ca.key"}[damage]
        (alice / name).write_bytes(b"altered")
    with pytest.raises(BundleError):
        inspect_bundle(alice)


def test_provision_refusals(bundles, tmp_path):
    _, passwords = bundles
    with pytest.raises(ValueError):
        provision_bundles(tmp_path / "provisioned", passwords)
    with pytest.raises(ValueError):
        provision_bundles(tmp_path / "weak", {role: b"a" * 20 for role in passwords})
    assert not (tmp_path / "weak").exists()
