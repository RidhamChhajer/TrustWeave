from dataclasses import replace
import secrets
import ssl

from cryptography import x509
from cryptography.hazmat.primitives import serialization
import pytest

from crypto.identity import Credentials, fingerprint, load_private_key, provision
from crypto.key_exchange import AuthenticationError, authenticate, context
from tests.tls_helpers import TLSChannel


def channel(identities, hostname="localhost"):
    creds, passwords = identities
    return TLSChannel(context(creds["alice"], lambda: passwords["alice"], server=False),
                      context(creds["bob"], lambda: passwords["bob"], server=True), hostname).handshake()


def test_encrypted_distinct_identities(identities):
    creds, passwords = identities
    pins = []
    for role in ("alice", "bob"):
        raw = creds[role].private_key.read_bytes()
        assert raw.startswith(b"-----BEGIN ENCRYPTED PRIVATE KEY-----")
        key = load_private_key(creds[role].private_key, passwords[role])
        cert = x509.load_pem_x509_certificate(creds[role].certificate.read_bytes())
        assert key.public_key().public_numbers() == cert.public_key().public_numbers()
        pins.append(fingerprint(cert))
        with pytest.raises((ValueError, TypeError)):
            serialization.load_pem_private_key(raw, password=None)
        with pytest.raises(ValueError):
            load_private_key(creds[role].private_key, b"wrong-password")
    assert pins[0] != pins[1]
    assert creds["alice"].expected_peer_pin == pins[1]
    assert creds["bob"].expected_peer_pin == pins[0]


def test_no_overwrite_or_empty_password(tmp_path, identities):
    creds, passwords = identities
    with pytest.raises(FileExistsError):
        provision(creds["alice"].certificate.parent.parent, passwords)
    with pytest.raises(ValueError):
        provision(tmp_path / "bad", {"ca": b""})
    assert not (tmp_path / "bad").exists()


def test_tls_authentication_and_compatible_directional_keys(identities):
    creds, _ = identities
    link = channel(identities)
    assert authenticate(link.client, creds["alice"].expected_peer_pin).protocol == "TLSv1.3"
    authenticate(link.server, creds["bob"].expected_peer_pin)
    # No key material is exported. Correct decryption proves compatible traffic keys.
    message = secrets.token_bytes(80)
    link.client.write(message)
    wire = link.c_out.read()
    assert message not in wire
    link.s_in.write(wire)
    assert link.server.read(1000) == message
    reply = secrets.token_bytes(80)
    link.server.write(reply)
    link.c_in.write(link.s_out.read())
    assert link.client.read(1000) == reply


def test_wrong_pin_rejected(identities):
    link = channel(identities)
    with pytest.raises(AuthenticationError, match="identity mismatch"):
        authenticate(link.client, "0" * 64)
    with pytest.raises(AuthenticationError):
        authenticate(None, "0" * 64)


def test_hostname_rejected(identities):
    with pytest.raises(ssl.SSLCertVerificationError):
        channel(identities, "wrong.example")


def test_untrusted_ca_rejected(tmp_path, identities):
    creds, passwords = identities
    other = provision(tmp_path / "other", passwords)
    wrong = replace(creds["alice"], authority=other["alice"].authority)
    client = context(wrong, lambda: passwords["alice"], server=False)
    server = context(creds["bob"], lambda: passwords["bob"], server=True)
    with pytest.raises(ssl.SSLCertVerificationError):
        TLSChannel(client, server).handshake()


def test_missing_client_certificate(identities):
    creds, passwords = identities
    client = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    client.minimum_version = ssl.TLSVersion.TLSv1_3
    client.load_verify_locations(str(creds["alice"].authority))
    server = context(creds["bob"], lambda: passwords["bob"], server=True)
    with pytest.raises(ssl.SSLError):
        TLSChannel(client, server).handshake()


def test_invalid_cryptographic_input(tmp_path):
    bad = tmp_path / "invalid.key"
    bad.write_bytes(b"not a private key")
    with pytest.raises(ValueError):
        load_private_key(bad, b"valid-password")
    (tmp_path / "peer.sha256").write_text("invalid", encoding="ascii")
    with pytest.raises(ValueError):
        Credentials.from_directory(tmp_path)


def test_no_key_logging_or_tickets(monkeypatch, tmp_path, identities):
    keylog = tmp_path / "must-not-exist.log"
    monkeypatch.setenv("SSLKEYLOGFILE", str(keylog))
    creds, passwords = identities
    for role in ("alice", "bob"):
        ctx = context(creds[role], lambda: passwords[role], server=role == "bob")
        assert ctx.keylog_filename is None
        assert ctx.options & ssl.OP_NO_TICKET
        assert ctx.minimum_version == ctx.maximum_version == ssl.TLSVersion.TLSv1_3
        assert ctx.verify_mode == ssl.CERT_REQUIRED
        if role == "bob":
            assert ctx.num_tickets == 0
    channel(identities)
    assert not keylog.exists()
