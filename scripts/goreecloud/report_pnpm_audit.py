"""Conservative summary of pnpm audit JSON. Never infer safety on incomplete data."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


SEVERITIES = ("info", "low", "moderate", "high", "critical")


def parse_counts(report: object) -> dict[str, int]:
    if not isinstance(report, dict):
        raise ValueError("audit response is not a JSON object")
    metadata = report.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("audit metadata is absent")
    vuln = metadata.get("vulnerabilities")
    if not isinstance(vuln, dict):
        raise ValueError("audit vulnerability counts are absent")
    counts: dict[str, int] = {}
    for level in SEVERITIES:
        n = vuln.get(level)
        if type(n) is not int or n < 0:
            raise ValueError(f"audit count invalid for {level}")
        counts[level] = n
    total = vuln.get("total")
    if type(total) is int and total < sum(counts.values()):
        raise ValueError("audit total is lower than severity totals")
    return counts



def advisory_examples(report: object, limit: int = 12) -> list[tuple[str, str, str, str]]:
    if not isinstance(report, dict):
        return []
    raw = report.get("advisories", {})
    if isinstance(raw, dict):
        entries = raw.values()
    elif isinstance(raw, list):
        entries = raw
    else:
        return []
    out: list[tuple[str, str, str, str]] = []
    def safe(value: object) -> str:
        if not isinstance(value, (str, int)):
            return "unspecified"
        return re.sub(r"[^A-Za-z0-9@/_.+<>~=* -]", "_", str(value))[:90]
    for item in entries:
        if not isinstance(item, dict) or item.get("severity") not in ("critical", "high"):
            continue
        out.append((
            safe(item.get("severity")),
            safe(item.get("module_name") or item.get("name")),
            safe(item.get("github_advisory_id") or item.get("id")),
            safe(item.get("patched_versions")),
        ))
    out.sort(key=lambda row: (0 if row[0] == "critical" else 1, row[1], row[2]))
    return out[:limit]

def main(argv: list[str]) -> int:
    if len(argv) != 4 or argv[3] not in ("full", "production"):
        print("usage: report_pnpm_audit.py REPORT_JSON AUDIT_EXIT_CODE SCOPE", file=sys.stderr)
        return 2
    path = Path(argv[1])
    try:
        code = int(argv[2])
        if not path.is_file() or path.stat().st_size > 15_000_000:
            raise ValueError("audit report absent or oversized")
        report = json.loads(path.read_text(encoding="utf-8"))
        counts = parse_counts(report)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"UNVERIFIED: pnpm audit output cannot be accepted: {type(exc).__name__}", file=sys.stderr)
        return 2
    print(f"pnpm advisory counts ({argv[3]} dependency scope):")
    for name in SEVERITIES:
        print(f"  {name}: {counts[name]}")
    examples = advisory_examples(report)
    if examples:
        print("Critical/high advisory samples (package, GHSA/id, patched range; not exhaustive):")
        for severity, package, advisory_id, patch in examples:
            print(f"  {severity}: {package}, {advisory_id}, patch={patch}")
    if code != 0:
        print(f"AUDIT NOT CLEAR: pnpm exited nonzero ({code}). Findings or service errors require triage.")
        return 1
    if sum(counts.values()):
        print("AUDIT NOT CLEAR: pnpm claimed success but reports advisory findings.")
        return 1
    print("No advisories returned by pnpm registry query at scan time. Not a full supply-chain/security clearance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
