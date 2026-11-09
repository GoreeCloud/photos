"""Source-only regression checks for the non-executing supply-chain preflight."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/goreecloud/inspect_multilang_supply_chain.py"


def inspect():
    spec = importlib.util.spec_from_file_location("gc_lockfile_inspector", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.scan(ROOT)


class MultiEcosystemSourceIntegrity(unittest.TestCase):
    def test_static_lockfile_inventory_preserves_scope_and_known_blocker(self):
        report = inspect()
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["blockers"], 16)
        self.assertEqual(report["reviews"], 7)
        self.assertIn("NOT a vulnerability", report["scope"])
        self.assertEqual(report["totals"]["uv"]["packages"], 127)
        self.assertEqual(report["totals"]["cargo"]["registry_sources"], 108)
        self.assertEqual(report["totals"]["dart"]["mobile/pubspec.lock"]["source_types"]["git"], 5)
        self.assertEqual(report["totals"]["containers"]["dockerfiles"], 5)
        self.assertEqual(report["totals"]["containers"]["external_base_references"], 17)
        blockers = [finding for finding in report["findings"] if finding["level"] == "blocker"]
        self.assertTrue(all(finding["code"] == "uv-missing-artifact-hash" for finding in blockers))
        self.assertEqual({finding["location"] for finding in blockers},
                         {"machine-learning/uv.lock:openvino"})

    def test_enforcement_is_fail_closed_and_never_installs_packages(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--enforce"], cwd=ROOT,
            capture_output=True, text=True, timeout=8, check=False,
        )
        self.assertEqual(completed.returncode, 2, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["blockers"], 16)

    def test_disposable_ci_is_manual_read_only_and_no_dependency_execution(self):
        workflow = (ROOT / ".github/workflows/goreecloud-multilang-supply-chain.yml").read_text()
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertNotIn("\n  push:", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("submodules: false", workflow)
        self.assertIn("actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683", workflow)
        self.assertIn("python3 scripts/goreecloud/inspect_multilang_supply_chain.py --enforce", workflow)
        self.assertNotIn("pip install", workflow)
        self.assertNotIn("cargo install", workflow)
        self.assertNotIn("flutter pub get", workflow)


if __name__ == "__main__":
    unittest.main()
