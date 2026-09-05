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
        [sys.executable, str(_ROOT / ".audit/generate_fixture_coverage_table.py")],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    rows = (_ROOT / ".audit/fixture-coverage-table.csv").read_text().splitlines()
    assert len(rows) == 607
