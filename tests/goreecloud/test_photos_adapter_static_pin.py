"""Source-only adapter-static security baseline; not production acceptance."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class AdapterStaticSecurityPinTests(unittest.TestCase):
    def test_web_requires_patched_static_adapter(self):
        package = json.loads((ROOT / "web/package.json").read_text(encoding="utf-8"))
        required = package["devDependencies"]["@sveltejs/adapter-static"]
        match = re.fullmatch(r"\^4\.(\d+)\.(\d+)", required)
        self.assertIsNotNone(match, "review adapter major API change")
        self.assertGreaterEqual((int(match[1]), int(match[2])), (0, 1))

    def test_pnpm_lock_resolves_patched_adapter(self):
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        self.assertNotIn("'@sveltejs/adapter-static@4.0.0':", lock)
        patches = re.findall(
            r"(?m)^  '@sveltejs/adapter-static@4\.(\d+)\.(\d+)':\s*$",
            lock,
        )
        self.assertTrue(patches, "no known patched adapter in pinned package graph")
        self.assertTrue(all((int(a), int(b)) >= (0, 1) for a, b in patches))

    def test_no_release_age_bypass(self):
        policy = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        self.assertNotRegex(policy, r"(?m)^  - '@sveltejs/adapter-static@")


if __name__ == "__main__":
    unittest.main()
