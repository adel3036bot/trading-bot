"""Fail a staged-file scan when common credential shapes are detected.

Usage: python scripts/security_scan.py [FILES...]
With no files it scans staged files. Explicit file arguments support the
pre-stage safety check without scanning config.py or the live DB.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


PATTERNS = (
    re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{20,}\b"),  # Telegram bot token
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),      # Google API key
    re.compile(r"(?i)(?:api[_-]?key|token|password|secret)\s*=\s*[\"'][^\"']{12,}[\"']"),
)
SAFE_MARKERS = ("REPLACE_WITH_", "[REDACTED]", "<")


def staged_files() -> list[Path]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        check=True, capture_output=True, text=True,
    )
    return [Path(line) for line in result.stdout.splitlines() if line]


def main() -> int:
    findings: list[str] = []
    paths = [Path(argument) for argument in sys.argv[1:]] or staged_files()
    for path in paths:
        if not path.is_file() or path.suffix.lower() in {".db", ".pyc"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if any(marker in line for marker in SAFE_MARKERS):
                continue
            if any(pattern.search(line) for pattern in PATTERNS):
                findings.append(f"{path}:{line_number}")
    if findings:
        print("Potential secret patterns found in staged files:")
        print("\n".join(findings))
        return 1
    print("Security scan passed: no common credential shape found in staged files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
