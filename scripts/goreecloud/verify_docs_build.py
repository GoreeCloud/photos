"""Check Docusaurus output existence without loading generated code or serving it."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    page = ROOT / "docs/build/index.html"
    if not page.is_file() or page.stat().st_size < 100:
        raise AssertionError("Docusaurus generated index.html missing/empty")
    html = page.read_text(encoding="utf-8", errors="replace").lower()
    if "<html" not in html or "<title" not in html:
        raise AssertionError("Generated documentation page lacks expected HTML scaffolding")
    print("PASS: imported docs static build produced an HTML shell. Not approved to deploy or rebrand.")


if __name__ == "__main__":
    main()
