"""Memory BIO drives the same OpenSSL TLS implementation without exporting keys."""

import ssl


class TLSChannel:
    def __init__(self, client_context, server_context, hostname="localhost"):
        self.c_in, self.c_out = ssl.MemoryBIO(), ssl.MemoryBIO()
        self.s_in, self.s_out = ssl.MemoryBIO(), ssl.MemoryBIO()
        self.client = client_context.wrap_bio(self.c_in, self.c_out, server_hostname=hostname)
        self.server = server_context.wrap_bio(self.s_in, self.s_out, server_side=True)

    def handshake(self):
        done = [False, False]
        for _ in range(30):
            for i, obj in enumerate((self.client, self.server)):
                if not done[i]:
                    try:
                        obj.do_handshake()
                        done[i] = True
                    except ssl.SSLWantReadError:
                        pass
            self.s_in.write(self.c_out.read())
            self.c_in.write(self.s_out.read())
            if all(done):
                return self
        raise AssertionError("TLS handshake did not complete")
