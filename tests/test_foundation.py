import json
import logging

import pytest

from config.settings import Settings
from event_log import event
from main import main


@pytest.mark.parametrize("changes", [
    {"host": ""}, {"port": -1}, {"port": 65536}, {"max_frame": 0},
    {"max_frame": 1048577}, {"connect_timeout": 0}, {"io_timeout": float("nan")},
    {"close_timeout": float("inf")},
])
def test_invalid_configuration(changes):
    with pytest.raises(ValueError):
        Settings(**changes)


def test_environment(monkeypatch):
    monkeypatch.setenv("TRUST_PORT", "9000")
    assert Settings.from_env().port == 9000


def test_application_starts(caplog):
    with caplog.at_level(logging.INFO, logger="adaptive_trust"):
        main()
    assert json.loads(caplog.records[-1].message)["event"] == "APPLICATION_READY"


@pytest.mark.parametrize("name,fields", [
    ("secret", {}), ("FRAME_SENT", {"plaintext": "secret"}),
    ("FRAME_SENT", {"byte_count": "secret"}),
    ("SESSION_STARTED", {"session_id": "secret"}),
])
def test_log_rejects_unsafe_fields(name, fields, caplog):
    with pytest.raises(ValueError):
        event(name, **fields)
    assert not caplog.records
