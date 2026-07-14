"""Generate a coverage report comparing fixtures against Magika and libmagic.

Usage:
    python examples/coverage_report.py
    python examples/coverage_report.py --format json > coverage.json
    python examples/coverage_report.py --format markdown > COVERAGE.md
"""

import json
import argparse
from pathlib import Path

import magic
from magika import Magika


def load_magika_types():
    """Load Magika's content types knowledge base.

    Returns
    -------
    dict
        Mapping of content type name to metadata (mime_type, extensions, is_text).
    """
    import magika as magika_pkg

    config_path = Path(magika_pkg.__file__).parent / "config" / "content_types_kb.min.json"
    with open(config_path) as f:
        return json.load(f)


def get_fixture_coverage(fixtures_dir):
    """Analyze current fixture files with both strategies.

    Parameters
    ----------
    fixtures_dir : Path
        Path to the fixtures directory.

    Returns
    -------
    list[dict]
        List of coverage records for each fixture file.
    """
    m = magic.Magic(mime=True)
    magika = Magika()
    magika_types = load_magika_types()

    results = []
    for sample in sorted(fixtures_dir.glob("sample.*")):
        libmagic_mime = m.from_file(str(sample))

        # Magika detection
        try:
            magika_result = magika.identify_path(path=str(sample))
            magika_mime = magika_result.output.mime_type
            magika_ext = magika_result.output.extensions
            magika_score = magika_result.prediction.score
        except Exception:
            magika_mime = None
            magika_ext = []
            magika_score = None

        # Find matching Magika type by extension
        ext = sample.suffix.lstrip(".").lower()
        magika_type = None
        for name, info in magika_types.items():
            if ext in [e.lower() for e in info.get("extensions", [])]:
                magika_type = name
                break

        results.append(
            {
                "file": sample.name,
                "extension": ext,
                "libmagic_mime": libmagic_mime,
                "magika_mime": magika_mime,
                "magika_type": magika_type,
                "magika_extensions": magika_ext,
                "magika_score": magika_score,
                "magika_supported": magika_type is not None,
            }
        )

    return results


def get_magika_gap_analysis(fixtures_dir):
    """Identify Magika-supported formats missing from fixtures.

    Parameters
    ----------
    fixtures_dir : Path
        Path to the fixtures directory.

    Returns
    -------
    dict
        Gap analysis with missing formats grouped by category.
    """
    magika_types = load_magika_types()
    fixture_exts = {f.suffix.lstrip(".").lower() for f in fixtures_dir.glob("sample.*")}

    # Collect all Magika extensions
    magika_ext_map = {}
    for name, info in magika_types.items():
        for ext in info.get("extensions", []):
            ext_lower = ext.lower()
            if ext_lower not in magika_ext_map:
                magika_ext_map[ext_lower] = []
            magika_ext_map[ext_lower].append(
                {
                    "type": name,
                    "mime": info.get("mime_type"),
                    "is_text": info.get("is_text", False),
                    "description": info.get("description", ""),
                }
            )

    missing = []
    for ext, types in sorted(magika_ext_map.items()):
        if ext not in fixture_exts:
            missing.append({"extension": ext, "types": types})

    # Categorize
    categories = {
        "images": ["png", "jpg", "jpeg", "gif", "bmp", "tiff", "ico", "svg", "webp", "avif", "jp2", "psd", "tga", "icns", "emf", "wmf"],
        "audio": ["mp3", "wav", "flac", "ogg", "midi", "aac", "wma"],
        "video": ["mp4", "avi", "mkv", "webm", "flv", "3gp", "mov", "qt"],
        "archives": ["zip", "tar", "gz", "bz2", "xz", "7z", "rar", "lz", "lzma"],
        "executables": ["exe", "dll", "so", "dylib", "elf", "macho", "pebin", "msi", "deb", "rpm"],
        "fonts": ["ttf", "otf", "woff", "woff2", "eot"],
        "code": ["go", "rs", "java", "rb", "php", "js", "ts", "sh", "lua", "swift", "kt", "scala"],
        "data": ["sqlite", "parquet", "avro", "protobuf", "h5", "onnx", "npy", "pickle"],
        "documents": ["rtf", "tex", "odt", "epub", "mobi", "djvu"],
        "config": ["ini", "toml", "yaml", "yml", "xml", "jsonl"],
    }

    categorized = {}
    uncategorized = []
    for item in missing:
        ext = item["extension"]
        placed = False
        for cat, exts in categories.items():
            if ext in exts:
                categorized.setdefault(cat, []).append(item)
                placed = True
                break
        if not placed:
            uncategorized.append(item)

    return {
        "total_magika_types": len(magika_types),
        "total_magika_extensions": len(magika_ext_map),
        "current_fixture_count": len(fixture_exts),
        "missing_count": len(missing),
        "categorized": categorized,
        "uncategorized": uncategorized,
    }


def format_markdown(coverage, gap):
    """Format coverage report as Markdown.

    Parameters
    ----------
    coverage : list[dict]
        Fixture coverage results.
    gap : dict
        Gap analysis results.

    Returns
    -------
    str
        Markdown-formatted report.
    """
    lines = [
        "# File Type Coverage Report",
        "",
        "## Summary",
        "",
        f"- **Magika supported types**: {gap['total_magika_types']}",
        f"- **Magika unique extensions**: {gap['total_magika_extensions']}",
        f"- **Current fixtures**: {gap['current_fixture_count']}",
        f"- **Missing fixtures**: {gap['missing_count']}",
        f"- **Coverage**: {gap['current_fixture_count'] / gap['total_magika_extensions'] * 100:.1f}%",
        "",
        "## Current Fixture Coverage",
        "",
        "| File | Extension | libmagic MIME | Magika MIME | Magika Type | Score |",
        "|------|-----------|---------------|-------------|-------------|-------|",
    ]

    for row in coverage:
        score = f"{row['magika_score']:.3f}" if row["magika_score"] else "—"
        mime = row["magika_mime"] or "—"
        mtype = row["magika_type"] or "—"
        lines.append(
            f"| {row['file']} | .{row['extension']} | {row['libmagic_mime']} | {mime} | {mtype} | {score} |"
        )

    lines.extend(["", "## Missing Fixtures by Category", ""])

    for cat, items in gap["categorized"].items():
        lines.append(f"### {cat.title()} ({len(items)})")
        lines.append("")
        lines.append("| Extension | Magika Type | MIME | Description |")
        lines.append("|-----------|-------------|------|-------------|")
        for item in sorted(items, key=lambda x: x["extension"]):
            for t in item["types"]:
                desc = t.get("description", "")
                lines.append(
                    f"| .{item['extension']} | {t['type']} | {t['mime'] or '—'} | {desc} |"
                )
        lines.append("")

    return "\n".join(lines)


def main():
    """Generate and display the coverage report."""
    parser = argparse.ArgumentParser(description="File type coverage report")
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=Path(__file__).parent.parent / "tests" / "fixtures",
        help="Path to fixtures directory",
    )
    args = parser.parse_args()

    fixtures_dir = args.fixtures
    coverage = get_fixture_coverage(fixtures_dir)
    gap = get_magika_gap_analysis(fixtures_dir)

    if args.format == "json":
        print(json.dumps({"coverage": coverage, "gap_analysis": gap}, indent=2))
    elif args.format == "markdown":
        print(format_markdown(coverage, gap))
    else:
        covered_count = gap["total_magika_extensions"] - gap["missing_count"]
        non_magika = gap["current_fixture_count"] - covered_count
        effective_total = gap["total_magika_extensions"] + non_magika
        print(f"Magika supported types: {gap['total_magika_types']}")
        print(f"Magika unique extensions: {gap['total_magika_extensions']}")
        print(f"Current fixtures: {gap['current_fixture_count']}")
        print(f"Missing fixtures: {gap['missing_count']}")
        print()
        print(f"Magika coverage: {covered_count}/{gap['total_magika_extensions']} = {covered_count / gap['total_magika_extensions'] * 100:.1f}%")
        print(f"Non-Magika fixtures: {non_magika}")
        print(f"Total coverage: {gap['current_fixture_count']}/{effective_total} = {gap['current_fixture_count'] / effective_total * 100:.1f}%")
        print()
        print("Current fixture coverage:")
        for row in coverage:
            score = f"({row['magika_score']:.3f})" if row["magika_score"] else ""
            mime = row["magika_mime"] or "—"
            print(f"  {row['file']:15s} -> libmagic: {row['libmagic_mime']:40s} magika: {mime} {score}")


if __name__ == "__main__":
    main()
