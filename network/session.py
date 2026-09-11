"""Public identity and transport descriptors; no message or key material."""

from dataclasses import dataclass
import hashlib
import ipaddress


@dataclass(frozen=True)
class SessionContext:
    session_id: str
    relationship_id: str
    peer_ip: str

    @classmethod
    def create(cls, session_id: str, local_pin: str, peer_pin: str, peer_ip: str):
        pair = b"".join(sorted((bytes.fromhex(local_pin), bytes.fromhex(peer_pin))))
        relationship = hashlib.sha256(b"adaptive-trust-relationship-v1\x00" + pair).hexdigest()
        return cls(session_id, relationship, str(ipaddress.ip_address(peer_ip)))
