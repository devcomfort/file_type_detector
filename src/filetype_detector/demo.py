"""Textual interface for exploring file-type inference strategies."""

from __future__ import annotations

import os
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.worker import get_current_worker
from textual.widgets import DataTable, Footer, Header, Input, Static

from .auto_inferencer import AutoInferencer, BackendType
from .core import FileType

_DEFAULT_LIMIT = 1_000
_MIN_SCAN_ENTRIES = 1_000
_SCAN_ENTRIES_PER_FILE = 20
_BACKENDS: tuple[BackendType, ...] = ("lexical", "magic", "magika", "hybrid")


@dataclass(frozen=True)
class DiscoveryResult:
    """Visible files discovered beneath a root directory."""

    paths: tuple[Path, ...]
    truncated: bool


@dataclass(frozen=True)
class StrategyResult:
    """Outcome from one inference backend."""

    backend: str
    file_type: FileType | None = None
    error: str | None = None


InferenceRunner = Callable[[Path], Sequence[StrategyResult]]


def discover_files(root: Path, limit: int = _DEFAULT_LIMIT) -> DiscoveryResult:
    """Find visible, non-symlink files while enforcing scan limits.

    Results use path order unless the directory-entry cap is reached; capped
    results follow the filesystem's available entry order. At most
    ``max(1_000, limit * 20)`` directory entries and ``limit + 1`` files are
    retained. Dot-prefixed paths and symlinks are omitted.
    """
    if limit < 1:
        raise ValueError("limit must be at least 1")

    root = root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")

    discovered: list[Path] = []
    stack: list[tuple[Path, bool]] = [(root, True)]
    entry_budget = max(_MIN_SCAN_ENTRIES, limit * _SCAN_ENTRIES_PER_FILE)
    entries_examined = 0
    scan_truncated = False

    while stack and len(discovered) <= limit:
        path, is_directory = stack.pop()
        if not is_directory:
            discovered.append(path)
            continue

        if scan_truncated or entries_examined >= entry_budget:
            scan_truncated = True
            continue

        try:
            with os.scandir(path) as iterator:
                children: list[tuple[Path, bool]] = []
                for entry in iterator:
                    if entries_examined >= entry_budget:
                        scan_truncated = True
                        break
                    entries_examined += 1
                    if entry.name.startswith(".") or entry.is_symlink():
                        continue
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            children.append((Path(entry.path), True))
                        elif entry.is_file(follow_symlinks=False):
                            children.append((Path(entry.path), False))
                    except OSError:
                        continue
        except OSError:
            continue

        children.sort(key=lambda item: item[0].name.casefold(), reverse=True)
        stack.extend(children)

    return DiscoveryResult(
        paths=tuple(discovered[:limit]),
        truncated=len(discovered) > limit or scan_truncated,
    )


class DefaultInferenceRunner:
    """Lazily reuse inferencers while serializing access to their models."""

    def __init__(self) -> None:
        self._inferencers: dict[BackendType, AutoInferencer] = {}
        self._lock = threading.Lock()

    def __call__(self, path: Path) -> tuple[StrategyResult, ...]:
        results: list[StrategyResult] = []
        with self._lock:
            for backend in _BACKENDS:
                try:
                    inferencer = self._inferencers.get(backend)
                    if inferencer is None:
                        inferencer = AutoInferencer(backend)
                        self._inferencers[backend] = inferencer
                    results.append(
                        StrategyResult(
                            backend=backend,
                            file_type=inferencer.infer(path),
                        )
                    )
                except Exception as error:
                    results.append(
                        StrategyResult(
                            backend=backend,
                            error=f"{type(error).__name__}: {error}",
                        )
                    )
        return tuple(results)


class FileTypeDemo(App[None]):
    """Interactive browser for comparing all bundled inference backends."""

    TITLE = "FILETYPE DETECTOR"
    SUB_TITLE = "interactive strategy explorer"

    CSS = """
    Screen {
        background: #071116;
        color: #d9e5e8;
    }

    Header {
        background: #0d2028;
        color: #e9f8fa;
    }

    #shell {
        padding: 1 2;
    }

    .eyebrow {
        height: 1;
        color: #68d5cf;
        text-style: bold;
    }

    #filter {
        margin: 1 0;
        border: tall #31545e;
        background: #0a191f;
    }

    #filter:focus {
        border: tall #68d5cf;
    }

    #status {
        height: 1;
        margin-bottom: 1;
        color: #89a8af;
    }

    #workspace {
        height: 1fr;
    }

    .panel {
        height: 1fr;
        border: round #29464f;
        background: #0a171d;
    }

    #file-pane {
        width: 58%;
        margin-right: 1;
    }

    #detail-pane {
        width: 42%;
    }

    .panel-title {
        height: 3;
        padding: 1 2;
        color: #68d5cf;
        background: #0d2028;
        text-style: bold;
    }

    #files {
        height: 1fr;
        background: #0a171d;
    }

    #details-scroll {
        height: 1fr;
        padding: 1 2;
    }

    #details {
        width: 1fr;
    }

    Footer {
        background: #0d2028;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+l", "focus_filter", "Filter"),
        Binding("ctrl+r", "refresh_files", "Refresh"),
    ]

    def __init__(
        self,
        root: Path,
        *,
        limit: int = _DEFAULT_LIMIT,
        inference_runner: InferenceRunner | None = None,
    ) -> None:
        self.root = root.expanduser().resolve()
        self.limit = limit
        self.discovery = discover_files(self.root, limit=limit)
        self.filtered_paths: tuple[Path, ...] = self.discovery.paths
        self._row_paths: dict[str, Path] = {}
        self._selected_path: Path | None = None
        self._selection_generation = 0
        self._inference_runner = inference_runner or DefaultInferenceRunner()
        super().__init__()
        self.sub_title = self.root.as_posix()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="shell"):
            yield Static("SEARCH / LIVE FILE FILTER", classes="eyebrow")
            yield Input(
                placeholder="Type part of a filename or relative path…",
                id="filter",
            )
            yield Static(id="status")
            with Horizontal(id="workspace"):
                with Vertical(classes="panel", id="file-pane"):
                    yield Static("FILES", classes="panel-title")
                    yield DataTable(id="files", cursor_type="row", zebra_stripes=True)
                with Vertical(classes="panel", id="detail-pane"):
                    yield Static("INFERENCE DETAILS", classes="panel-title")
                    with VerticalScroll(id="details-scroll"):
                        yield Static(self._empty_details(), id="details")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#files", DataTable)
        table.add_columns("Name", "Relative path", "Size")
        self._rebuild_table("")
        self.query_one("#filter", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        self._rebuild_table(event.value)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row_key = event.row_key.value
        if row_key is None:
            return
        path = self._row_paths.get(row_key)
        if path is not None:
            self._start_inference(path)

    def action_focus_filter(self) -> None:
        filter_input = self.query_one("#filter", Input)
        filter_input.focus()
        filter_input.select_all()

    def action_refresh_files(self) -> None:
        self.discovery = discover_files(self.root, limit=self.limit)
        query = self.query_one("#filter", Input).value
        self._rebuild_table(query)

    def _rebuild_table(self, query: str) -> None:
        normalized_query = query.strip().casefold()
        self.filtered_paths = tuple(
            path
            for path in self.discovery.paths
            if normalized_query in path.relative_to(self.root).as_posix().casefold()
        )
        if not normalized_query:
            self.filtered_paths = self.discovery.paths

        self._invalidate_selection()
        table = self.query_one("#files", DataTable)
        table.clear()
        self._row_paths.clear()

        for index, path in enumerate(self.filtered_paths):
            row_key = str(index)
            self._row_paths[row_key] = path
            relative_path = path.relative_to(self.root).as_posix()
            try:
                size = _format_size(path.stat().st_size)
            except OSError:
                size = "unavailable"
            table.add_row(path.name, relative_path, size, key=row_key)

        total = len(self.discovery.paths)
        status = f"{len(self.filtered_paths):,} shown · {total:,} indexed"
        if self.discovery.truncated:
            status += " · scan limit reached"
        if self.filtered_paths:
            status += " · select a row and press Enter to inspect"
        else:
            status += " · no matching files"
        self.query_one("#status", Static).update(status)

    def _invalidate_selection(self) -> None:
        self._selection_generation += 1
        self._selected_path = None
        self.workers.cancel_group(self, "inference")
        self.query_one("#details", Static).update(self._empty_details())

    def _start_inference(self, path: Path) -> None:
        self._selection_generation += 1
        generation = self._selection_generation
        self._selected_path = path
        loading = Text()
        loading.append(path.name, style="bold #e9f8fa")
        loading.append(
            "\n\nRunning lexical, Magic, Magika, and Hybrid…", style="#89a8af"
        )
        self.query_one("#details", Static).update(loading)
        self._infer_in_background(path, generation)

    @work(
        thread=True,
        exclusive=True,
        group="inference",
        exit_on_error=False,
    )
    def _infer_in_background(self, path: Path, generation: int) -> None:
        worker = get_current_worker()
        try:
            results = tuple(self._inference_runner(path))
        except Exception as error:
            results = (
                StrategyResult(
                    backend="demo",
                    error=f"{type(error).__name__}: {error}",
                ),
            )

        if worker.is_cancelled:
            return
        self.call_from_thread(self._publish_results, path, generation, results)

    def _publish_results(
        self,
        path: Path,
        generation: int,
        results: Sequence[StrategyResult],
    ) -> None:
        if generation != self._selection_generation or path != self._selected_path:
            return
        self.query_one("#details", Static).update(self._render_results(path, results))

    def _render_results(
        self,
        path: Path,
        results: Sequence[StrategyResult],
    ) -> Text:
        relative_path = path.relative_to(self.root).as_posix()
        output = Text()
        output.append(path.name, style="bold #e9f8fa")
        output.append(f"\n{relative_path}", style="#89a8af")

        for result in results:
            output.append("\n\n")
            output.append(result.backend.upper(), style="bold #68d5cf")
            output.append("\n")
            if result.error is not None:
                output.append(result.error, style="#ff8f87")
                continue
            if result.file_type is None:
                output.append("No result", style="#ff8f87")
                continue
            extensions = ", ".join(result.file_type.extensions) or "—"
            mime_types = ", ".join(result.file_type.mime_types) or "—"
            output.append("Extensions  ", style="#89a8af")
            output.append(extensions)
            output.append("\nMIME types  ", style="#89a8af")
            output.append(mime_types)

        return output

    @staticmethod
    def _empty_details() -> Text:
        details = Text()
        details.append("Choose a file", style="bold #e9f8fa")
        details.append(
            "\n\nFilter by filename or path, move to the table, then press Enter. "
            "Inference runs only for the selected file.",
            style="#89a8af",
        )
        return details


def _format_size(size: int) -> str:
    value = float(size)
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    raise AssertionError("unreachable")


def run_demo(root: Path, limit: int = _DEFAULT_LIMIT) -> None:
    """Run the interactive demo for ``root``."""
    FileTypeDemo(root, limit=limit).run()
