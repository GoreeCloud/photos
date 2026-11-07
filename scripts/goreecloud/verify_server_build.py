"""Offline inspection of compiled Nest server; never start services or inspect user media."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def main() -> None:
    sdk = ROOT / "packages/sdk/build/index.js"
    plugin = ROOT / "packages/plugin-sdk/dist/index.js"
    main = ROOT / "server/dist/main.js"
    for file in (sdk, plugin, main):
        if not file.is_file() or file.stat().st_size < 50:
            raise AssertionError(f"Expected nonempty build output missing: {file.relative_to(ROOT)}")
        # Importing these modules could run server setup or load backend APIs.
        # Inspection is deliberately static and does not evaluate JS contents.
    print("PASS: isolated SDK, plugin SDK and Nest server outputs exist and are nonempty. No service started.")

if __name__ == "__main__":
    main()
