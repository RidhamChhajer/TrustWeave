"""Bounded, non-secret configuration for the LAN chat application."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ChatConfig:
    tls_port: int = 8765
    ui_port: int = 8766
    chat_bytes: int = 4096
    heartbeat_seconds: float = 1.0
    verification_timeout: float = 30.0
    queue_size: int = 128
    duplicate_cache: int = 2048
    history_size: int = 500
    reconnect_attempts: int = 3

    def __post_init__(self):
        for value, low, high in (
            (self.tls_port, 1, 65535), (self.ui_port, 1, 65535),
            (self.chat_bytes, 1, 4096), (self.queue_size, 1, 1024),
            (self.duplicate_cache, 1, 16384), (self.history_size, 1, 2000),
            (self.reconnect_attempts, 1, 3),
        ):
            if type(value) is not int or not low <= value <= high:
                raise ValueError("invalid chat configuration")
        for value in (self.heartbeat_seconds, self.verification_timeout):
            if type(value) not in (int, float) or not math.isfinite(value) or not 0.05 <= value <= 120:
                raise ValueError("invalid chat timing configuration")
        if self.tls_port == self.ui_port:
            raise ValueError("TLS and browser ports must differ")
