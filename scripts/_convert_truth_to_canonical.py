"""Convert accuracy_truth.py categories into canonical_fixtures.json.

This script reads the 5 categories from accuracy_truth.py and produces
a structured JSON file with canonical MIME decisions per fixture.

Run: rye run python scripts/_convert_truth_to_canonical.py
"""

import json
import sys
from pathlib import Path

# Add project root to path so we can import accuracy_truth
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.accuracy_truth import (  # noqa: E402
    MAGIC_CORRECT,
    MAGIKA_IMPROVES,
    MAGIC_WRONG,
    BOTH_GENERIC,
    MAGIKA_FAILS,
)

# Canonical MIME decision rules:
# MAGIC_CORRECT:   canonical_mime = magic_mime (Magic is right)
# MAGIKA_IMPROVES: canonical_mime = magika_mime (Magika provides better)
# MAGIC_WRONG:     canonical_mime = magika_mime (Magika corrects Magic)
# BOTH_GENERIC:    canonical_mime = best known MIME (see mapping below)
# MAGIKA_FAILS:    canonical_mime = magic_mime (only Magic available)

# For BOTH_GENERIC, map extensions to their actual canonical MIME types.
# When the file type is genuinely unknown, use "text/plain" or "application/octet-stream".
BOTH_GENERIC_CANONICAL = {
    # C family
    "c": "text/x-c",
    "c++": "text/x-c++",
    "cc": "text/x-c++",
    "cpp": "text/x-c++",
    "cppm": "text/x-c++",
    "cxx": "text/x-c++",
    "h": "text/x-c",
    "h++": "text/x-c++",
    "hh": "text/x-c++",
    "hpp": "text/x-c++",
    "hxx": "text/x-c++",
    "ixx": "text/x-c++",
    "metal": "text/x-c++",
    # Haskell family
    "hs": "text/x-haskell",
    "lhs": "text/x-haskell",
    "agda": "text/x-agda",
    "idr": "text/x-idris",
    "purs": "text/x-purescript",
    "elm": "text/x-elm",
    # Other languages
    "dart": "text/x-dart",
    "gleam": "text/x-gleam",
    "kt": "text/x-kotlin",
    "kts": "text/x-kotlin",
    "lua": "text/x-lua",
    "jl": "text/x-julia",
    "sol": "text/x-solidity",
    "hlsl": "text/x-hlsl",
    "glsl": "text/x-glsl",
    "wgsl": "text/x-wgsl",
    "mlir": "text/x-mlir",
    # Config / data formats
    "ini": "text/x-ini",
    "m3u": "audio/x-mpegurl",
    "m3u8": "application/vnd.apple.mpegurl",
    "csproj": "text/xml",
    "gemspec": "text/x-ruby",
    "pyi": "text/x-python",
    # Truly generic / unknown
    "txt": "text/plain",
    "text": "text/plain",
    "pub": "text/plain",
    "ps1": "text/x-powershell",
    "vim": "text/x-vim",
    "nix": "text/x-nix",
    "lean": "text/x-lean",
    "dhall": "text/x-dhall",
    "roc": "text/x-roc",
    "sgml": "text/sgml",
    "sum": "text/plain",
    "spv": "application/octet-stream",
    "pb": "application/octet-stream",
    "protobuf": "application/x-protobuf",
    "avro": "application/x-avro",
    "cab": "application/vnd.ms-cab-compressed",
    "carbon": "text/x-carbon",
    "dm": "text/x-dm",
    "dmigd": "text/x-dm",
    "firrtl": "text/x-firrtl",
    "a68": "text/x-algol68",
    "abnf": "text/x-abnf",
    "aidl": "text/x-aidl",
    "au3": "text/x-autoit",
    "b": "text/plain",
    "bdf": "application/x-font-bdf",
    "bf": "text/x-brainfuck",
    "bfm": "text/plain",
    "brf": "text/plain",
    "CPY": "text/x-cobol",
    "m2t": "text/plain",
    "npy": "application/x-numpy",
    "onnx": "application/x-onnx",
    "pickle": "application/x-python-pickle",
    "pkl": "application/x-python-pickle",
    "pt": "application/x-pytorch",
    "pth": "application/x-pytorch",
    "ts": "text/plain",
}

# Canonical extensions for BOTH_GENERIC entries
BOTH_GENERIC_EXTENSIONS = {
    "c": [".c"],
    "c++": [".c++", ".cc", ".cpp", ".cxx", ".cppm", ".ixx"],
    "cc": [".cc", ".cpp", ".cxx", ".c++", ".cppm", ".ixx"],
    "cpp": [".cc", ".cpp", ".cxx", ".c++", ".cppm", ".ixx"],
    "cppm": [".cc", ".cpp", ".cxx", ".c++", ".cppm", ".ixx"],
    "cxx": [".cc", ".cpp", ".cxx", ".c++", ".cppm", ".ixx"],
    "h": [".h"],
    "h++": [".h++", ".hh", ".hpp", ".hxx"],
    "hh": [".h++", ".hh", ".hpp", ".hxx"],
    "hpp": [".h++", ".hh", ".hpp", ".hxx"],
    "hxx": [".h++", ".hh", ".hpp", ".hxx"],
    "ixx": [".cc", ".cpp", ".cxx", ".c++", ".cppm", ".ixx"],
    "metal": [".metal"],
    "hs": [".hs", ".lhs"],
    "lhs": [".hs", ".lhs"],
    "agda": [".agda"],
    "idr": [".idr"],
    "purs": [".purs"],
    "elm": [".elm"],
    "dart": [".dart"],
    "gleam": [".gleam"],
    "kt": [".kt", ".kts"],
    "kts": [".kt", ".kts"],
    "lua": [".lua"],
    "jl": [".jl"],
    "sol": [".sol"],
    "hlsl": [".hlsl"],
    "glsl": [".glsl"],
    "wgsl": [".wgsl"],
    "mlir": [".mlir"],
    "ini": [".ini"],
    "m3u": [".m3u", ".m3u8"],
    "m3u8": [".m3u8", ".m3u"],
    "csproj": [".csproj"],
    "gemspec": [".gemspec"],
    "pyi": [".pyi"],
    "txt": [".txt"],
    "text": [".txt", ".text"],
    "pub": [".pub"],
    "ps1": [".ps1"],
    "vim": [".vim"],
    "nix": [".nix"],
    "lean": [".lean"],
    "dhall": [".dhall"],
    "roc": [".roc"],
    "sgml": [".sgml"],
    "sum": [".sum"],
    "spv": [".spv"],
    "pb": [".pb"],
    "protobuf": [".proto", ".protobuf"],
    "avro": [".avro"],
    "cab": [".cab"],
    "carbon": [".carbon"],
    "dm": [".dm"],
    "dmigd": [".dmigd"],
    "firrtl": [".firrtl"],
    "a68": [".a68"],
    "abnf": [".abnf"],
    "aidl": [".aidl"],
    "au3": [".au3"],
    "b": [".b"],
    "bdf": [".bdf"],
    "bf": [".bf"],
    "bfm": [".bfm"],
    "brf": [".brf"],
    "CPY": [".cpy", ".cbl", ".cob"],
    "m2t": [".m2t"],
    "npy": [".npy"],
    "onnx": [".onnx"],
    "pickle": [".pickle", ".pkl"],
    "pkl": [".pickle", ".pkl"],
    "pt": [".pt"],
    "pth": [".pth"],
    "ts": [".ts"],
}


def make_fixture(
    ext,
    canonical_mime,
    canonical_extensions,
    category,
    provenance,
    ambiguity_notes=None,
):
    """Create a canonical fixture entry."""
    entry = {
        "path": f"tests/fixtures/sample.{ext}",
        "canonical_mime": canonical_mime,
        "canonical_extensions": canonical_extensions,
        "category": category,
        "provenance": provenance,
    }
    if ambiguity_notes:
        entry["ambiguity_notes"] = ambiguity_notes
    return entry


def convert_magic_correct():
    """MAGIC_CORRECT: canonical_mime = magic_mime (Magic is right)."""
    fixtures = []
    for ext, magic_mime, magika_mime, magika_exts, magika_score in MAGIC_CORRECT:
        canonical_exts = [f".{e}" for e in magika_exts] if magika_exts else [f".{ext}"]
        provenance = f"Magic correctly identifies as {magic_mime}"
        ambiguity = None
        if magic_mime != magika_mime and magika_mime not in (
            "text/plain",
            "application/octet-stream",
        ):
            ambiguity = f"Magika suggests {magika_mime} (score={magika_score}), but Magic is authoritative"
        fixtures.append(
            make_fixture(
                ext, magic_mime, canonical_exts, "magic_correct", provenance, ambiguity
            )
        )
    return fixtures


def convert_magika_improves():
    """MAGIKA_IMPROVES: canonical_mime = magika_mime (Magika provides better)."""
    fixtures = []
    for ext, magic_mime, magika_mime, magika_exts, magika_score in MAGIKA_IMPROVES:
        canonical_exts = [f".{e}" for e in magika_exts] if magika_exts else [f".{ext}"]
        provenance = (
            f"Magika improves over Magic's generic '{magic_mime}' to {magika_mime}"
        )
        fixtures.append(
            make_fixture(
                ext, magika_mime, canonical_exts, "magika_improves", provenance
            )
        )
    return fixtures


def convert_magic_wrong():
    """MAGIC_WRONG: canonical_mime = magika_mime (Magika corrects Magic)."""
    fixtures = []
    seen = set()
    for ext, magic_mime, magika_mime, magika_exts, magika_score in MAGIC_WRONG:
        if ext in seen:
            continue  # skip duplicates (bz2, gz appear twice)
        seen.add(ext)
        canonical_exts = [f".{e}" for e in magika_exts] if magika_exts else [f".{ext}"]
        provenance = (
            f"Magic incorrectly reports {magic_mime}; Magika corrects to {magika_mime}"
        )
        fixtures.append(
            make_fixture(ext, magika_mime, canonical_exts, "magic_wrong", provenance)
        )
    return fixtures


def convert_both_generic():
    """BOTH_GENERIC: canonical_mime = best known MIME from mapping."""
    fixtures = []
    for ext, magic_mime, magika_mime, magika_exts, magika_score in BOTH_GENERIC:
        canonical_mime = BOTH_GENERIC_CANONICAL.get(ext, magic_mime)
        canonical_exts = BOTH_GENERIC_EXTENSIONS.get(ext, [f".{ext}"])
        provenance = "Both tools return generic; canonical MIME determined by file extension semantics"
        ambiguity = f"Magic: {magic_mime}, Magika: {magika_mime} (score={magika_score})"
        fixtures.append(
            make_fixture(
                ext,
                canonical_mime,
                canonical_exts,
                "both_generic",
                provenance,
                ambiguity,
            )
        )
    return fixtures


def convert_magika_fails():
    """MAGIKA_FAILS: canonical_mime = magic_mime (only Magic available)."""
    fixtures = []
    for ext, magic_mime, magika_mime, magika_exts, magika_score in MAGIKA_FAILS:
        canonical_exts = [f".{ext}"]
        provenance = f"Magika returns empty; Magic identifies as {magic_mime}"
        fixtures.append(
            make_fixture(ext, magic_mime, canonical_exts, "magika_fails", provenance)
        )
    return fixtures


def main():
    fixtures = []
    fixtures.extend(convert_magic_correct())
    fixtures.extend(convert_magika_improves())
    fixtures.extend(convert_magic_wrong())
    fixtures.extend(convert_both_generic())
    fixtures.extend(convert_magika_fails())

    output = {
        "schema_version": "1.0.0",
        "description": "Canonical fixture truth for filetype-detector accuracy tests. "
        "Each entry defines the ground-truth MIME type and extensions for a test fixture.",
        "fixtures": fixtures,
    }

    output_path = project_root / "tests" / "truth" / "canonical_fixtures.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")

    print(f"Wrote {len(fixtures)} fixtures to {output_path}")

    # Print category counts
    categories = {}
    for f in fixtures:
        categories[f["category"]] = categories.get(f["category"], 0) + 1
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
