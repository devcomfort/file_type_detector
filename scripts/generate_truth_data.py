"""Generate tool snapshot data from canonical fixture truth.

Reads canonical_fixtures.json, runs each inference tool against the
corresponding fixture files, and writes version-pinned results to
tool_snapshots.json.

Usage:
    rye run python scripts/generate_truth_data.py
    rye run python scripts/generate_truth_data.py --check

Output:
    tests/truth/tool_snapshots.json — populated with per-fixture tool results
"""

import argparse
import json
import mimetypes
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Initialize mimetypes deterministically — no OS-specific drift.
mimetypes.init(files=[])

PROJECT_ROOT = Path(__file__).parent.parent
CANONICAL_PATH = PROJECT_ROOT / "tests" / "truth" / "canonical_fixtures.json"
SNAPSHOT_PATH = PROJECT_ROOT / "tests" / "truth" / "tool_snapshots.json"
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"


def _require_magic():
    """Fail loudly if python-magic is not installed."""
    try:
        import magic  # noqa: F401
    except ImportError:
        print("ERROR: python-magic is not installed.", file=sys.stderr)
        print("Install it with: rye add python-magic", file=sys.stderr)
        sys.exit(1)


def _require_magika():
    """Fail loudly if magika is not installed."""
    try:
        import magika  # noqa: F401
    except ImportError:
        print("ERROR: magika is not installed.", file=sys.stderr)
        print("Install it with: rye add magika", file=sys.stderr)
        sys.exit(1)


def collect_metadata():
    """Gather version information for all tools and the runtime environment."""
    python_version = platform.python_version()

    try:
        result = subprocess.run(
            ["file", "--version"],
            capture_output=True, text=True, check=True,
        )
        libmagic_version = result.stdout.splitlines()[0] if result.stdout else "unknown"
    except (FileNotFoundError, subprocess.CalledProcessError):
        libmagic_version = "unknown"

    try:
        import magika
        magika_version = getattr(magika, "__version__", "unknown")
    except ImportError:
        magika_version = "not-installed"

    # Resolve actual model name from Magika config.
    try:
        from magika import Magika, PredictionMode
        m = Magika(prediction_mode=PredictionMode.MEDIUM_CONFIDENCE)
        magika_model = m.get_model_name()
    except Exception:
        magika_model = "unknown"

    return {
        "python_version": python_version,
        "libmagic_version": libmagic_version,
        "magika_version": magika_version,
        "magika_model": magika_model,
        "generation_timestamp": datetime.now(timezone.utc).isoformat(),
        "schema_version": "1.0.0",
    }


def run_magic(fixture_path):
    """Run libmagic on a fixture file and return (mime, extensions).

    Uses magic.from_file for MIME detection, then derives extensions
    via FileType.from_mimetype.
    """
    import magic
    from filetype_detector.core.file_type import FileType

    mime = magic.from_file(str(fixture_path), mime=True)
    if mime is None:
        return None, []

    ft = FileType.from_mimetype(mime)
    return mime, list(ft.extensions)


def run_magika(fixture_path, magika_instance=None):
    """Run Magika on a fixture file and return (mime, extensions, score).

    Uses Magika with MEDIUM_CONFIDENCE prediction mode.
    Accepts an optional pre-created Magika instance for reuse.
    """
    from filetype_detector.core.file_type import FileType

    if magika_instance is not None:
        magika = magika_instance
    else:
        from magika import Magika, PredictionMode
        magika = Magika(prediction_mode=PredictionMode.MEDIUM_CONFIDENCE)

    result = magika.identify_path(path=str(fixture_path))

    mime = result.output.mime_type
    raw_extensions = result.output.extensions
    score = result.prediction.score

    # Normalize extensions to include leading dot.
    extensions = [FileType.normalize_extension(ext) for ext in raw_extensions]

    return mime, extensions, score


def run_lexical(fixture_path):
    """Run lexical (extension-based) inference and return (mime, extensions).

    Uses FileType.from_extension on the path's suffix.
    """
    from filetype_detector.core.file_type import FileType

    suffix = Path(fixture_path).suffix
    if not suffix:
        return None, []

    ft = FileType.from_extension(suffix)
    mime = ft.mime_types[0] if ft.mime_types else None
    return mime, list(ft.extensions)


def run_hybrid(fixture_path):
    """Run hybrid inference and return (mime, extensions).

    Uses HybridInferencer which applies Magic first, then Magika for text files.
    """
    from filetype_detector.strategies.hybrid_inferencer import HybridInferencer

    ft = HybridInferencer().infer(fixture_path)
    mime = ft.mime_types[0] if ft.mime_types else None
    return mime, list(ft.extensions)


def generate_snapshots(canonical_fixtures):
    """Run all tools against each canonical fixture and collect results.

    Parameters
    ----------
    canonical_fixtures : list[dict]
        Entries from canonical_fixtures.json.

    Returns
    -------
    list[dict]
        Per-fixture snapshot with tool outputs.
    """
    from magika import Magika, PredictionMode

    snapshots = []
    missing = []

    # Single Magika instance reused across all fixtures — avoids reloading
    # the model (~100ms) per fixture.
    magika = Magika(prediction_mode=PredictionMode.MEDIUM_CONFIDENCE)

    for fixture in canonical_fixtures:
        fixture_path = PROJECT_ROOT / fixture["path"]
        if not fixture_path.exists():
            missing.append(fixture["path"])
            continue

        magic_mime, magic_exts = run_magic(fixture_path)
        magika_mime, magika_exts, magika_score = run_magika(fixture_path, magika_instance=magika)
        lexical_mime, lexical_exts = run_lexical(fixture_path)
        hybrid_mime, hybrid_exts = run_hybrid(fixture_path)

        snapshots.append({
            "path": fixture["path"],
            "canonical_mime": fixture["canonical_mime"],
            "canonical_extensions": fixture["canonical_extensions"],
            "category": fixture["category"],
            "tool_results": {
                "magic": {"mime": magic_mime, "extensions": magic_exts},
                "magika": {"mime": magika_mime, "extensions": magika_exts, "score": magika_score},
                "lexical": {"mime": lexical_mime, "extensions": lexical_exts},
                "hybrid": {"mime": hybrid_mime, "extensions": hybrid_exts},
            },
        })

    if missing:
        print(f"WARNING: {len(missing)} fixtures missing from filesystem:", file=sys.stderr)
        for p in missing[:10]:
            print(f"  - {p}", file=sys.stderr)
        if len(missing) > 10:
            print(f"  ... and {len(missing) - 10} more", file=sys.stderr)

    return snapshots


def check_fixtures():
    """Verify canonical fixture manifest matches actual fixture files.

    Returns 0 if in sync, 1 if diverged.
    """
    canonical = json.loads(CANONICAL_PATH.read_text())
    canonical_paths = {entry["path"] for entry in canonical["fixtures"]}

    # Check all canonical paths exist.
    missing = []
    for rel_path in sorted(canonical_paths):
        if not (PROJECT_ROOT / rel_path).exists():
            missing.append(rel_path)

    # Check for extra fixtures not in manifest.
    # Exclude documentation and non-fixture files (e.g. SOURCES.md).
    _SKIP_EXTRAS = {"SOURCES.md", ".gitkeep", "README.md"}
    actual_paths = {
        f"tests/fixtures/{f.name}"
        for f in FIXTURES_DIR.iterdir()
        if f.is_file() and f.name not in _SKIP_EXTRAS
    }
    extra = actual_paths - canonical_paths

    if missing or extra:
        if missing:
            print(f"ERROR: {len(missing)} canonical fixtures missing:", file=sys.stderr)
            for p in missing:
                print(f"  - {p}", file=sys.stderr)
        if extra:
            print(f"ERROR: {len(extra)} extra fixtures not in manifest:", file=sys.stderr)
            for p in sorted(extra):
                print(f"  - {p}", file=sys.stderr)
        return 1

    print(f"OK: {len(canonical_paths)} fixtures in sync with manifest.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Generate tool snapshot data from canonical fixtures.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify canonical fixture manifest matches actual fixture files.",
    )
    args = parser.parse_args()

    if args.check:
        sys.exit(check_fixtures())

    # Require dependencies before doing any work.
    _require_magic()
    _require_magika()

    canonical = json.loads(CANONICAL_PATH.read_text())
    fixtures = canonical["fixtures"]

    metadata = collect_metadata()
    snapshots = generate_snapshots(fixtures)

    output = {
        "schema_version": metadata["schema_version"],
        "metadata": metadata,
        "fixtures": snapshots,
    }

    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")

    print(f"Generated {len(snapshots)} snapshots to {SNAPSHOT_PATH}")
    print(f"  Python: {metadata['python_version']}")
    print(f"  libmagic: {metadata['libmagic_version']}")
    print(f"  Magika: {metadata['magika_version']} ({metadata['magika_model']})")


if __name__ == "__main__":
    main()
