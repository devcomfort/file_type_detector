# Idempotent Windows setup for audit-only fixture validators.
$ErrorActionPreference = 'Stop'

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw 'Unsupported Windows host: winget is required to install audit tools.'
}

winget install --id Gyan.FFmpeg --exact --accept-source-agreements --accept-package-agreements --silent
winget install --id TheDocumentFoundation.LibreOffice --exact --accept-source-agreements --accept-package-agreements --silent

py -m pip install -r .audit/requirements-apk.txt
py -m pip install -r .audit/requirements-hlp.txt
py -m pip install ds-store==1.3.3

if (-not (Get-Command unsquashfs.exe -ErrorAction SilentlyContinue)) {
    throw 'Unsupported Windows audit capability: unsquashfs.exe is not available; SquashFS extraction validation cannot run.'
}

Write-Host 'Fixture audit tools installed: ffmpeg, LibreOffice, unsquashfs, androguard, winhlp, ds-store'
