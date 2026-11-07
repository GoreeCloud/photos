"""Read-only source, attribution and first-party branding acceptance for GoreeCloud Photos.

These tests intentionally do NOT import, compile, install or execute upstream Immich code.
They require only Python's standard library and Git's read-only index inspection.
"""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web" / "static"
UPSTREAM_SHA = "87ef895041e160aef4f61f2d7af1ad3f8e38827d"
PINNED_FILES = {
    "LICENSE": "a3bad629f67f442b23b5224419e49edafc32e6b9c876b89464f7aafe6091ccde",
    "docs/UPSTREAM-README.md": "b37199a0b7b52d1a6a62c97d6ad1a4eea18f367b8f8dad378ac9a0926f351a34",
}
BRAND_ASSET_HASHES = {
    "icon.svg": "cedeb508dc4a68875bfd40d495ae38ef9869bf615c0b02d4e2b569b6473bb3fb",
    "favicon.ico": "e2f8f74c7ec727ca52759dd973560346a89fee1764d827e77ee79577c556e0b8",
    "goreecloud-photos-192.png": "33ca452348119cfc3e085362084a7a4425a55159f989170a801a2d1bf08562bf",
    "goreecloud-photos-512.png": "03f9c527e95ab553a9b54cc1943743a8bba2e3757835b61befa3fe0c1dddfa19",
    "apple-icon-180.png": "b151decee7e040ec32e3f3d07e427415f2a1738766a4bc918b45fd4e08f334f2",
}
SOURCE_CHECK = "goreecloud-source-checks.yml"
CHECKOUT_SHA = "11bd71901bbe5b1630ceea73d27597364c9af683"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise AssertionError(f"Not a PNG: {path}")
    return struct.unpack(">II", data[16:24])


class SourceBaselineTests(unittest.TestCase):
    def test_license_and_original_readme_are_unmodified(self) -> None:
        for path, digest in PINNED_FILES.items():
            with self.subTest(path=path):
                self.assertEqual(sha256(ROOT / path), digest)

    def test_provenance_identifies_upstream_and_unreleased_state(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        provenance = (ROOT / "docs/GOREECLOUD-IMPORT-PROVENANCE.md").read_text(encoding="utf-8")
        self.assertIn("# GoreeCloud Photos", readme)
        self.assertIn("Rebranded Import", readme)
        self.assertIn("Not deployed or production-ready", readme)
        self.assertIn("AGPL-3.0", readme)
        self.assertIn("https://github.com/immich-app/immich", provenance)
        self.assertIn(UPSTREAM_SHA, readme)
        self.assertIn(UPSTREAM_SHA, provenance)

    def test_inherited_actions_remain_inert(self) -> None:
        archive = ROOT / "docs/upstream-github-workflows"
        archived = sorted(p for p in archive.iterdir() if p.is_file())
        self.assertEqual(len(archived), 27)
        self.assertTrue(all(p.suffix in {".yml", ".yaml"} for p in archived))
        active = {p.name for p in (ROOT / ".github/workflows").iterdir() if p.is_file()}
        self.assertEqual(active, {SOURCE_CHECK, "goreecloud-web-build.yml"})
        self.assertTrue((ROOT / "docs/UPSTREAM-CODEOWNERS").is_file())
        self.assertFalse((ROOT / "CODEOWNERS").exists())

    def test_unreviewed_upstream_repository_controls_are_quarantined(self) -> None:
        quarantined = ROOT / "docs/upstream-repository-controls"
        expected = {
            "renovate.json", "ISSUE_TEMPLATE/bug_report.yaml",
            "ISSUE_TEMPLATE/config.yml", "DISCUSSION_TEMPLATE/feature-request.yaml",
            "PULL_REQUEST_TEMPLATE/config.yml", "pull_request_template.md",
            "release.yml", "labeler.yml",
        }
        actual = {str(path.relative_to(quarantined)) for path in quarantined.rglob("*") if path.is_file()}
        self.assertEqual(actual, expected)
        self.assertFalse((ROOT / "renovate.json").exists())
        self.assertFalse((ROOT / ".github/release.yml").exists())
        self.assertFalse((ROOT / ".github/labeler.yml").exists())
        self.assertFalse((ROOT / ".github/ISSUE_TEMPLATE/bug_report.yaml").exists())
        self.assertIn("# Contributing to GoreeCloud Photos", (ROOT / "CONTRIBUTING.md").read_text())
        self.assertTrue((ROOT / "docs/UPSTREAM-CONTRIBUTING.md").is_file())

    def test_isolated_web_build_is_manual_and_least_privilege(self) -> None:
        workflow = (ROOT / ".github/workflows/goreecloud-web-build.yml").read_text(encoding="utf-8")
        self.assertIn("on:\n  workflow_dispatch:", workflow)
        self.assertNotIn("\n  pull_request:", workflow)
        self.assertNotIn("\n  push:", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020", workflow)
        self.assertIn("actions/checkout@" + CHECKOUT_SHA, workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("submodules: false", workflow)
        self.assertIn("pnpm install --frozen-lockfile --ignore-scripts", workflow)
        self.assertIn("pnpm --filter @immich/sdk run build", workflow)
        self.assertIn("python3 scripts/goreecloud/verify_web_build.py", workflow)

    def test_deployment_env_contains_only_secret_manager_references(self) -> None:
        # Prevent accidental future substitution of literal credentials into this
        # tracked upstream deployment file; the file is never sourced/executed.
        env = (ROOT / "deployment/.env").read_text(encoding="utf-8")
        keys = ("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN", "TF_STATE_POSTGRES_CONN_STR")
        for key in keys:
            with self.subTest(key=key):
                matches = [line for line in env.splitlines() if line.startswith("export " + key + "=")]
                self.assertEqual(len(matches), 1)
                value = matches[0].split("=", 1)[1].strip().strip("'\\\"")
                self.assertTrue(value.startswith("op://"), "tracked deployment credential must be secret-manager reference")
        self.assertIn("export TF_VAR_env=", env)

    def test_brand_and_release_gate_documents_exist(self) -> None:
        brand = (ROOT / "docs/GOREECLOUD-BRAND-ADOPTION.md").read_text()
        gates = (ROOT / "docs/GOREECLOUD-RELEASE-GATES.md").read_text()
        self.assertIn("3231d720b1ae17a2c49f4d58e98c60acd331118a", brand)
        self.assertIn("GoreeCloud Photos", brand)
        self.assertIn("not deployed", gates)
        self.assertIn("GoreeShield", gates)
        self.assertIn("Wardveil", gates)
        self.assertIn("GoreeCloud Mesh", gates)

    def test_static_ci_is_read_only_and_pinned(self) -> None:
        workflow = (ROOT / ".github/workflows" / SOURCE_CHECK).read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("actions/checkout@" + CHECKOUT_SHA, workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("submodules: false", workflow)
        self.assertIn('python3 -m unittest discover -s tests/goreecloud', workflow)
        self.assertEqual(workflow.count("uses:"), 1)

    def test_upstream_test_assets_gitlink_is_preserved(self) -> None:
        result = subprocess.run(
            ["git", "ls-files", "--stage", "--", "e2e/test-assets"],
            cwd=ROOT, capture_output=True, text=True, check=True, timeout=10
        )
        self.assertRegex(
            result.stdout,
            r"^160000 6742055402de1aa48f93d12ded7d18f4057f9d1f 0\te2e/test-assets\n$",
        )

    def test_web_manifest_and_icons_use_first_party_art(self) -> None:
        manifest = json.loads((WEB / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "GoreeCloud Photos")
        self.assertEqual(manifest["short_name"], "Photos")
        self.assertEqual(len(manifest["icons"]), 2)
        expected = [(192, "goreecloud-photos-192.png"), (512, "goreecloud-photos-512.png")]
        for icon, (size, filename) in zip(manifest["icons"], expected, strict=True):
            with self.subTest(icon=filename):
                self.assertEqual(icon["src"], filename)
                self.assertEqual(icon["sizes"], f"{size}x{size}")
                self.assertEqual(icon["purpose"], "any")
                self.assertEqual(icon["type"], "image/png")
                self.assertEqual(png_dimensions(WEB / filename), (size, size))
        self.assertEqual(png_dimensions(WEB / "apple-icon-180.png"), (180, 180))
        for old in ("manifest-icon-192.maskable.png", "manifest-icon-512.maskable.png"):
            self.assertFalse((WEB / old).exists(), old)

    def test_brand_asset_byte_integrity(self) -> None:
        for path, digest in BRAND_ASSET_HASHES.items():
            with self.subTest(path=path):
                self.assertEqual(sha256(WEB / path), digest)
        icon = (WEB / "icon.svg").read_text(encoding="utf-8")
        self.assertIn('aria-label="GoreeCloud Photos"', icon)

    def test_browser_fallback_and_reference_paths(self) -> None:
        app = (ROOT / "web/src/app.html").read_text(encoding="utf-8")
        self.assertIn("To use GoreeCloud Photos, you must enable JavaScript", app)
        self.assertIn('href="/icon.svg"', app)
        self.assertIn('href="/favicon.ico"', app)
        self.assertIn('href="/apple-icon-180.png"', app)


if __name__ == "__main__":
    unittest.main()
