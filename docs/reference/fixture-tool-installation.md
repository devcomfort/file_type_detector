# Fixture Tool Installation Dossier

Fixture generation and independent validation use audit-only tools. They are not runtime dependencies of `filetype-detector`.

## Installation scripts

| OS | Script | Scope |
|---|---|---|
| Linux | [`scripts/install-fixture-tools-linux.sh`](../../scripts/install-fixture-tools-linux.sh) | ffmpeg, LibreOffice, squashfs-tools, androguard, winhlp, ds-store |
| macOS | [`scripts/install-fixture-tools-macos.sh`](../../scripts/install-fixture-tools-macos.sh) | Homebrew ffmpeg, LibreOffice, squashfs-tools, androguard, winhlp, ds-store; fails explicitly if `unsquashfs` is unavailable |
| Windows | [`scripts/install-fixture-tools-windows.ps1`](../../scripts/install-fixture-tools-windows.ps1) | winget ffmpeg/LibreOffice, Python audit packages; fails explicitly if `unsquashfs.exe` is unavailable |

All scripts are idempotent: package managers may report already-installed packages without changing the resulting environment. Unsupported prerequisites fail with a non-zero exit and an explicit message.

## Format dossiers and validators

| Format | Construction/validation | Required tool | Validator |
|---|---|---|---|
| DS_Store | `MacOSGenerator._create_dsstore`; deterministic writer and parser round-trip | `ds-store==1.3.3` | `.audit/w3_validate.py --id sample-dsstore` |
| APK | ZIP + binary AXML + DEX fixture; independent package parse | `androguard==4.1.4` | `.audit/apk_validate.py --id sample-apk` |
| HLP | Immutable upstream FXSEARCH.HLP fixture; WinHelp internal-file parse | `winhlp==0.3.0` | `.audit/hlp_validate.py --id sample-hlp` |
| SquashFS/Snap | Pinned reproducible bytes; extraction round-trip | `squashfs-tools` | `.audit/w3_validate.py --id sample-squashfs` |
| EMF/WMF | Generator record structures; LibreOffice Draw import/export | `libreoffice` | `.audit/metafile_validate.py --id sample-emf` / `sample-wmf` |
| FLAC/WebM | Decoder-valid media bytes | `ffmpeg`/`ffprobe` | Generator-specific media checks and CI audit steps |
| WOFF | Complete font table package | `fontTools` | `FontGenerator` exact-byte gate and fontTools reopen |
| DICOM | File Meta and dataset generated with pydicom | `pydicom` | `.audit/w3_validate.py --id sample-dcm` |

## Evidence rule

A detector label is never the only validity evidence. A fixture is promoted only when its bytes are reproducible or immutably sourced, an independent parser/round-trip check succeeds, MIME/extension or filename evidence exists, and identifiability is recorded.
