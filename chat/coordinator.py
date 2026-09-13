"""Single-event-loop state machine with gates checked at delivery boundaries."""

from collections import deque
from enum import Enum

from chat.config import ChatConfig
from chat.protocol import ChatProtocolError, DuplicateCache, decode, encode
from network.connection import ConnectionFailure


class State(str, Enum):
    LOCKED = "LOCKED"
    CONNECTING = "CONNECTING"
    VERIFYING = "VERIFYING"
    ACTIVE = "ACTIVE"
    RECONNECTING = "RECONNECTING"
    RESTRICTED = "RESTRICTED"
    CLOSED = "CLOSED"


TRANSITIONS = {
    State.LOCKED: {State.CONNECTING, State.CLOSED},
    State.CONNECTING: {State.VERIFYING, State.RESTRICTED, State.CLOSED},
    State.VERIFYING: {State.ACTIVE, State.RECONNECTING, State.RESTRICTED, State.CLOSED},
    State.ACTIVE: {State.VERIFYING, State.RECONNECTING, State.RESTRICTED, State.CLOSED},
    State.RECONNECTING: {State.VERIFYING, State.RESTRICTED, State.CLOSED},
    State.RESTRICTED: {State.CLOSED}, State.CLOSED: set(),
}


class Coordinator:
    def __init__(self, role, config=ChatConfig()):
        if role not in {"alice", "bob"}:
            raise ValueError("invalid endpoint role")
        self.role = role
        self.peer = "bob" if role == "alice" else "alice"
        self.config = config
        self.state = State.LOCKED
        self.connection = None
        self.generation = 0
        self.outbox = deque()
        self.seen = DuplicateCache(config.duplicate_cache)

    def transition(self, state):
        state = State(state)
        if state == self.state:
            return
        if state not in TRANSITIONS[self.state]:
            raise ConnectionFailure("invalid chat state transition")
        self.state = state
        if state != State.ACTIVE:
            self.generation += 1
            self.outbox.clear()

    def attach(self, connection):
        if self.state not in {State.CONNECTING, State.RECONNECTING}:
            raise ConnectionFailure("cannot attach session in current state")
        self.connection = connection
        self.transition(State.VERIFYING)

    def queue_chat(self, message):
        encode(message)
        if message["type"] != "chat" or message["sender"] != self.role or self.state != State.ACTIVE:
            raise ConnectionFailure("chat requires both verification approvals")
        if len(self.outbox) >= self.config.queue_size:
            raise ConnectionFailure("chat queue is full")
        self.outbox.append((self.generation, message))

    async def flush_one(self):
        if not self.outbox:
            return None
        generation, message = self.outbox.popleft()
        connection = self.connection
        await connection.send(encode(message), permitted=lambda: self.state == State.ACTIVE
                              and generation == self.generation and connection is self.connection)
        return message

    async def control(self, message):
        if message["type"] == "chat" or message["sender"] != self.role:
            raise ChatProtocolError()
        if self.connection is None or self.state in {State.LOCKED, State.CLOSED, State.RESTRICTED}:
            raise ConnectionFailure("control channel unavailable")
        await self.connection.send(encode(message))

    async def receive(self):
        connection, generation = self.connection, self.generation
        try:
            message = decode(await connection.receive())
            if message["sender"] != self.peer:
                raise ChatProtocolError()
            self.seen.accept(message["id"])
            if message["type"] == "chat" and (self.state != State.ACTIVE or generation != self.generation):
                return None
            return message
        except ChatProtocolError:
            self.transition(State.RESTRICTED)
            await connection.close()
            raise


class GuardAdapter:
    """SessionGuard's byte-transport gate becomes the coordinator's chat-only gate.

    Controls continue over the underlying framed transport during human comparison.
    Legacy SessionGuard callers continue using FramedConnection directly.
    """
    def __init__(self, coordinator):
        self.coordinator = coordinator

    @property
    def info(self):
        return self.coordinator.connection.info

    @property
    def metrics(self):
        return self.coordinator.connection.metrics

    def require_verification(self, required):
        if required and self.coordinator.state == State.ACTIVE:
            self.coordinator.transition(State.VERIFYING)
        # Only the dual-verification coordinator is allowed to open the chat gate.

    async def close(self):
        await self.coordinator.connection.close()
