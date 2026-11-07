"""Test advisory output triage without network or pnpm execution."""

import unittest

from scripts.goreecloud.report_pnpm_audit import parse_counts


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

    def test_incomplete_metadata_fails_closed(self) -> None:
        for report in ({}, [], {"metadata": {"vulnerabilities": {"high": 0}}}):
            with self.subTest(report=report), self.assertRaises(ValueError):
                parse_counts(report)

    def test_inconsistent_counts_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            parse_counts({"metadata": {"vulnerabilities": {
                "info": 0, "low": 0, "moderate": 0, "high": 2, "critical": 0,
                "total": 1,
            }}})


if __name__ == "__main__":
    unittest.main()
