"""Trusted USB provisioning and read-only signed bundle inspection."""

import argparse
import base64
from datetime import datetime, timezone
from getpass import getpass
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from crypto.identity import Credentials, fingerprint, load_private_key, provision

FILES = {"identity.pem", "identity.key", "ca.pem", "peer.sha256"}
DEFAULTS = {"tls_port": 8765, "ui_port": 8766, "server_hostname": "bob.local"}


class BundleError(ValueError):
    def __init__(self):
        super().__init__("Bundle validation failed. Use an intact bundle for this device from trusted provisioning.")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def provision_bundles(target, passwords):
    target = Path(target)
    if target.exists():
        raise ValueError("Provisioning target already exists; choose a new directory.")
    if set(passwords) != {"ca", "alice", "bob"} or any(
        not isinstance(p, bytes) or len(p) < 16 or len(set(p)) < 8 for p in passwords.values()
    ) or len(set(passwords.values())) != 3:
        raise ValueError("Use three different passwords, each at least 16 bytes with at least eight distinct characters.")
    target.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="provision-", dir=target) as temporary:
        raw = Path(temporary) / "raw"
        provision(raw, passwords)
        ca_key = load_private_key(raw / "ca.key", passwords["ca"])
        organizer = target / "organizer"
        organizer.mkdir()
        for name in ("ca.pem", "ca.key"):
            shutil.move(str(raw / name), organizer / name)
        for role in ("alice", "bob"):
            bundle = target / (role + "-bundle")
            shutil.move(str(raw / role), bundle)
            manifest = {"version": 1, "role": role, "defaults": DEFAULTS,
                        "sha256": {name: hashlib.sha256((bundle / name).read_bytes()).hexdigest() for name in sorted(FILES)}}
            signature = ca_key.sign(canonical(manifest), ec.ECDSA(hashes.SHA256()))
            (bundle / "manifest.json").write_bytes(canonical(manifest))
            (bundle / "manifest.sig").write_bytes(base64.b64encode(signature))
    return {role: target / (role + "-bundle") for role in ("alice", "bob")}


def inspect_bundle(directory, role=None):
    directory = Path(directory)
    try:
        if {p.name for p in directory.iterdir()} != FILES | {"manifest.json", "manifest.sig"}:
            raise BundleError()
        if any(p.is_symlink() or not p.is_file() or p.stat().st_size > 65536 for p in directory.iterdir()):
            raise BundleError()
        manifest = json.loads((directory / "manifest.json").read_bytes())
        if set(manifest) != {"version", "role", "defaults", "sha256"} or type(manifest["version"]) is not int or manifest["version"] != 1:
            raise BundleError()
        if manifest["role"] not in {"alice", "bob"} or (role is not None and role != manifest["role"]):
            raise BundleError()
        if manifest["defaults"] != DEFAULTS or set(manifest["sha256"]) != FILES:
            raise BundleError()
        for name in FILES:
            if hashlib.sha256((directory / name).read_bytes()).hexdigest() != manifest["sha256"][name]:
                raise BundleError()
        credentials = Credentials.from_directory(directory)
        ca = x509.load_pem_x509_certificate(credentials.authority.read_bytes())
        cert = x509.load_pem_x509_certificate(credentials.certificate.read_bytes())
        ca.public_key().verify(base64.b64decode((directory / "manifest.sig").read_bytes(), validate=True),
                               canonical(manifest), ec.ECDSA(hashes.SHA256()))
        cert.verify_directly_issued_by(ca)
        now = datetime.now(timezone.utc)
        if not ca.not_valid_before_utc <= now <= ca.not_valid_after_utc or not cert.not_valid_before_utc <= now <= cert.not_valid_after_utc:
            raise BundleError()
        if cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value != manifest["role"]:
            raise BundleError()
        return {"role": manifest["role"], "fingerprint": fingerprint(cert),
                "peer_fingerprint": credentials.expected_peer_pin, "defaults": dict(DEFAULTS)}
    except Exception:
        raise BundleError() from None


def credentials_from_bundle(directory, role):
    inspect_bundle(directory, role)
    return Credentials.from_directory(Path(directory))


def main():
    parser = argparse.ArgumentParser(description="Trusted chat identity provisioning / public inspection")
    parser.add_argument("command", choices=["provision", "inspect"])
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "inspect":
            print(json.dumps(inspect_bundle(args.directory), indent=2))
        else:
            passwords = {role: getpass(f"New {role} password (16+ characters): ").encode("utf-8") for role in ("ca", "alice", "bob")}
            try:
                provision_bundles(args.directory, passwords)
            finally:
                passwords.clear()
            print("Created organizer, alice-bundle, and bob-bundle. Transfer only the matching device bundle.")
    except (ValueError, OSError):
        print("Provisioning or inspection failed. Check passwords and choose a new target or an intact bundle.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
