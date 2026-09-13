import asyncio
import json

import pytest

from chat.bridge import Events, command_from_text, create_app
from chat.config import ChatConfig


@pytest.mark.parametrize("text", ['{}', '[]', '{"command":"unlock","password":"secret","extra":1}',
    '{"command":"send_chat","text":" "}', '{"command":"disconnect","command":"disconnect"}'])
def test_bad_commands_sanitized(text):
    with pytest.raises(ValueError) as error:
        command_from_text(text)
    assert "secret" not in str(error.value)


def test_queue_bounded():
    events = Events(2)
    queue = events.subscribe()
    for i in range(3):
        events.publish({"event": "state", "i": i})
    assert queue.qsize() == 1 and queue.get_nowait() == {"event": "resync"}


class FakeRuntime:
    config = ChatConfig()
    def __init__(self):
        self.events = Events()
        self.commands = 0
    def snapshot(self):
        return {"role": "bob", "state": "LOCKED"}
    async def command(self, command):
        self.commands += 1
        self.events.publish({"event": "state", "data": self.snapshot()})
    async def browser_closed(self):
        pass
    async def close(self):
        pass


def test_origin_client_host_and_password():
    async def run(origin="http://127.0.0.1:8766", client="127.0.0.1", host="127.0.0.1:8766"):
        runtime = FakeRuntime()
        incoming = asyncio.Queue()
        await incoming.put({"type": "websocket.connect"})
        output = []
        async def send(message):
            output.append(message)
            if message["type"] == "websocket.accept":
                await incoming.put({"type": "websocket.receive", "text": '{"command":"unlock","password":"PASSWORD-MARKER"}'})
            if message["type"] == "websocket.send" and runtime.commands:
                await incoming.put({"type": "websocket.disconnect", "code": 1000})
        scope = {"type": "websocket", "asgi": {"version": "3.0"}, "scheme": "ws", "path": "/ws",
                 "query_string": b"", "root_path": "", "client": (client, 1), "server": ("127.0.0.1", 8766),
                 "headers": [(b"host", host.encode()), (b"origin", origin.encode())], "subprotocols": []}
        await asyncio.wait_for(create_app(runtime)(scope, incoming.get, send), 2)
        assert "PASSWORD-MARKER" not in repr(output)
        return output
    assert asyncio.run(run())[0]["type"] == "websocket.accept"
    for values in ({"origin": "http://evil.invalid"}, {"client": "192.168.1.2"}, {"host": "evil.invalid"}):
        assert asyncio.run(run(**values))[0]["type"] != "websocket.accept"
