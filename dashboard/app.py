"""Serve on loopback only: python -m dashboard.app."""

from contextlib import asynccontextmanager
import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel

from dashboard.runtime import Runtime
from verification.verification import Outcome
from experiments.runner import run_trace, save
from experiments.sudden import trace, validate


class Answer(BaseModel):
    request_id: str
    outcome: Outcome


def create_app(database=".state/dashboard.db"):
    @asynccontextmanager
    async def lifespan(app):
        runtime = Runtime(database)
        await runtime.start()
        app.state.runtime = runtime
        app.state.experiment_lock = asyncio.Lock()
        try:
            yield
        finally:
            await runtime.close()

    app = FastAPI(title="Adaptive Trust Engine", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])

    def checked(request):
        if request.headers.get("origin") != str(request.base_url).rstrip("/") or request.headers.get("x-requested-with") != "adaptive-trust":
            raise HTTPException(403, "Same-origin dashboard request required")
        return app.state.runtime

    @app.get("/")
    async def index():
        return FileResponse(Path(__file__).parent / "index.html", headers={"Cache-Control": "no-store"})

    @app.get("/api/state")
    async def state():
        return app.state.runtime.snapshot()

    @app.get("/experiment.js")
    async def experiment_script():
        return FileResponse(Path(__file__).parent / "experiment.js", media_type="text/javascript")

    @app.post("/api/start")
    async def start(request: Request):
        try:
            await checked(request).begin()
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from None
        return {"ok": True}

    @app.post("/api/stop")
    async def stop(request: Request):
        await checked(request).stop()
        return {"ok": True}

    @app.post("/api/experiment/sudden")
    async def sudden(request: Request):
        checked(request)
        lock = app.state.experiment_lock
        if lock.locked():
            raise HTTPException(409, "An experiment is already running")
        async with lock:
            result = await run_trace(trace())
            validate(result)
            save(result, "artifacts/dashboard-sudden.json")
            return {"simulated_metadata": True, "simulated_oob": True,
                    "transport": result["transport"], "rows": result["rows"]}

    @app.post("/api/verify")
    async def verification(request: Request, answer: Answer):
        try:
            checked(request).resolve(answer.request_id, answer.outcome)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from None
        return {"ok": True}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8766, access_log=False)
