"""Lockfile baseline for React Email's server-side glob advisory path.

Static evidence only; safe execution, pnpm audit and server compilation
remain independently required.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ReactEmailGlobBaselineTests(unittest.TestCase):
    def test_server_declares_patched_react_email_minimum(self):
        data = json.loads((ROOT / "server/package.json").read_text(encoding="utf-8"))
        required = data["dependencies"]["react-email"]
        match = re.fullmatch(r"\^6\.(\d+)\.(\d+)", required)
        self.assertIsNotNone(match, "review a new React Email major/minor contract")
        self.assertGreaterEqual((int(match[1]), int(match[2])), (11, 8))

    def test_locked_server_react_email_uses_glob_14(self):
        source = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        snapshot = re.search(
            r"(?m)^  react-email@6\.11\.8\([^\n]*\):\n(.*?)(?=\n\n)",
            source, flags=re.DOTALL,
        )
        self.assertIsNotNone(snapshot, "review changed package identity or lock graph")
        self.assertRegex(snapshot.group(1), r"(?m)^      glob: 14\.0\.[0-9]+$")
        self.assertNotIn("  react-email@6.11.5:", source)

    def test_no_new_release_age_policy_exception(self):
        policy = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        self.assertNotRegex(
            policy, r"(?m)^  - react-email@",
            "do not override dependency release-age protections to force a patch",
        )


if __name__ == "__main__":
    unittest.main()
