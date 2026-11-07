"""Check generated web output in an isolated build, without launching the app."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "web/static"
OUTPUT = ROOT / "web/build"
FILES = [
    "icon.svg",
    "favicon.ico",
    "goreecloud-photos-192.png",
    "goreecloud-photos-512.png",
    "apple-icon-180.png",
]


def main() -> None:
    index = OUTPUT / "index.html"
    if not index.is_file() or not index.read_text(encoding="utf-8").strip():
        raise AssertionError("SvelteKit static build index.html was not produced")
    actual = OUTPUT / "manifest.json"
    if not actual.is_file():
        raise AssertionError("Built PWA manifest missing")
    manifest = json.loads(actual.read_text(encoding="utf-8"))
    expected = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))
    if manifest != expected or manifest["name"] != "GoreeCloud Photos":
        raise AssertionError("Built PWA manifest differs from approved source")
    for name in FILES:
        origin = SOURCE / name
        built = OUTPUT / name
        if not built.is_file():
            raise AssertionError(f"Built static asset missing: {name}")
        digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        if digest(built) != digest(origin):
            raise AssertionError(f"Built asset differs from approved source: {name}")
    print(f"PASS: isolated web build emitted index, PWA manifest and {len(FILES)} verified first-party assets")


if __name__ == "__main__":
    main()
