"""Transport configuration; no secrets are accepted here."""

from dataclasses import dataclass
import math
import os

METADATA_MAX_AGE_SECONDS = 30.0
DASHBOARD_PORT = 8766


@dataclass(frozen=True)
class Settings:
    host: str = "127.0.0.1"
    port: int = 8765
    max_frame: int = 1024 * 1024
    connect_timeout: float = 10.0
    io_timeout: float = 30.0
    close_timeout: float = 3.0

    def __post_init__(self) -> None:
        if not self.host or not self.host.strip():
            raise ValueError("host must not be empty")
        if not 0 <= self.port <= 65535:
            raise ValueError("port must be between 0 and 65535")
        if not 1 <= self.max_frame <= 1024 * 1024:
            raise ValueError("max_frame must be between 1 and 1048576")
        for value in (self.connect_timeout, self.io_timeout, self.close_timeout):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("timeouts must be positive and finite")

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            host=os.getenv("TRUST_HOST", "127.0.0.1"),
            port=int(os.getenv("TRUST_PORT", "8765")),
            max_frame=int(os.getenv("TRUST_MAX_FRAME", "1048576")),
            connect_timeout=float(os.getenv("TRUST_CONNECT_TIMEOUT", "10")),
            io_timeout=float(os.getenv("TRUST_IO_TIMEOUT", "30")),
            close_timeout=float(os.getenv("TRUST_CLOSE_TIMEOUT", "3")),
        )
