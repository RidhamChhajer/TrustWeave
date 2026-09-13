"""Bounded same-origin loopback browser bridge; all diagnostics are fixed text."""

import asyncio
from contextlib import asynccontextmanager
import ipaddress
import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from chat.protocol import MODES

COMMANDS = {"unlock": {"password"}, "start_server": set(), "connect": {"address"},
            "send_chat": {"text"}, "confirm_verification": {"request_id", "decision"},
            "set_demo_mode": {"mode"}, "disconnect": set()}


def command_from_text(text):
    try:
        if len(text.encode("utf-8")) > 32768:
            raise ValueError()
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError()
                result[key] = value
            return result
        command = json.loads(text, object_pairs_hook=unique)
        kind = command["command"]
        if kind not in COMMANDS or set(command) != {"command"} | COMMANDS[kind]:
            raise ValueError()
        for key, value in command.items():
            if not isinstance(value, str):
                raise ValueError()
            if key == "password" and not 1 <= len(value.encode("utf-8")) <= 1024:
                raise ValueError()
            if key == "text" and (not value.strip() or len(value.encode("utf-8")) > 4096):
                raise ValueError()
        if kind == "confirm_verification":
            from chat.protocol import _hex
            if not _hex(command["request_id"]) or command["decision"] not in {"MATCH", "MISMATCH", "CANCEL"}:
                raise ValueError()
        if kind == "set_demo_mode" and command["mode"] not in MODES:
            raise ValueError()
        if kind == "connect" and len(command["address"]) > 15:
            raise ValueError()
        return command
    except (ValueError, KeyError, TypeError, UnicodeError, RecursionError):
        raise ValueError("Invalid command. Check the input and try again.") from None


class Events:
    def __init__(self, bound=128):
        self.bound = bound
        self.clients = set()

    def subscribe(self):
        if len(self.clients) >= 4:
            raise ValueError("Too many local browser connections.")
        queue = asyncio.Queue(self.bound)
        self.clients.add(queue)
        return queue

    def publish(self, event):
        for queue in tuple(self.clients):
            if queue.full():
                # A slow consumer reconnects and reconstructs from bounded memory.
                while not queue.empty():
                    queue.get_nowait()
                queue.put_nowait({"event": "resync"})
            else:
                queue.put_nowait(event)


class LoopbackOnly:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in {"http", "websocket"}:
            try:
                allowed = ipaddress.ip_address(scope.get("client", ("", 0))[0]).is_loopback
            except ValueError:
                allowed = False
            host = dict(scope.get("headers", [])).get(b"host", b"").split(b":")[0]
            allowed = allowed and host in {b"127.0.0.1", b"localhost"}
            if not allowed:
                if scope["type"] == "websocket":
                    await send({"type": "websocket.close", "code": 1008})
                else:
                    await send({"type": "http.response.start", "status": 403, "headers": []})
                    await send({"type": "http.response.body", "body": b"Local browser required"})
                return
        await self.app(scope, receive, send)


def create_app(runtime):
    @asynccontextmanager
    async def lifespan(app):
        try:
            yield
        finally:
            await runtime.close()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.runtime = runtime
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])
    app.add_middleware(LoopbackOnly)

    @app.get("/")
    async def index():
        return FileResponse(Path(__file__).parent / "index.html", headers={
            "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'"})

    @app.get("/chat.js")
    async def javascript():
        return FileResponse(Path(__file__).parent / "chat.js", media_type="text/javascript")

    @app.get("/chat.css")
    async def stylesheet():
        return FileResponse(Path(__file__).parent / "chat.css", media_type="text/css")

    @app.websocket("/ws")
    async def websocket(ws: WebSocket):
        expected = f"http://127.0.0.1:{runtime.config.ui_port}"
        if ws.headers.get("origin") != expected or ws.headers.get("host") != f"127.0.0.1:{runtime.config.ui_port}":
            await ws.close(code=1008)
            return
        try:
            queue = runtime.events.subscribe()
        except ValueError:
            await ws.close(code=1013)
            return
        await ws.accept()
        async def output():
            await ws.send_json({"event": "state", "data": runtime.snapshot()})
            while True:
                event = await queue.get()
                if event["event"] == "resync":
                    await ws.close(code=1013)
                    return
                await ws.send_json(event)
        async def commands():
            while True:
                try:
                    text = await ws.receive_text()
                    command = command_from_text(text)
                    text = None
                    try:
                        await runtime.command(command)
                    finally:
                        command.clear()
                except WebSocketDisconnect:
                    return
                except Exception:
                    if queue.full():
                        return
                    queue.put_nowait({"event": "error", "message": "Command failed safely. Check input and connection state, then retry."})
        tasks = [asyncio.create_task(output()), asyncio.create_task(commands())]
        try:
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            runtime.events.clients.discard(queue)
            await runtime.browser_closed()
    return app
