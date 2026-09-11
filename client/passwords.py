"""Refuse password entry if the terminal cannot disable echo."""

from getpass import GetPassWarning, getpass
import warnings


def read_password(prompt: str) -> bytes:
    with warnings.catch_warnings():
        warnings.simplefilter("error", GetPassWarning)
        return getpass(prompt).encode("utf-8")
