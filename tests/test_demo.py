"""Behavior tests for the interactive file-type demo."""

import asyncio
from pathlib import Path

from textual.widgets import DataTable, Input, Static

from filetype_detector import FileType
from filetype_detector.demo import (
    FileTypeDemo,
    StrategyResult,
    discover_files,
)


def test_discover_files_is_sorted_hidden_safe_and_bounded(tmp_path: Path) -> None:
    (tmp_path / "nested").mkdir()
    (tmp_path / ".hidden").mkdir()
    (tmp_path / "alpha.txt").write_text("alpha")
    (tmp_path / "nested" / "beta.pdf").write_bytes(b"%PDF")
    (tmp_path / "zeta.png").write_bytes(b"png")
    (tmp_path / ".hidden" / "secret.txt").write_text("secret")

    discovery = discover_files(tmp_path, limit=2)

    assert [path.relative_to(tmp_path).as_posix() for path in discovery.paths] == [
        "alpha.txt",
        "nested/beta.pdf",
    ]
    assert discovery.truncated is True


def test_discover_files_caps_directory_entry_scanning(tmp_path: Path) -> None:
    for index in range(1_001):
        (tmp_path / f"empty-{index:04d}").mkdir()

    discovery = discover_files(tmp_path, limit=1)

    assert discovery.paths == ()
    assert discovery.truncated is True


def test_live_filter_and_selection_show_inference_details(tmp_path: Path) -> None:
    report = tmp_path / "report.pdf"
    report.write_bytes(b"%PDF")
    (tmp_path / "notes.txt").write_text("notes")
    (tmp_path / "image.png").write_bytes(b"png")

    def infer(path: Path) -> tuple[StrategyResult, ...]:
        assert path == report
        return (
            StrategyResult(
                backend="magic",
                file_type=FileType(
                    extensions=(".pdf",),
                    mime_types=("application/pdf",),
                ),
            ),
        )

    async def exercise() -> None:
        app = FileTypeDemo(tmp_path, inference_runner=infer)
        async with app.run_test(size=(120, 38)) as pilot:
            filter_input = app.query_one("#filter", Input)
            assert filter_input.has_focus

            await pilot.press("p", "d", "f")
            await pilot.pause()

            table = app.query_one("#files", DataTable)
            assert table.row_count == 1
            assert app.filtered_paths == (report,)

            await pilot.press("tab", "enter")
            await app.workers.wait_for_complete()

            details = app.query_one("#details", Static)
            rendered_details = str(details.render())
            assert "MAGIC" in rendered_details
            assert ".pdf" in rendered_details
            assert "application/pdf" in rendered_details

    asyncio.run(exercise())
