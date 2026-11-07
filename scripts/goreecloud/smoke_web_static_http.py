"""Loopback-only GET/HEAD contract for generated Photos web static artifacts.

No app server, user data, cookies, external domains, or browser JavaScript is loaded.
"""

from __future__ import annotations

import functools
import http.server
import json
import threading
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "web/build"
MAX_RESPONSE = 5_000_000
NO_PROXY_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


def request(base: str, path: str, method: str = "GET") -> tuple[bytes, str]:
    req = urllib.request.Request(base + path, method=method)
    with NO_PROXY_OPENER.open(req, timeout=8) as response:
        if response.status != 200:
            raise AssertionError(f"Unexpected {response.status} for {path}")
        data = response.read(MAX_RESPONSE + 1)
        if len(data) > MAX_RESPONSE:
            raise AssertionError(f"Oversized test response: {path}")
        return data, response.headers.get_content_type()


def main() -> None:
    if not OUTPUT.is_dir():
        raise AssertionError("web/build does not exist; run the isolated web compile first")
    handler = functools.partial(QuietHandler, directory=str(OUTPUT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        html, content_type = request(base, "/")
        if content_type != "text/html" or b"<html" not in html.lower():
            raise AssertionError("Static page shell is not served as HTML")
        pwa_bytes, pwa_type = request(base, "/manifest.json")
        if pwa_type != "application/json":
            raise AssertionError("PWA manifest not served as JSON")
        if pwa_bytes != (OUTPUT / "manifest.json").read_bytes():
            raise AssertionError("HTTP manifest differs from built file")
        manifest = json.loads(pwa_bytes)
        if manifest.get("name") != "GoreeCloud Photos":
            raise AssertionError("HTTP PWA identity is incorrect")
        files = (
            "icon.svg", "favicon.ico", "goreecloud-photos-192.png",
            "goreecloud-photos-512.png", "apple-icon-180.png",
            "goreecloud-photos-logo.svg", "goreecloud-photos-logo-dark.svg",
        )
        for name in files:
            data, mime = request(base, "/" + name)
            if data != (OUTPUT / name).read_bytes():
                raise AssertionError(f"HTTP asset differs from build: {name}")
            if name.endswith(".png") and mime != "image/png":
                raise AssertionError(f"PNG not served with correct type: {name}")
            if name.endswith(".svg") and mime != "image/svg+xml":
                raise AssertionError(f"SVG not served with correct type: {name}")
            head_bytes, _ = request(base, "/" + name, method="HEAD")
            if head_bytes:
                raise AssertionError(f"HEAD unexpectedly has a response body: {name}")
        print(f"PASS: loopback-only HTTP GET/HEAD for static HTML, PWA manifest and {len(files)} branded assets")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


if __name__ == "__main__":
    main()
