"""Two independent human decisions bound to one authenticated relationship."""

import asyncio

from chat.protocol import ChatProtocolError, _hex


def safety_code(relationship):
    if not _hex(relationship, 64):
        raise ChatProtocolError()
    return " ".join(relationship[i:i + 8].upper() for i in range(0, 64, 8))


class DualVerification:
    def __init__(self, request_id, relationship, reason, recovery=False):
        if not _hex(request_id):
            raise ChatProtocolError()
        self.id, self.relationship, self.reason, self.recovery = request_id, relationship, reason, recovery
        self.code = safety_code(relationship)
        self.decisions = {}
        self.ready = asyncio.get_running_loop().create_future()

    def decide(self, role, request_id, relationship, decision):
        if (request_id != self.id or relationship != self.relationship or role not in {"alice", "bob"}
            or role in self.decisions or decision not in {"MATCH", "MISMATCH", "CANCEL"}):
            self.fail()
            raise ChatProtocolError()
        self.decisions[role] = decision
        if decision != "MATCH":
            self.fail()
        elif len(self.decisions) == 2 and not self.ready.done():
            self.ready.set_result(True)

    def fail(self):
        if not self.ready.done():
            self.ready.set_result(False)

    def snapshot(self, role):
        return {"id": self.id, "code": self.code, "reason": self.reason,
                "local_decision": self.decisions.get(role), "recovery": self.recovery}
