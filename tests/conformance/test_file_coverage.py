"""Regression tests for the separate fixture coverage report."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


_ROOT = Path(__file__).parents[2]


# Q. Does the checked-in file coverage report match inventory and validators?
def test_file_coverage_report_is_current() -> None:
    result = subprocess.run(
        [sys.executable, str(_ROOT / ".audit/coverage-report.py"), "--check"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


# Q. Does the complete fixture table stay synchronized with candidate inventory?
def test_complete_fixture_table_is_current() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(_ROOT / ".audit/generate_fixture_coverage_table.py"),
            "--check",
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    import csv
    import json

    rows = list(
        csv.DictReader(
            (_ROOT / ".audit/fixture-coverage-table.csv").open(
                encoding="utf-8", newline=""
            )
        )
    )
    candidates = json.loads(
        (_ROOT / "tests/truth/backend_inventory_candidates.json").read_text(
            encoding="utf-8"
        )
    )["records"]
    assert len(rows) == len(candidates)
    assert {row["id"] for row in rows} == {record["id"] for record in candidates}


# Q. Does the full corpus audit artifact match current inventory/matrix data?
def test_full_corpus_audit_is_current() -> None:
    result = subprocess.run(
        [sys.executable, str(_ROOT / ".audit/full-corpus-audit.py"), "--check"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
