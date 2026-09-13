import asyncio
import json
import logging

import pytest

from chat.protocol import ChatProtocolError, DuplicateCache, decode, encode, envelope
from config.settings import Settings
from network.secure import SecureServer, connect


def samples(sender="alice"):
    correlation = {"request_id": "a" * 32, "relationship": "b" * 64}
    return [envelope(kind, sender, **fields) for kind, fields in (
        ("chat", {"text": "secret-marker नमस्ते 🌍"}), ("chat_ack", {"chat_id": "c" * 32}),
        ("ping", {}), ("pong", {"ping_id": "d" * 32}),
        ("verify_request", {**correlation, "reason": "new_relationship", "recovery": False}),
        ("verify_response", {**correlation, "decision": "MATCH"}),
        ("verification_result", {**correlation, "result": "SUCCESS", "recovery": False}),
        ("demo_mode", {"mode": "latency"}), ("session_notice", {"notice": "shutdown"}))]


def test_all_envelopes_real_tls(identities, caplog):
    creds, passwords = identities
    async def run():
        async def peer(connection):
            for expected in samples():
                message = decode(await connection.receive())
                assert message["type"] == expected["type"]
                await connection.send(encode(message))
        async with await SecureServer.start(Settings(port=0), creds["bob"], lambda: passwords["bob"], peer) as server:
            async with await connect(Settings(port=server.port), creds["alice"], lambda: passwords["alice"]) as connection:
                for message in samples():
                    await connection.send(encode(message))
                    assert decode(await connection.receive()) == message
    with caplog.at_level(logging.INFO):
        asyncio.run(run())
    assert "secret-marker" not in caplog.text


@pytest.mark.parametrize("text", ["x" * 4096, "🌍" * 1024, "\x00" * 4096], ids=["ascii-limit", "unicode-limit", "escaped-limit"])
def test_boundary(text):
    assert decode(encode(envelope("chat", "bob", text=text)))["text"] == text


@pytest.mark.parametrize("text", ["", " \t\n", "🌍" * 1025, "x" * 4097, "\ud800", 42], ids=["empty", "whitespace", "unicode-over", "ascii-over", "surrogate", "number"])
def test_bad_text(text):
    with pytest.raises(ChatProtocolError, match="^Invalid chat protocol"):
        envelope("chat", "alice", text=text)


@pytest.mark.parametrize("payload", [b"\xffsecret-marker", b"secret-marker", b"[]", b"null", b"{}",
    b'{"version":1,"version":1}', b'{"type":NaN}', b"[" * 2000, b"x" * 32769], ids=["utf8", "json", "array", "null", "empty-object", "duplicate-key", "nan", "deep", "oversize"])
def test_bad_wire(payload):
    with pytest.raises(ChatProtocolError) as error:
        decode(payload)
    assert "secret-marker" not in str(error.value)


@pytest.mark.parametrize("change", [{"version": True}, {"version": 2}, {"sender": "eve"},
    {"type": "other"}, {"extra": "secret-marker"}, {"timestamp": "2026-01-01"}, {"id": "bad"}])
def test_strict_fields(change):
    message = samples()[0] | change
    with pytest.raises(ChatProtocolError):
        decode(json.dumps(message).encode())


def test_duplicate_cache_bounded():
    cache = DuplicateCache(2)
    for value in ("a", "b"):
        cache.accept(value * 32)
    with pytest.raises(ChatProtocolError):
        cache.accept("a" * 32)
    cache.accept("c" * 32)
    assert len(cache.ids) == 2
    cache.accept("a" * 32)
