import asyncio
from dataclasses import replace
import json
from pathlib import Path
import socket
import subprocess
import sys

import pytest

from chat.app import main, preflight
from tests.test_chat_bob import make_bob, free_port


def test_preflight_spaces_missing_bundle_and_ports(tmp_path, capsys):
    parent = tmp_path / "path with spaces"
    parent.mkdir()
    bob, bundles, _ = make_bob(parent)
    config = replace(bob.config, ui_port=free_port())
    assert preflight("bob", bundles["bob"], config)["ui_host"] == "127.0.0.1"
    with pytest.raises(ValueError):
        preflight("alice", bundles["bob"], config)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", config.ui_port))
        with pytest.raises(ValueError):
            preflight("bob", bundles["bob"], config)
    assert main(["bob", "--bundle", str(parent / "missing"), "--check"]) == 1
    assert str(parent) not in capsys.readouterr().out
    result = subprocess.run([sys.executable, "-m", "chat.app", "bob", "--bundle", str(bundles["bob"]),
                             "--tls-port", str(config.tls_port), "--ui-port", str(config.ui_port), "--check"],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0 and not result.stderr
    assert json.loads(result.stdout)["role"] == "bob"


def test_missing_bob_fails_sanitized(tmp_path):
    from chat.alice import AliceRuntime
    bob, bundles, passwords = make_bob(tmp_path)
    alice = AliceRuntime(bundles["alice"], bob.config, tmp_path / "alice.db")
    async def run():
        try:
            await alice.unlock(passwords["alice"].decode())
            with pytest.raises(ValueError, match="Secure connection failed"):
                await alice._connect("127.0.0.1")
            assert alice.gate.state.value == "RESTRICTED"
        finally:
            await alice.close()
    asyncio.run(run())
