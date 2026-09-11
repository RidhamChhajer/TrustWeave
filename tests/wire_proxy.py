"""Test-only TCP relay. Captures TLS records; never terminates or decrypts TLS."""

import asyncio

from network.connection import close_writer


class WireProxy:
    def __init__(self, destination_port):
        self.destination_port = destination_port
        self.captured = {"client": bytearray(), "server": bytearray()}
        self.corrupt_next = False
        self.corrupted = False
        self._tasks = set()
        self._server = None

    async def __aenter__(self):
        self._server = await asyncio.start_server(self._accepted, "127.0.0.1", 0)
        self.port = self._server.sockets[0].getsockname()[1]
        return self

    def _accepted(self, reader, writer):
        task = asyncio.create_task(self._relay(reader, writer))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _pump(self, reader, writer, direction):
        while True:
            header = await reader.readexactly(5)
            body = await reader.readexactly(int.from_bytes(header[3:5], "big"))
            self.captured[direction].extend(header + body)
            if direction == "client" and self.corrupt_next and header[0] == 23:
                # Armed only AFTER secure connect returns; this is an application-data record.
                body = body[:-1] + bytes([body[-1] ^ 1])
                self.corrupt_next = False
                self.corrupted = True
            writer.write(header + body)
            await writer.drain()

    async def _relay(self, reader, writer):
        upstream_writer = None
        pumps = []
        try:
            upstream_reader, upstream_writer = await asyncio.open_connection("127.0.0.1", self.destination_port)
            pumps = [asyncio.create_task(self._pump(reader, upstream_writer, "client")),
                     asyncio.create_task(self._pump(upstream_reader, writer, "server"))]
            await asyncio.wait(pumps, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for task in pumps:
                task.cancel()
            await asyncio.gather(*pumps, return_exceptions=True)
            await close_writer(writer, 0.3)
            if upstream_writer is not None:
                await close_writer(upstream_writer, 0.3)

    async def __aexit__(self, *_args):
        self._server.close()
        await self._server.wait_closed()
        tasks = tuple(self._tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
