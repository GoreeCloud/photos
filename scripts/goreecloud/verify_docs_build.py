"""Read-only Docusaurus artifact inspection, not site/runtime acceptance."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs/build"


def main() -> None:
    index = OUTPUT / "index.html"
    if not index.is_file() or index.stat().st_size < 100:
        raise AssertionError("Expected nonempty docs/build/index.html was not generated")
    if not index.read_text(encoding="utf-8").strip().lower().startswith("<!doctype html"):
        raise AssertionError("Generated docs entry is not an HTML document")
    print("PASS: inherited Docusaurus static entry compiled without publishing")


if __name__ == "__main__":
    main()
