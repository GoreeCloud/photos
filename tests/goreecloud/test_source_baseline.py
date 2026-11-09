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
    "goreecloud-photos-logo.svg": "5955b3f5653f48302d18b1ffbd173b2adce1211d531b7f81da892f6e5bf2d6e0",
    "goreecloud-photos-logo-dark.svg": "f549bcb33ae0962bafa0d1e7e7bab635e42a54835e46999daff0bf97467be302",
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
    def test_undici_v8_redirect_cache_security_patch(self) -> None:
        workspace = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        script = (ROOT / "scripts/goreecloud/verify_undici_redirect_cache.cjs").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/goreecloud-e2e-typecheck.yml").read_text(encoding="utf-8")
        self.assertIn("'undici@8': 8.12.2", workspace)
        self.assertIn("undici@8: 8.12.2", lock)
        self.assertIn("  undici@8.12.2:\n    resolution:", lock)
        self.assertIn("  undici@8.12.2: {}", lock)
        self.assertNotIn("undici@8.11.2", lock)
        self.assertIn("undici: 8.12.2", lock)
        self.assertIn("127.0.0.1", script)
        self.assertIn("new cacheStores.MemoryCacheStore()", script)
        self.assertIn("interceptors.redirect", script)
        self.assertIn("synthetic-trusted-data", script)
        self.assertIn("timeout 15s node scripts/goreecloud/verify_undici_redirect_cache.cjs", workflow)

    def test_zod_v4_early_collection_size_security_patch(self) -> None:
        workspace = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        server = (ROOT / "server/package.json").read_text(encoding="utf-8")
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/goreecloud-server-build.yml").read_text(encoding="utf-8")
        script = (ROOT / "scripts/goreecloud/verify_zod_size_guards.cjs").read_text(encoding="utf-8")
        self.assertIn("  zod: 4.6.6", workspace)
        self.assertIn('"zod": "4.6.6"', server)
        self.assertIn("  zod@4.6.6:\n    resolution:", lock)
        self.assertIn("  zod@4.6.6: {}", lock)
        self.assertNotIn("zod@4.4.3", lock)
        self.assertIn("timeout 12s node scripts/goreecloud/verify_zod_size_guards.cjs", workflow)
        self.assertIn("Array(4096).fill", script)
        self.assertIn("elementChecks, 0", script)
        self.assertIn("z.set(z.string()).max(1)", script)
        self.assertIn("z.map(z.string(), z.string()).max(1)", script)

    def test_serializer_v7_security_patch_and_docs_smoke(self) -> None:
        workspace = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/goreecloud-docs-build.yml").read_text(encoding="utf-8")
        script = (ROOT / "scripts/goreecloud/verify_serializer_guards.cjs").read_text(encoding="utf-8")
        self.assertIn("'serialize-javascript@6': 7.1.3", workspace)
        self.assertIn("serialize-javascript@6: 7.1.3", lock)
        self.assertIn("  serialize-javascript@7.1.3:\n    resolution:", lock)
        self.assertIn("  serialize-javascript@7.1.3: {}", lock)
        self.assertNotIn("serialize-javascript@6.0.2", lock)
        self.assertIn("serialize-javascript: 7.1.3", lock)
        self.assertIn("fakeRegex.toJSON", script)
        self.assertIn("fakeDate.toISOString", script)
        self.assertIn("assert.throws", script)
        self.assertIn("spoofedFunction.toString", script)
        self.assertIn("mermaid: 11.16.1", workspace)
        self.assertIn("timeout 12s node scripts/goreecloud/verify_serializer_guards.cjs", workflow)

    def test_mermaid_security_patch_lock_consistent(self) -> None:
        workspace = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        self.assertIn("  mermaid: 11.16.1", workspace)
        self.assertIn("  mermaid: 11.16.1", lock)
        self.assertIn("  mermaid@11.16.1:\n    resolution:", lock)
        self.assertNotIn("mermaid@11.16.0", lock)

    def test_parser_moderate_advisory_versions_are_major_scoped(self) -> None:
        workspace = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        for item in ("'express@4>qs': 6.16.1", "  colord: 2.9.4",
                     "'postcss-selector-parser@6': 6.1.5",
                     "'postcss-selector-parser@7': 7.1.6"):
            self.assertIn(item, workspace)
        for item in ("  qs@6.16.1:\n", "  colord@2.9.4:\n",
                     "  postcss-selector-parser@6.1.5:\n",
                     "  postcss-selector-parser@7.1.6:\n",
                     "  brace-expansion@1.1.21:\n",
                     "  brace-expansion@2.1.7:\n",
                     "  brace-expansion@5.0.12:\n"):
            self.assertIn(item, lock)
        for old in ("qs@6.15.3", "colord@2.9.3",
                    "postcss-selector-parser@6.1.4",
                    "postcss-selector-parser@7.1.5",
                    "brace-expansion@1.1.20"):
            self.assertNotIn(old, lock)

    def test_parser_synthetic_security_smoke_is_hosted(self) -> None:
        workflow = (ROOT / ".github/workflows/goreecloud-docs-build.yml").read_text(encoding="utf-8")
        script = (ROOT / "scripts/goreecloud/verify_parser_guards.cjs").read_text(encoding="utf-8")
        self.assertIn("timeout 12s node scripts/goreecloud/verify_parser_guards.cjs", workflow)
        self.assertIn("maxRewrites: 0", script)
        self.assertIn("repeat(12000)", script)
        self.assertIn("arrayLimit: 1", script)
        self.assertIn("2.9.4", script)
        self.assertIn("postcss-selector-parser", script)
        self.assertNotIn("eval(", script)

    def test_scoped_ws_fragment_security_patch_is_consistent(self) -> None:
        workspace = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        smoke = (ROOT / "scripts/goreecloud/verify_ws_fragments.cjs").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/goreecloud-e2e-typecheck.yml").read_text(encoding="utf-8")
        self.assertIn("'engine.io-client>ws': 8.21.3", workspace)
        self.assertIn("engine.io-client>ws: 8.21.3", lock)
        self.assertNotIn("  ws@8.20.1:\n    resolution:", lock)
        self.assertIn("  ws@7.5.12:\n", lock)
        self.assertIn("  ws@8.21.3:\n", lock)
        self.assertIn("  ws@8.22.1:\n", lock)
        self.assertIn("maxFragments: 2", smoke)
        self.assertIn("WS_ERR_TOO_MANY_BUFFERED_PARTS", smoke)
        self.assertIn("ws@8.21.3", smoke)
        self.assertIn("timeout 12s node scripts/goreecloud/verify_ws_fragments.cjs", workflow)

    def test_e2e_native_timestamp_dependency_removal_is_consistent(self) -> None:
        manifest = (ROOT / "e2e/package.json").read_text(encoding="utf-8")
        test_source = (ROOT / "e2e/src/specs/server/api/library.e2e-spec.ts").read_text(encoding="utf-8")
        workspace = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        self.assertNotIn('"utimes":', manifest)
        self.assertNotIn("  utimes: false", workspace)
        self.assertIn("import { utimes } from 'node:fs/promises';", test_source)
        self.assertNotIn("from 'utimes';", test_source)
        self.assertEqual(test_source.count('await setFixtureMtime('), 5)
        self.assertIn("const time = new Date(timeMs);", test_source)
        self.assertNotIn("  utimes@5.2.1:", lock)
        self.assertNotIn("  tar@6.2.1:", lock)
        self.assertNotIn("  '@mapbox/node-pre-gyp@1.0.11", lock)
        self.assertIn("  tar@7.5.22:", lock)

    def test_isolated_e2e_typecheck_is_manual_and_least_privilege(self) -> None:
        workflow = (ROOT / ".github/workflows/goreecloud-e2e-typecheck.yml").read_text(encoding="utf-8")
        script = (ROOT / "scripts/goreecloud/verify_e2e_mtime.mjs").read_text(encoding="utf-8")
        self.assertIn("on:\n  workflow_dispatch:", workflow)
        self.assertNotIn("\n  push:", workflow)
        self.assertNotIn("\n  pull_request:", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("actions/checkout@" + CHECKOUT_SHA, workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("submodules: false", workflow)
        self.assertIn("pnpm install --frozen-lockfile --ignore-scripts", workflow)
        self.assertIn("pnpm --dir e2e run check", workflow)
        self.assertIn("timeout 12s node scripts/goreecloud/verify_e2e_mtime.mjs", workflow)
        self.assertIn("447_775_200_000, 447_775_200_001, 447_775_200_001", script)
        self.assertNotIn("docker compose", workflow)
        self.assertNotIn("pnpm --dir e2e run test", workflow)

    def test_immutable_v5_dos_patch_and_bounded_ci_smoke(self) -> None:
        workspace = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/goreecloud-docs-build.yml").read_text(encoding="utf-8")
        smoke = (ROOT / "scripts/goreecloud/verify_immutable_guards.cjs").read_text(encoding="utf-8")
        self.assertIn("  immutable: 5.1.8\n", workspace)
        self.assertIn("  immutable: 5.1.8\n", lock)
        self.assertIn("  immutable@5.1.8:\n    resolution:", lock)
        self.assertIn("  immutable@5.1.8: {}", lock)
        self.assertNotIn("immutable@5.1.6", lock)
        self.assertIn("timeout 12s node scripts/goreecloud/verify_immutable_guards.cjs", workflow)
        self.assertIn("List().set(2 ** 30, 'x')", smoke)
        self.assertIn("List([1, 2, 3]).setSize(2 ** 31)", smoke)
        self.assertIn("assert.equal(map.size, colliders.length)", smoke)
        self.assertIn("immutable@5.1.8", smoke)

    def test_image_size_v2_parser_patch_consistent(self) -> None:
        workspace = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        self.assertIn("  image-size: 2.0.4\n", workspace)
        self.assertIn("  image-size: 2.0.4\n", lock)
        self.assertIn("  image-size@2.0.4:\n    resolution:", lock)
        self.assertIn("  image-size@2.0.4: {}", lock)
        self.assertNotIn("image-size@2.0.2", lock)
        self.assertNotIn("image-size: 2.0.2", lock)

    def test_launch_editor_windows_security_patch_consistent(self) -> None:
        workspace = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        self.assertIn("  launch-editor: 2.14.2\n", workspace)
        self.assertIn("  launch-editor: 2.14.2\n", lock)
        self.assertIn("  launch-editor@2.14.2:\n    resolution:", lock)
        self.assertIn("  launch-editor@2.14.2:\n    dependencies:", lock)
        self.assertNotIn("launch-editor@2.14.1", lock)
        self.assertNotIn("launch-editor: 2.14.1", lock)
        self.assertIn("  shell-quote@1.11.0:\n", lock)

    def test_svgo_v3_security_patch_consistent(self) -> None:
        workspace = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        self.assertIn("  svgo: 3.3.5\n", workspace)
        self.assertIn("  svgo: 3.3.5\n", lock)
        self.assertIn("  svgo@3.3.5:\n    resolution:", lock)
        self.assertIn("  svgo@3.3.5:\n    dependencies:", lock)
        self.assertNotIn("svgo@3.3.4", lock)
        self.assertNotIn("svgo: 3.3.4", lock)

    def test_systeminformation_patch_consistent(self) -> None:
        workspace = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        self.assertIn("  systeminformation: 5.33.16\n", workspace)
        self.assertIn("  systeminformation: 5.33.16\n", lock)
        self.assertIn("  systeminformation@5.33.16:\n    resolution:", lock)
        self.assertIn("  systeminformation@5.33.16: {}", lock)
        self.assertNotIn("systeminformation@5.33.15", lock)
        self.assertNotIn("systeminformation: 5.33.15", lock)

    def test_body_parser_v1_patch_preserves_server_major_v2(self) -> None:
        workspace = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        self.assertIn("'body-parser@1': 1.20.9", workspace)
        self.assertIn("body-parser@1: 1.20.9", lock)
        self.assertIn("  body-parser@1.20.9:\n    resolution:", lock)
        self.assertNotIn("body-parser@1.20.6", lock)
        self.assertIn("  body-parser@2.4.0:\n    resolution:", lock)
        self.assertIn("      body-parser: 2.4.0(", lock)

    def test_joi_17_security_patch_is_lockfile_consistent(self) -> None:
        workspace = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        self.assertIn("  joi: 17.13.9\n", workspace)
        self.assertIn("  joi: 17.13.9\n", lock)
        self.assertIn("  joi@17.13.9:\n    resolution:", lock)
        self.assertIn("  joi@17.13.9:\n    dependencies:", lock)
        self.assertNotIn("joi@17.13.4", lock)
        self.assertNotIn("joi: 17.13.4", lock)
        self.assertIn("  follow-redirects@1.16.2:\n", lock)

    def test_follow_redirects_security_patch_is_lockfile_consistent(self) -> None:
        workspace = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        self.assertIn("  follow-redirects: 1.16.2\n", workspace)
        self.assertIn("  follow-redirects: 1.16.2\n", lock)
        self.assertIn("  follow-redirects@1.16.2:\n    resolution:", lock)
        self.assertIn("      follow-redirects: 1.16.2(", lock)
        self.assertNotIn("follow-redirects@1.16.0", lock)
        self.assertNotIn("follow-redirects: 1.16.0", lock)
        self.assertIn("  fast-uri@3.1.9:\n", lock)

    def test_brace_expansion_v1_scoped_patch_keeps_other_major_lines(self) -> None:
        import re
        workspace = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        pattern = r"(?m)^\s+['\\\"]?brace-expansion@1['\\\"]?: 1\.1\.21\s*$"
        self.assertRegex(workspace, pattern)
        self.assertRegex(lock, pattern)
        self.assertIn("  brace-expansion@1.1.21:\n", lock)
        self.assertNotIn("brace-expansion@1.1.15", lock)
        self.assertIn("  brace-expansion@2.1.7:\n", lock)
        self.assertIn("  brace-expansion@5.0.12:\n", lock)

    def test_tinypool_docs_security_patch_is_lockfile_consistent(self) -> None:
        workspace = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        self.assertIn("  tinypool: 2.2.0\n", workspace)
        self.assertIn("  tinypool: 2.2.0\n", lock)
        self.assertIn("  tinypool@2.2.0:\n", lock)
        self.assertIn("  tinypool@2.2.0: {}", lock)
        self.assertNotIn("tinypool@1.1.1", lock)
        self.assertNotIn("tinypool: 1.1.1", lock)

    def test_docs_leaf_security_overrides_are_lockfile_consistent(self) -> None:
        workspace = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        for name, old, new in (("dompurify", "3.4.12", "3.4.17"), ("shell-quote", "1.10.0", "1.11.0")):
            with self.subTest(package=name):
                self.assertIn("  " + name + ": " + new + "\n", workspace)
                self.assertIn("  " + name + ": " + new + "\n", lock)
                self.assertIn("  " + name + "@" + new + ":\n", lock)
                self.assertNotIn(name + "@" + old, lock)
                self.assertNotIn(name + ": " + old, lock)

    def test_fast_uri_security_override_and_lockfile_are_consistent(self) -> None:
        workspace = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        self.assertIn("  fast-uri: 3.1.9\n", workspace)
        self.assertIn("  fast-uri: 3.1.9\n", lock)
        self.assertIn("  fast-uri@3.1.9:\n    resolution:", lock)
        self.assertIn("      fast-uri: 3.1.9\n", lock)
        self.assertIn("  fast-uri@3.1.9: {}", lock)
        self.assertNotIn("fast-uri@3.1.4", lock)
        self.assertNotIn("fast-uri: 3.1.4", lock)

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
        self.assertEqual(active, {SOURCE_CHECK, "goreecloud-web-build.yml", "goreecloud-server-build.yml", "goreecloud-dependency-audit.yml", "goreecloud-docs-build.yml", "goreecloud-e2e-typecheck.yml", "goreecloud-multilang-supply-chain.yml"})
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

    def test_inherited_docs_build_is_manual_and_no_deployment(self) -> None:
        workflow = (ROOT / ".github/workflows/goreecloud-docs-build.yml").read_text(encoding="utf-8")
        self.assertIn("on:\n  workflow_dispatch:", workflow)
        self.assertNotIn("\n  push:", workflow)
        self.assertNotIn("\n  pull_request:", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("actions/checkout@" + CHECKOUT_SHA, workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("submodules: false", workflow)
        self.assertIn("pnpm install --frozen-lockfile --ignore-scripts", workflow)
        self.assertIn("pnpm --dir docs run build", workflow)
        self.assertIn("verify_docs_build.py", workflow)
        self.assertNotIn("docs run deploy", workflow)

    def test_dependency_advisory_preflight_is_manual_and_read_only(self) -> None:
        workflow = (ROOT / ".github/workflows/goreecloud-dependency-audit.yml").read_text(encoding="utf-8")
        self.assertIn("on:\n  workflow_dispatch:", workflow)
        self.assertNotIn("\n  pull_request:", workflow)
        self.assertNotIn("\n  push:", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("actions/checkout@" + CHECKOUT_SHA, workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("submodules: false", workflow)
        self.assertIn("pnpm audit --json", workflow)
        self.assertIn("pnpm audit --prod --json", workflow)
        self.assertNotIn("pnpm install", workflow)
        self.assertNotIn("audit --fix", workflow)
        self.assertIn("report_pnpm_audit.py", workflow)

    def test_isolated_server_build_is_manual_and_least_privilege(self) -> None:
        workflow = (ROOT / ".github/workflows/goreecloud-server-build.yml").read_text(encoding="utf-8")
        self.assertIn("on:\n  workflow_dispatch:", workflow)
        self.assertNotIn("\n  push:", workflow)
        self.assertNotIn("\n  pull_request:", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("actions/checkout@" + CHECKOUT_SHA, workflow)
        self.assertIn("actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("submodules: false", workflow)
        self.assertIn("pnpm install --frozen-lockfile --ignore-scripts", workflow)
        self.assertIn("pnpm --filter @immich/sdk run build", workflow)
        self.assertIn("pnpm --filter @immich/plugin-sdk run build", workflow)
        self.assertIn("pnpm --dir server run build", workflow)
        self.assertIn("python3 scripts/goreecloud/verify_server_build.py", workflow)
        self.assertIn("pnpm --dir e2e run check", workflow)
        self.assertIn("timeout 12s node scripts/goreecloud/verify_e2e_mtime.mjs", workflow)

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
        self.assertIn("python3 scripts/goreecloud/smoke_web_static_http.py", workflow)

    def test_loopback_http_static_asset_delivery_with_synthetic_page(self) -> None:
        import contextlib
        import importlib.util
        import io
        import tempfile

        smoke = ROOT / "scripts/goreecloud/smoke_web_static_http.py"
        source = smoke.read_text(encoding="utf-8")
        self.assertIn('("127.0.0.1", 0)', source)
        self.assertIn('urllib.request.ProxyHandler({})', source)
        spec = importlib.util.spec_from_file_location("goreecloud_photos_http_smoke", smoke)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory(prefix="goreecloud-static-http-") as root:
            out = Path(root)
            (out / "index.html").write_text("<!doctype html><html><body>synthetic shell</body></html>")
            (out / "manifest.json").write_bytes((WEB / "manifest.json").read_bytes())
            for name in ("icon.svg", "favicon.ico", "goreecloud-photos-192.png",
                         "goreecloud-photos-512.png", "apple-icon-180.png",
                         "goreecloud-photos-logo.svg", "goreecloud-photos-logo-dark.svg"):
                (out / name).write_bytes((WEB / name).read_bytes())
            mod.OUTPUT = out
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                mod.main()
            self.assertIn("PASS: loopback-only HTTP", captured.getvalue())

    def test_security_advisory_release_blocker_is_documented(self) -> None:
        gates = (ROOT / "docs/GOREECLOUD-RELEASE-GATES.md").read_text(encoding="utf-8")
        triage = (ROOT / "docs/GOREECLOUD-DEPENDENCY-TRIAGE-2026-11-07.md").read_text(encoding="utf-8")
        self.assertIn("GOREECLOUD-DEPENDENCY-TRIAGE-2026-11-07.md", gates)
        self.assertIn("release-blocking", triage)
        self.assertIn("42418292059", triage)
        self.assertIn("fast-uri 3.1.4", triage)
        self.assertIn("not a complete dependency", triage)

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

    def test_primary_web_brand_identity_surfaces_use_official_component(self) -> None:
        component = (ROOT / "web/src/lib/components/shared-components/GoreeCloudPhotosLogo.svelte").read_text()
        self.assertIn('src="/icon.svg"', component)
        self.assertIn('src="/goreecloud-photos-logo.svg"', component)
        self.assertIn('src="/goreecloud-photos-logo-dark.svg"', component)
        self.assertIn("dark:hidden", component)
        self.assertIn("dark:block", component)
        for path in (
            "web/src/lib/components/layouts/AuthPageLayout.svelte",
            "web/src/lib/components/shared-components/navigation-bar/NavigationBar.svelte",
            "web/src/routes/auth/onboarding/OnboardingHello.svelte",
            "web/src/routes/ErrorLayout.svelte",
            "web/src/lib/components/pages/SharedLinkPage.svelte",
        ):
            with self.subTest(path=path):
                text = (ROOT / path).read_text()
                self.assertIn("GoreeCloudPhotosLogo", text)
                self.assertNotIn("<Logo ", text)
        layout = (ROOT / "web/src/routes/+layout.svelte").read_text()
        self.assertIn(" - GoreeCloud Photos</title>", layout)
        self.assertNotIn(" - Immich</title>", layout)

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
