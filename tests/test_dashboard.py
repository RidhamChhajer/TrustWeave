import asyncio
import json

from dashboard.runtime import Runtime


def test_dashboard_runtime_interactive_verification(tmp_path):
    async def run():
        runtime = Runtime(tmp_path / "dashboard.db")
        await runtime.start()
        try:
            await runtime.begin()
            async def wait_pending():
                while not runtime.snapshot()["pending"]:
                    await asyncio.sleep(0.01)
            await asyncio.wait_for(wait_pending(), 2)
            pending = runtime.snapshot()["pending"]
            runtime.resolve(pending["id"], "SUCCESS")
            async def wait_history():
                while not runtime.history:
                    await asyncio.sleep(0.01)
            await asyncio.wait_for(wait_history(), 2)
            assert runtime.snapshot()["score"] >= 50
            assert runtime.snapshot()["session"]["protocol"] == "TLSv1.3"
        finally:
            await runtime.close()
    asyncio.run(run())


def test_sudden_endpoint_origin_and_result(tmp_path, monkeypatch):
    from dashboard.app import create_app
    monkeypatch.chdir(tmp_path)
    async def run():
        app = create_app(tmp_path / "http.db")
        async with app.router.lifespan_context(app):
            async def request(origin):
                messages = []
                async def receive():
                    return {"type": "http.request", "body": b"", "more_body": False}
                async def send(message):
                    messages.append(message)
                await app({"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
                           "method": "POST", "scheme": "http", "path": "/api/experiment/sudden",
                           "raw_path": b"/api/experiment/sudden", "query_string": b"", "root_path": "",
                           "server": ("127.0.0.1", 8766), "client": ("127.0.0.1", 12345),
                           "headers": [(b"host", b"127.0.0.1:8766"), (b"origin", origin),
                                       (b"x-requested-with", b"adaptive-trust")]}, receive, send)
                return messages
            assert (await request(b"http://untrusted.invalid"))[0]["status"] == 403
            messages = await request(b"http://127.0.0.1:8766")
            assert messages[0]["status"] == 200
            data = json.loads(b"".join(m.get("body", b"") for m in messages))
            anomaly = next(r for r in data["rows"] if r["anomaly"])
            assert data["simulated_metadata"] and data["simulated_oob"]
            assert anomaly["score"] > 50 and anomaly["action"] == "VERIFY_IMMEDIATELY"
    asyncio.run(run())
