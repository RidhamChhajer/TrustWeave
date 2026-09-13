"""Local-only Windows entry point: python -m chat.app alice|bob --bundle PATH."""

import argparse
import asyncio
import json
from pathlib import Path
import socket
import ssl
import sys
import webbrowser

from chat.alice import AliceRuntime
from chat.bridge import create_app
from chat.bundles import inspect_bundle
from chat.config import ChatConfig
from chat.runtime import BobRuntime, private_addresses


def check_port(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            sock.bind((host, port))
    except OSError:
        raise ValueError("Required port is occupied. Stop the other chat/dashboard process and retry.") from None


def preflight(role, bundle, config):
    if sys.version_info < (3, 10) or not ssl.HAS_TLSv1_3:
        raise ValueError("Python 3.10 or newer with OpenSSL TLS 1.3 is required.")
    public = inspect_bundle(bundle, role)
    check_port("127.0.0.1", config.ui_port)
    if role == "bob":
        check_port("0.0.0.0", config.tls_port)
    addresses = private_addresses()
    return {"role": role, "python": sys.version.split()[0], "openssl": ssl.OPENSSL_VERSION,
            "ui_host": "127.0.0.1", "ui_port": config.ui_port, "tls_port": config.tls_port,
            "private_ipv4_candidates": addresses, "fingerprint": public["fingerprint"],
            "notice": None if addresses else "No private IPv4 found. Join the same private Wi-Fi before connecting."}


async def serve(runtime, open_browser=True):
    import uvicorn
    server = uvicorn.Server(uvicorn.Config(create_app(runtime), host="127.0.0.1", port=runtime.config.ui_port,
        ws="websockets-sansio", ws_max_size=32768, ws_max_queue=16, access_log=False,
        log_level="critical", proxy_headers=False, timeout_graceful_shutdown=3))
    task = asyncio.create_task(server.serve())
    try:
        for _ in range(100):
            if server.started or task.done():
                break
            await asyncio.sleep(0.05)
        if server.started:
            url = f"http://127.0.0.1:{runtime.config.ui_port}"
            print(f"Local chat ready: {url}. Press Ctrl+C to stop.", flush=True)
            if open_browser:
                webbrowser.open(url)
        await task
    finally:
        server.should_exit = True
        if not task.done():
            await task


def main(argv=None):
    parser = argparse.ArgumentParser(description="Two-device mutual-TLS LAN chat")
    parser.add_argument("role", choices=["alice", "bob"])
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--tls-port", type=int, default=8765)
    parser.add_argument("--ui-port", type=int, default=8766)
    parser.add_argument("--database", type=Path, default=Path(".state/chat-alice.db"))
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--check", action="store_true", help="Run read-only preflight and exit")
    args = parser.parse_args(argv)
    try:
        config = ChatConfig(tls_port=args.tls_port, ui_port=args.ui_port)
        evidence = preflight(args.role, args.bundle, config)
        print(json.dumps(evidence), flush=True)
        if args.check:
            return 0
        runtime = (AliceRuntime(args.bundle, config, args.database) if args.role == "alice"
                   else BobRuntime(args.bundle, config))
        asyncio.run(serve(runtime, not args.no_browser))
    except KeyboardInterrupt:
        return 0
    except Exception:
        print("Chat could not start safely. Check Python/dependencies, the role-specific bundle, and occupied ports.", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
