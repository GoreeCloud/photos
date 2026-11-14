"""Lockfile regression: keep web SvelteKit above known affected 3.1.0.

A source baseline guard only; pnpm registry audit and web build remain required.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "web" / "package.json"
LOCK = ROOT / "pnpm-lock.yaml"


class SvelteKitAdvisoryBaselineTests(unittest.TestCase):
    def test_direct_web_dependency_requires_patched_sveltekit(self):
        package = json.loads(PACKAGE.read_text(encoding="utf-8"))
        declared = package["devDependencies"]["@sveltejs/kit"]
        match = re.fullmatch(r"\^3\.(\d+)\.(\d+)", declared)
        self.assertIsNotNone(match, "review unexpected SvelteKit dependency range")
        self.assertGreaterEqual((int(match[1]), int(match[2])), (1, 1))

    def test_lockfile_does_not_resolve_known_affected_sveltekit_310(self):
        source = LOCK.read_text(encoding="utf-8")
        self.assertNotIn("'@sveltejs/kit@3.1.0':", source)
        observed = re.findall(r"(?m)^  '@sveltejs/kit@3\.(\d+)\.(\d+)':\s*$", source)
        self.assertTrue(observed, "no pinned SvelteKit 3.x in public lockfile")
        for minor, patch in observed:
            self.assertGreaterEqual((int(minor), int(patch)), (1, 1))


if __name__ == "__main__":
    unittest.main()
