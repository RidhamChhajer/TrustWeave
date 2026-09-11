from getpass import GetPassWarning
import json
from pathlib import Path
import subprocess
import sys
import warnings

import pytest

from client import passwords

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("module", ["client.alice", "client.bob", "client.provision"])
def test_cli_help(module):
    result = subprocess.run([sys.executable, "-m", module, "--help"], cwd=ROOT,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0
    assert "usage:" in result.stdout


@pytest.mark.parametrize("module", ["client.alice", "client.bob"])
def test_cli_configuration_error_is_sanitized(module, tmp_path):
    private_marker = "sensitive-file-path-do-not-print"
    result = subprocess.run([sys.executable, "-m", module, "--credentials", str(tmp_path / private_marker)],
                            cwd=ROOT, capture_output=True, text=True, timeout=10)
    assert result.returncode == 1
    assert private_marker not in result.stderr
    assert "Traceback" not in result.stderr
    assert json.loads(result.stderr)["event"] == "SESSION_FAILED"


def test_password_requires_hidden_input(monkeypatch):
    def no_secure_terminal(_prompt):
        warnings.warn("cannot hide input", GetPassWarning)
        return "must not be returned"
    monkeypatch.setattr(passwords, "getpass", no_secure_terminal)
    with pytest.raises(GetPassWarning):
        passwords.read_password("Password: ")
