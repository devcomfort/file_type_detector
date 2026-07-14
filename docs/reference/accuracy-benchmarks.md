# Accuracy Benchmarks

> Empirical accuracy data across **598 file formats** for Magic, Magika, Hybrid, and Lexical.
> Generated: 2026-05-04 · libmagic 5.41 · Magika 1.0.1 (standard_v3_3) · Python 3.13.1
> Auto-generated: `rye run python scripts/generate_accuracy_diagram.py`

## Methodology

598 canonical fixture files in `tests/fixtures/` were run through all four inference strategies. Results were compared against `tests/truth/canonical_fixtures.json`, which defines the expected MIME type per format. Tool outputs are version-pinned in `tests/truth/tool_snapshots.json` to ensure reproducibility across environments. A result is considered **correct** when the tool's output MIME exactly matches the canonical MIME.

## Scope

The benchmark covers **598 file formats**. 394 fixtures were generated from format specifications or Python libraries. 204 were downloaded from external repositories: `iamahsanmehmood/sample-files` (MIT, files CC0) and `openpreserve/format-corpus` (CC0). The selection targets commonly encountered formats plus specialized CAD, GIS, scientific, and camera RAW domains.

For context: there are ~50,000+ registered extensions (filext.com), **991 unique MIME types** in libmagic (v5.47), and **216 content types** in Magika's official model (standard_v3_3). Realistically, testing all 50,000 formats is impossible — most are proprietary, obsolete, or require unavailable software to generate valid files.

### Format Distribution

| Category | Formats | Examples |
|----------|:------:|----------|
| Code / Programming | 163 | Python, Rust, Go, C++, TypeScript, COBOL, Fortran, Lisp, Lua... |
| Documents / Text | 47 | PDF, DOCX, HTML, Markdown, CSV, JSON, XML, RTF, EPUB... |
| Archives / Packages | 32 | ZIP, tar.gz, 7z, RAR, DEB, RPM, APK, ISO, DMG... |
| Images | 26 | PNG, JPEG, WebP, SVG, HEIC, PSD, TIFF, BMP, ICNS... |
| Data / Serialization | 21 | SQLite, Parquet, Pickle, HDF5, Protobuf, ONNX, NumPy... |
| Executables / Binaries | 13 | EXE, DLL, ELF, WASM, .class, .pyc, SWF... |
| Audio | 12 | MP3, WAV, FLAC, OGG, AAC, MIDI, AIFF... |
| Video | 9 | MP4, AVI, MKV, MOV, WebM, FLV, 3GP... |
| Certificates / Crypto | 8 | PEM, CRT, CER, DER, PGP, GPG... |
| Fonts | 6 | TTF, OTF, WOFF2, EOT, TTC... |
| Special Documents | 3 | HWP, HWPX, ONE |

> **Note**: 258 of the 598 formats do not map cleanly to a single category above. These include 55 CAD/GIS/3D formats (`.step`, `.stp`, `.stl`, `.gltf`, `.fbx`, `.shp`, `.geojson`, etc.), 53 miscellaneous unclassified formats (`.chm`, `.msi`, `.lnk`, `.url`, `.wad`, `.dcm`, `.gpx`, etc.), and 150 programming language variants that cross into multiple domains.

### Known Gaps

Notable domains not represented in this benchmark: EDA/circuit design files, game engine assets beyond `.wad`, thousands of minor or legacy formats. For formats outside the benchmark scope, behavior is untested and should be validated independently.

### Magika Coverage

Google Magika officially supports **216 content types** in its standard_v3_3 model (112 text, 104 non-text). In our test set, **52 formats** (8.7%) return no result from Magika, and an additional **88** (14.7%) return only a generic MIME — totaling 140 formats where Magika provides no useful signal. These include `.hwp` (not in training data), CAD formats (`.step`, `.iges`, `.brep`), camera RAW (`.arw`, `.cr2`, `.nef`), and several legacy archive formats. Magic covers most of these correctly via byte signature detection.

---

## Unified Accuracy Table

**598 file formats** tested across 4 scenarios.

| Scenario | Samples | ✅ Correct | ⬜ Generic | ❌ Wrong | ⚪ No Result | Accuracy |
|----------|:------:|:------:|:---------:|:------:|:---------:|:------:|
| **Magic** (libmagic) | **598** | 358 | 166 | 74 | 0 | **59.9%** |
| **Magika** (Google AI) | **598** | 374 | 88 | 84 | 52 | **62.5%** |
| **Hybrid** (Magic→Magika) | **598** | 444 | 69 | 85 | 0 | **74.2%** |
| **Lexical** (extension only) | **598** | 116 | 3 | 167 | 312 | **19.4%** |
| **Magic ∪ Magika** (union) | **598** | **535** | — | — | — | **89.5%** |

> **Legend**: ✅ canonical MIME match · ⬜ generic MIME only (text/plain, text/x-c, application/octet-stream) · ❌ wrong specific MIME · ⚪ no result

### Key Insights

| Finding | Data |
|---------|------|
| Magic correct but Magika wrong/empty | **161 formats** (26.9%) — Magic only |
| Magika correct but Magic wrong/generic | **177 formats** (29.6%) — Magika only |
| Both correct | **197 formats** (32.9%) |
| Neither correct | **63 formats** (10.5%) — documented limitations |
| **Hybrid improvement** (Magic→Magika) | **177 formats** improved via Magika refinement |
| Magika empty results (50 formats) covered by Magic | Mostly CAD, camera RAW, legacy archives |
| Lexical completely fails (no MIME) | **312 formats** (52.2%) — mimetypes database too narrow |

---

## Category Analysis

| Category | Count | Description | Magic | Magika | Hybrid |
|----------|:----:|-------------|:-----:|:------:|:------:|
| `magic_correct` | 186 | Magic returns correct specific MIME | **186/186** | 81/186 | 179/186 |
| `magika_improves` | 101 | Magika refines Magic's generic output | 0/101 | **101/101** | **101/101** |
| `magic_wrong` | 166 | Magic returns wrong specific MIME | 91/166 | 129/166 | 85/166 |
| `both_generic` | 95 | Both tools return only generic MIME | 32/95 | 27/95 | 30/95 |
| `magika_fails` | 50 | Magika returns empty — Magic only | **49/50** | 36/50 | **49/50** |
| **Sum** | **598** | | **358** | **374** | **444** |

---

## Reproduction

```bash
# Rebuild fixture set
rye run python -m scripts.generators --all --sources

# Regenerate truth data (after tool version changes)
rye run python scripts/generate_truth_data.py

# Verify fixture-manifest sync
rye run python scripts/generate_truth_data.py --check

# Regenerate SVG diagram + README badges
rye run python scripts/generate_accuracy_diagram.py

# Run full accuracy suite
rye run python -m pytest tests/ -q
```
