"""Milestone foundation smoke entry point."""

from config.settings import Settings
from event_log import configure_logging, event


def main() -> None:
    Settings.from_env()
    configure_logging()
    event("APPLICATION_READY")


if __name__ == "__main__":
    main()
