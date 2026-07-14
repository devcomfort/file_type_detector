"""Command-line entrypoint for the interactive terminal demo."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from pathlib import Path

DemoRunner = Callable[[Path, int], None]


def _positive_integer(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="filetype-detector-demo",
        description="Explore file-type inference results in an interactive terminal UI.",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="directory to browse (default: current directory)",
    )
    parser.add_argument(
        "--limit",
        type=_positive_integer,
        default=1_000,
        help="maximum files to index (default: 1000)",
    )
    return parser


def _load_runner() -> DemoRunner:
    from .demo import run_demo

    return run_demo


def main(argv: Sequence[str] | None = None) -> int:
    """Parse CLI arguments and launch the Textual demo."""
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    directory = arguments.directory.expanduser().resolve()

    if not directory.exists():
        parser.error(f"directory does not exist: {directory}")
    if not directory.is_dir():
        parser.error(f"not a directory: {directory}")

    runner = _load_runner()

    runner(directory, arguments.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
