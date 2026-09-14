import pytest
from chat import check_runtime


@pytest.mark.parametrize("python,openssl,expected", [
    ((3, 10), (1, 1, 1), 1), ((3, 14), (1, 1, 1), 1), ((3, 14), (3, 5, 7), 0)])
def test_runtime_floor(monkeypatch, python, openssl, expected):
    monkeypatch.setattr(check_runtime.sys, "version_info", python)
    monkeypatch.setattr(check_runtime.ssl, "OPENSSL_VERSION_INFO", openssl)
    assert check_runtime.main() == expected
