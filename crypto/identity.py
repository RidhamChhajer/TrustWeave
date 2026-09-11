"""Local development PKI. Private keys are always encrypted at rest."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import ipaddress
from pathlib import Path
import re

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


@dataclass(frozen=True)
class Credentials:
    certificate: Path
    private_key: Path
    authority: Path
    expected_peer_pin: str

    @classmethod
    def from_directory(cls, directory: Path) -> "Credentials":
        pin = (directory / "peer.sha256").read_text(encoding="ascii").strip()
        if not re.fullmatch(r"[0-9a-f]{64}", pin):
            raise ValueError("invalid peer fingerprint")
        return cls(directory / "identity.pem", directory / "identity.key",
                   directory / "ca.pem", pin)


def fingerprint(certificate: x509.Certificate) -> str:
    """SHA-256 of public SubjectPublicKeyInfo; stable across certificate renewal."""
    public = certificate.public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    return hashlib.sha256(public).hexdigest()


def load_private_key(path: Path, password: bytes) -> ec.EllipticCurvePrivateKey:
    if not password:
        raise ValueError("a nonempty key password is required")
    key = serialization.load_pem_private_key(path.read_bytes(), password=password)
    if not isinstance(key, ec.EllipticCurvePrivateKey) or not isinstance(key.curve, ec.SECP256R1):
        raise ValueError("expected a P-256 identity key")
    return key


def _write_new(path: Path, data: bytes) -> None:
    with path.open("xb") as output:
        output.write(data)


def _private_bytes(key: ec.EllipticCurvePrivateKey, password: bytes) -> bytes:
    return key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                             serialization.BestAvailableEncryption(password))


def provision(directory: Path, passwords: dict[str, bytes]) -> dict[str, Credentials]:
    """Create a new demo CA and endpoint folders. Never overwrite existing data.

    This is trusted, single-machine bootstrap, not identity verification over a network.
    The caller supplies separate passwords for ca, alice and bob without logging them.
    """
    if any(not isinstance(passwords.get(role), bytes) or len(passwords[role]) < 12
           for role in ("ca", "alice", "bob")):
        raise ValueError("each role needs a password of at least 12 bytes")
    directory.mkdir(parents=True, exist_ok=False)
    now = datetime.now(timezone.utc)
    ca_key = ec.generate_private_key(ec.SECP256R1())
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Adaptive Trust Demo CA")])
    ca = (x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name)
          .public_key(ca_key.public_key()).serial_number(x509.random_serial_number())
          .not_valid_before(now - timedelta(minutes=5)).not_valid_after(now + timedelta(days=365))
          .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
          .add_extension(x509.KeyUsage(False, False, False, False, False, True, True, False, False), critical=True)
          .add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False)
          .sign(ca_key, hashes.SHA256()))
    ca_pem = ca.public_bytes(serialization.Encoding.PEM)
    _write_new(directory / "ca.pem", ca_pem)
    _write_new(directory / "ca.key", _private_bytes(ca_key, passwords["ca"]))
    pins = {}
    for role in ("alice", "bob"):
        endpoint = directory / role
        endpoint.mkdir()
        key = ec.generate_private_key(ec.SECP256R1())
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, role)])
        names = [x509.DNSName(role + ".local")]
        if role == "bob":
            names.extend([x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))])
        usage = ExtendedKeyUsageOID.CLIENT_AUTH if role == "alice" else ExtendedKeyUsageOID.SERVER_AUTH
        cert = (x509.CertificateBuilder().subject_name(subject).issuer_name(ca.subject)
                .public_key(key.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(now - timedelta(minutes=5)).not_valid_after(now + timedelta(days=30))
                .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
                .add_extension(x509.KeyUsage(True, False, False, False, False, False, False, False, False), critical=True)
                .add_extension(x509.ExtendedKeyUsage([usage]), critical=False)
                .add_extension(x509.SubjectAlternativeName(names), critical=False)
                .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
                .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False)
                .sign(ca_key, hashes.SHA256()))
        _write_new(endpoint / "identity.pem", cert.public_bytes(serialization.Encoding.PEM))
        _write_new(endpoint / "identity.key", _private_bytes(key, passwords[role]))
        _write_new(endpoint / "ca.pem", ca_pem)
        pins[role] = fingerprint(cert)
    for role, peer in (("alice", "bob"), ("bob", "alice")):
        _write_new(directory / role / "peer.sha256", (pins[peer] + "\n").encode("ascii"))
    return {role: Credentials.from_directory(directory / role) for role in ("alice", "bob")}
