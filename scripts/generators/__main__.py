#!/usr/bin/env python3
"""CLI for generating fixture files.

Usage:
    python -m scripts.generators                     # List all available extensions
    python -m scripts.generators --list                # Same as above
    python -m scripts.generators --list-by-category    # Group by category
    python -m scripts.generators png jpg gif           # Generate specific extensions
    python -m scripts.generators --category image      # Generate all image formats
    python -m scripts.generators --all                 # Generate all supported formats
    python -m scripts.generators --all --force         # Overwrite existing files
    python -m scripts.generators --sources             # Write SOURCES.md manifest
    python -m scripts.generators --output /path/to/fixtures  # Custom output directory
"""

import argparse
import sys
from pathlib import Path

from . import list_generators, list_extensions, list_sources
from .base import BaseGenerator


def write_sources_manifest(output_dir: Path) -> None:
    """Write SOURCES.md covering every sample.* fixture on disk in the output directory."""
    sources = list_sources()
    cats = list_extensions()
    cat_map: dict[str, str] = {}
    for cat, exts in cats.items():
        for ext in exts:
            cat_map[ext] = cat

    # Scan disk for all sample.* fixtures
    disk_exts: dict[str, Path] = {}
    for f in sorted(output_dir.glob("sample.*")):
        ext = f.name.replace("sample.", "")
        disk_exts[ext] = f

    # Categorize: fixtures with registered generators vs. discovered-only
    registered: dict[str, str] = {}
    discovered: dict[str, Path] = {}

    for ext, path in disk_exts.items():
        if ext in sources:
            registered[ext] = sources[ext]
        else:
            discovered[ext] = path

    generated_count = sum(1 for s in sources.values() if not s.startswith("download:"))
    download_count = sum(1 for s in sources.values() if s.startswith("download:"))

    lines = [
        "# Fixture Sources",
        "",
        f"This directory contains **{len(disk_exts)}** fixture files used by the",
        "filetype-detector test suite.",
        "",
    ]
    if generated_count > 0:
        lines.append(
            f"**{generated_count}** fixtures are synthetically generated from format"
            " specifications."
        )
    if download_count > 0:
        lines.append(
            f"**{download_count}** fixtures are downloaded from external repositories"
            " (see attribution details below)."
        )
    if discovered:
        lines.append(
            f"**{len(discovered)}** fixtures exist on disk but have no registered"
            " generator; they were added manually or via legacy scripts."
        )

    lines.append("")
    lines.append("## Registered generators")
    lines.append("")

    for ext in sorted(registered):
        cat = cat_map.get(ext, "unknown")
        lines.append(f"- `sample.{ext}` ({cat}): {registered[ext]}")

    if discovered:
        lines.append("")
        lines.append("## Discovered fixtures (no registered generator)")
        lines.append("")
        lines.append(
            "These fixture files exist on disk but are not produced by any registered"
            " generator. They were added via legacy `scripts/generate_fixtures.py` or"
            " `scripts/download_fixtures.py` workflows, or were manually placed."
            " Regenerate them with:"
        )
        lines.append("")
        lines.append("    rye run python scripts/generate_fixtures.py")
        lines.append("    rye run python scripts/download_fixtures.py")
        lines.append("")
        for ext in sorted(discovered):
            path = discovered[ext]
            size = path.stat().st_size
            lines.append(f"- `sample.{ext}` ({size:,} bytes): external: existing fixture (no registered generator)")
        lines.append("")

    lines.append("")
    lines.append(f"Total: {len(disk_exts)} fixtures")
    lines.append("")

    (output_dir / "SOURCES.md").write_text("\n".join(lines))
    print(f"  Wrote SOURCES.md ({len(registered)} registered, {len(discovered)} discovered, {len(disk_exts)} total)")


def get_all_generators() -> list[BaseGenerator]:
    """Instantiate all registered generators."""
    return [cls() for cls in list_generators().values()]


def find_generator_for_ext(ext: str) -> BaseGenerator | None:
    """Find a generator that can produce the given extension."""
    for gen in get_all_generators():
        if ext in gen.extensions:
            return gen
    return None


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate fixture files for file type detection testing.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "extensions",
        nargs="*",
        help="Specific extensions to generate (without dot, e.g., png jpg gif)",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available extensions",
    )
    parser.add_argument(
        "--list-by-category", "-L",
        action="store_true",
        help="List extensions grouped by category",
    )
    parser.add_argument(
        "--category", "-c",
        type=str,
        help="Generate all extensions in a category",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Generate all supported formats",
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite existing files",
    )
    parser.add_argument(
        "--sources", "-s",
        action="store_true",
        help="Write SOURCES.md manifest to output directory",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path(__file__).parent.parent.parent / "tests" / "fixtures",
        help="Output directory (default: tests/fixtures/)",
    )
    args = parser.parse_args()

    # Determine which extensions to generate
    target_exts = set()

    if args.all:
        for gen in get_all_generators():
            target_exts.update(gen.extensions)
    elif args.category:
        cats = list_extensions()
        if args.category not in cats:
            print(f"Unknown category: {args.category}")
            print(f"Available: {', '.join(sorted(cats.keys()))}")
            sys.exit(1)
        target_exts.update(cats[args.category])
    elif args.extensions:
        target_exts.update(args.extensions)

    # List mode (only when nothing to generate)
    if not target_exts:
        if args.list:
            exts = set()
            for gen in get_all_generators():
                exts.update(gen.extensions)
            for ext in sorted(exts):
                print(ext)
            print(f"\nTotal: {len(exts)} extensions")
            return

        if args.list_by_category:
            cats = list_extensions()
            for cat in sorted(cats):
                print(f"\n=== {cat} ({len(cats[cat])}) ===")
                for ext in sorted(cats[cat]):
                    print(f"  {ext}")
            total = sum(len(v) for v in cats.values())
            print(f"\nTotal: {total} extensions across {len(cats)} categories")
            return

        # --sources only: write manifest without generating
        if args.sources:
            args.output.mkdir(parents=True, exist_ok=True)
            write_sources_manifest(args.output)
            return

        parser.print_help()
        return

    # Generate
    args.output.mkdir(parents=True, exist_ok=True)
    success = 0
    skipped = 0
    failed = 0

    for ext in sorted(target_exts):
        gen = find_generator_for_ext(ext)
        if gen is None:
            print(f"  ✗ {ext}: No generator found")
            failed += 1
            continue

        path = args.output / f"sample.{ext}"
        if path.exists() and not args.force:
            skipped += 1
            continue

        try:
            content = gen.generate(ext)
            path.write_bytes(content)
            print(f"  ✓ {ext} ({len(content):,} bytes)")
            success += 1
        except Exception as e:
            print(f"  ✗ {ext}: {e}")
            failed += 1

    if args.sources:
        write_sources_manifest(args.output)

    print(f"\nDone: {success} created, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    main()
