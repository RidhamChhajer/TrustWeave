import pytest
from chat import check_runtime


@pytest.mark.parametrize("python,openssl,tls13,expected", [
    ((3, 10), (3, 0, 0), True, 1),
    ((3, 14), (1, 1, 1), True, 1),
    ((3, 14), (3, 0, 0), True, 0),
    ((3, 14), (3, 0, 0), False, 1),
    ((3, 14), (3, 5, 7), True, 0)])
def test_runtime_floor(monkeypatch, python, openssl, tls13, expected):
    monkeypatch.setattr(check_runtime.sys, "version_info", python)
    monkeypatch.setattr(check_runtime.ssl, "OPENSSL_VERSION_INFO", openssl)
    monkeypatch.setattr(check_runtime.ssl, "HAS_TLSv1_3", tls13)
    assert check_runtime.main() == expected
