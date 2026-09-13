import subprocess
import sys

import pytest

from chat.config import ChatConfig


def test_import_is_inert(tmp_path):
    result = subprocess.run([sys.executable, "-c", "import chat; import threading; assert len(threading.enumerate()) == 1"],
                            capture_output=True, check=True)
    assert not result.stdout and not result.stderr


@pytest.mark.parametrize("values", [{"tls_port": 0}, {"ui_port": 8765}, {"chat_bytes": 4097},
    {"queue_size": True}, {"reconnect_attempts": 4}, {"heartbeat_seconds": float("nan")},
    {"verification_timeout": -1}])
def test_configuration_bounds(values):
    with pytest.raises(ValueError):
        ChatConfig(**values)


def test_defaults():
    assert ChatConfig().chat_bytes == 4096
