"""Mutual TLS 1.3 contexts; OpenSSL owns ephemeral and directional traffic keys."""

from dataclasses import dataclass
import hmac
import re
import ssl
from typing import Callable

from cryptography import x509

from crypto.identity import Credentials, fingerprint


class AuthenticationError(Exception):
    """Peer cannot be authenticated. Contains no remote-controlled diagnostics."""


@dataclass(frozen=True)
class PeerInfo:
    fingerprint: str
    protocol: str
    cipher: str


def context(credentials: Credentials, password: Callable[[], bytes], *, server: bool) -> ssl.SSLContext:
    """Explicit contexts avoid create_default_context's SSLKEYLOGFILE behavior."""
    if not ssl.HAS_TLSv1_3:
        raise RuntimeError("TLS 1.3 is required")
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER if server else ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.maximum_version = ssl.TLSVersion.TLSv1_3
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.options |= ssl.OP_NO_TICKET
    ctx.keylog_filename = None
    if server:
        ctx.num_tickets = 0
    else:
        ctx.check_hostname = True
    ctx.load_verify_locations(cafile=str(credentials.authority))
    ctx.load_cert_chain(str(credentials.certificate), str(credentials.private_key), password=password)
    return ctx


def authenticate(tls: ssl.SSLObject | ssl.SSLSocket | None, expected_pin: str) -> PeerInfo:
    if tls is None or tls.version() != "TLSv1.3" or tls.session_reused:
        raise AuthenticationError("authenticated fresh TLS 1.3 session required")
    if not re.fullmatch(r"[0-9a-f]{64}", expected_pin):
        raise AuthenticationError("invalid peer identity configuration")
    der = tls.getpeercert(binary_form=True)
    if not der:
        raise AuthenticationError("peer certificate required")
    try:
        pin = fingerprint(x509.load_der_x509_certificate(der))
    except ValueError:
        raise AuthenticationError("invalid peer certificate") from None
    if not hmac.compare_digest(pin, expected_pin):
        raise AuthenticationError("peer identity mismatch")
    cipher = tls.cipher()
    if cipher is None:
        raise AuthenticationError("cipher negotiation incomplete")
    return PeerInfo(pin, "TLSv1.3", cipher[0])
