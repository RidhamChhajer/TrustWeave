import asyncio

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
