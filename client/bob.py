"""Phase-2 local socket echo server."""

import asyncio
from config.settings import Settings
from event_log import configure_logging, event
from network.connection import ConnectionFailure, FramedConnection


async def run() -> None:
    settings = Settings.from_env()
    tasks = set()

    async def handle(reader, writer):
        async with FramedConnection(reader, writer, settings) as connection:
            try:
                while True:
                    await connection.send(await connection.receive())
            except ConnectionFailure:
                pass

    def accepted(reader, writer):
        task = asyncio.create_task(handle(reader, writer))
        tasks.add(task)
        task.add_done_callback(tasks.discard)

    server = await asyncio.start_server(accepted, settings.host, settings.port)
    event("SERVER_STARTED", port=server.sockets[0].getsockname()[1])
    try:
        async with server:
            await server.serve_forever()
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    configure_logging()
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass
