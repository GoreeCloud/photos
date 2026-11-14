"""Test advisory output triage without network or pnpm execution."""

import unittest

from scripts.goreecloud.report_pnpm_audit import advisory_examples, parse_counts


class AuditParseTests(unittest.TestCase):
    def test_zero_counts_are_valid(self) -> None:
        counts = parse_counts({"metadata": {"vulnerabilities": {
            "info": 0, "low": 0, "moderate": 0, "high": 0, "critical": 0,
            "total": 0,
        }}})
        self.assertEqual(sum(counts.values()), 0)

    def test_known_advisories_are_not_silently_dropped(self) -> None:
        counts = parse_counts({"metadata": {"vulnerabilities": {
            "info": 0, "low": 2, "moderate": 1, "high": 3, "critical": 1,
            "total": 7,
        }}})
        self.assertEqual(counts["critical"] + counts["high"], 4)

    def test_advisory_samples_are_bounded_and_sanitized(self) -> None:
        reports = {"advisories": {
            "a": {"severity": "critical", "module_name": "image-parser", "github_advisory_id": "GHSA-1111-2222-3333", "patched_versions": ">=2"},
            "b": {"severity": "high", "module_name": "foo\\nINJECT", "id": 123, "patched_versions": "<2"},
            "c": {"severity": "moderate", "module_name": "bar"},
        }}
        rows = advisory_examples(reports, limit=2)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], "critical")
        self.assertNotIn("\\n", rows[1][1])

    def test_moderate_and_low_findings_remain_visible_without_highs(self) -> None:
        report = {"advisories": {
            "low": {"severity": "low", "module_name": "media-codec", "github_advisory_id": "GHSA-4444-5555-6666"},
            "moderate": {"severity": "moderate", "module_name": "xml-loader", "github_advisory_id": "GHSA-7777-8888-9999"},
            "info": {"severity": "info", "module_name": "info-package"},
        }}
        rows = advisory_examples(report)
        self.assertEqual([row[0] for row in rows], ["moderate", "low", "info"])
        self.assertEqual(rows[0][1], "xml-loader")
        self.assertEqual(len(advisory_examples(report, limit=1)), 1)

    def test_lower_severity_samples_still_sanitize_log_injection(self) -> None:
        rows = advisory_examples({"advisories": [{
            "severity": "moderate",
            "module_name": "safe\\n::error::forged",
            "github_advisory_id": "GHSA-ABCD-1234-5678",
            "patched_versions": ">=1.2"
        }]})
        self.assertEqual(len(rows), 1)
        self.assertNotIn("\\n", rows[0][1])
        self.assertNotIn(":", rows[0][1])

    def test_incomplete_metadata_fails_closed(self) -> None:
        for report in ({}, [], {"metadata": {"vulnerabilities": {"high": 0}}}):
            with self.subTest(report=report), self.assertRaises(ValueError):
                parse_counts(report)

    def test_missing_or_overstated_total_fails_closed(self) -> None:
        severities = {"info": 0, "low": 0, "moderate": 0, "high": 0, "critical": 0}
        for total in (None, True, "0", -1, 1):
            with self.subTest(total=total), self.assertRaises(ValueError):
                parse_counts({"metadata": {"vulnerabilities": {**severities, "total": total}}})
        with self.assertRaises(ValueError):
            parse_counts({"metadata": {"vulnerabilities": severities}})

    def test_inconsistent_counts_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            parse_counts({"metadata": {"vulnerabilities": {
                "info": 0, "low": 0, "moderate": 0, "high": 2, "critical": 0,
                "total": 1,
            }}})


if __name__ == "__main__":
    unittest.main()
