# Fixture Tool Installation Dossier

This document is the required precondition for fixtures that need external tools. It records what the extension means, how the bytes are constructed, which tools are needed, how to install them per OS, and which repository script performs generation or validation.

## OS installation entry points

Run the script for the target operating system before generating or validating fixtures.

| OS | Script | Installation behavior |
|---|---|---|
| Linux | [`scripts/install-fixture-tools-linux.sh`](../../scripts/install-fixture-tools-linux.sh) | Installs `ffmpeg`, `libreoffice`, `squashfs-tools`, pinned Python audit packages, and `ds-store`. Requires `apt-get` and `sudo`; otherwise exits `unsupported`. |
| macOS | [`scripts/install-fixture-tools-macos.sh`](../../scripts/install-fixture-tools-macos.sh) | Installs Homebrew formulae `ffmpeg` and `squashfs-tools`, the LibreOffice cask, and pinned Python audit packages. Requires Homebrew and `unsquashfs`; otherwise exits `unsupported`. |
| Windows | [`scripts/install-fixture-tools-windows.ps1`](../../scripts/install-fixture-tools-windows.ps1) | Installs FFmpeg and LibreOffice with `winget`, then Python audit packages. It exits `unsupported` when `unsquashfs.exe` is unavailable because the SquashFS validator cannot run. |

All scripts are intended to be idempotent. They install audit-only tools; these tools are not runtime dependencies of `filetype-detector`.

## Format dossiers

| Extension / filename | What the format means and how the file is structured | Construction method | Independent tool | Installation command / method | Repository script |
|---|---|---|---|---|---|
| `.dcm` / DICOM | 128-byte preamble, `DICM` marker, File Meta Information, transfer syntax, and dataset elements | `DataFormatGenerator._create_dcm` with fixed metadata and `pydicom.dcmwrite` | `pydicom.dcmread` | Included in the locked fixture environment; otherwise `python -m pip install -r requirements-dev.lock` | `scripts/generators/data_formats.py`; `.audit/w3_validate.py --id sample-dcm` |
| `.pyc` / Python bytecode | CPython magic number, fixed header, and marshalled code object | `ExecutableGenerator._create_pyc` using `compile("pass", "<module>", "exec")` and `marshal` | CPython magic/header check plus `marshal.loads` | `python -m pip install -r requirements-dev.lock` | `scripts/generators/executables.py`; `.audit/w3_validate.py --id sample-pyc` |
| `.snap` / `.squashfs` | SquashFS 4.0 superblock and compressed filesystem blocks; `.snap` is a package convention over a SquashFS image | Pinned reproducible SquashFS bytes generated with fixed timestamps and embedded for portable reproduction | `unsquashfs` extraction; `squashfs-tools` | Linux: `sudo apt-get install squashfs-tools`; macOS: `brew install squashfs-tools`; Windows: explicitly unsupported unless `unsquashfs.exe` is supplied | `scripts/generators/archives.py`; `.audit/w3_validate.py --id sample-snap` / `sample-squashfs` |
| `.dsstore` fixture staged as `.DS_Store` | macOS Desktop Services Store, including `Bud1` header, B-tree metadata, and typed records such as `Iloc`; the exact filename is `.DS_Store`, not a normative `.dsstore` extension | `MacOSGenerator._create_dsstore` with deterministic `Iloc` entry | `ds-store==1.3.3` parser reopen and record traversal | `python -m pip install ds-store==1.3.3`, or run the OS installer script | `scripts/generators/macos.py`; `.audit/w3_validate.py --id sample-dsstore` |
| `.apk` | ZIP package containing binary Android XML, DEX, and package metadata | `ArchiveGenerator._create_apk` | `androguard==4.1.4`; current result is container/AXML validation, not full Android application semantics | `python -m pip install -r .audit/requirements-apk.txt` | `scripts/generators/archives.py`; `.audit/apk_validate.py --id sample-apk` |
| `.hlp` | Windows Help file with header, directory B-tree, `|SYSTEM`, `|TOPIC`, and related internal files | Immutable upstream `FXSEARCH.HLP` fixture pinned to an upstream commit | `winhlp==0.3.0` parser | `python -m pip install -r .audit/requirements-hlp.txt` | `.audit/hlp_validate.py --id sample-hlp` |
| `.emf` | Enhanced Metafile header and EMF records such as header, move, line, and EOF | `ImageGenerator._create_emf` | Structural record assertions plus LibreOffice Draw import/export | Linux/macOS: install LibreOffice through the OS installer script; Windows requires a supported LibreOffice installation | `scripts/generators/images.py`; `.audit/metafile_validate.py --id sample-emf` |
| `.wmf` | Windows Metafile header and 16-bit records such as `META_MOVETO`, `META_LINETO`, and EOF | `ImageGenerator._create_wmf` | Structural record assertions plus LibreOffice Draw import/export | Same LibreOffice installation procedure as EMF | `scripts/generators/images.py`; `.audit/metafile_validate.py --id sample-wmf` |
| `.flac` | FLAC stream marker, STREAMINFO metadata, audio frame, and checksums | Pinned decodable bytes produced from a deterministic silent audio recipe | `ffprobe`/`ffmpeg` decode | Linux: `sudo apt-get install ffmpeg`; macOS: `brew install ffmpeg`; Windows: install FFmpeg from the installer/script | `scripts/generators/audio.py`; fixture generator tests |
| `.webm` | EBML/WebM header, Segment, tracks, and encoded media payload | Pinned bytes produced from a deterministic VP9 recipe | `ffprobe`/`ffmpeg` decode | Same FFmpeg installation procedure as FLAC | `scripts/generators/video.py`; fixture generator tests |
| `.woff` | WOFF header, table directory, and valid sfnt tables such as `head`, `glyf`, `name`, and `post` | FontTools-generated WOFF bytes embedded for portable reproduction | `fontTools.ttLib.TTFont` reopen | `python -m pip install -r requirements-dev.lock` | `scripts/generators/fonts.py`; exact-byte gate |
| `.tga` / `.icns` | TGA pixel/header/footer structure; ICNS icon chunk containing a valid PNG | Image generator with fixed pixels and PNG bytes | Pillow image decode | `python -m pip install -r requirements-dev.lock` | `scripts/generators/images.py`; fixture generator tests |
| `.cab`, `.crx`, `.deb`, `.dex`, `.rpm`, `.xar`, `.lha` | Each uses its own archive/header/record structure; these are not validated by a shared ZIP fallback | Dedicated generator methods | Format-specific structural parser, cryptographic check, `tarfile`, or archive tool as recorded in the W3 matrix | Use the Linux/macOS/Windows installer or locked Python fixture dependencies as applicable | `scripts/generators/archives.py`, `scripts/generators/executables.py`; `.audit/w3_validate.py` |
| `.ai` | Illustrator files can contain PDF-compatible data, but a valid PDF alone does not prove native Illustrator PGF semantics | Deterministic PDF-compatible generator retaining Illustrator markers | `pdfinfo` confirms PDF structure; it does not establish native Illustrator semantics | `pdfinfo` is supplied by Poppler on Linux/macOS; Windows requires a Poppler installation | `scripts/generators/documents.py`; exact-byte gate; remains quarantined for subtype promotion |

## Evidence and promotion policy

A detector label is not format-validity evidence. A fixture may be promoted only when all of the following are recorded:

1. Reproducible generator output or immutable external provenance.
2. Independent parser, reader, decoder, or round-trip validation.
3. MIME and extension or exact-filename authority evidence.
4. Content identifiability and a clear distinction from generic containers.
5. Correct source license and tool version information.

If a validator is unavailable on an operating system, the script must fail explicitly as unsupported; it must not silently skip the check. The separate coverage report records those gaps instead of turning them into false passes.
