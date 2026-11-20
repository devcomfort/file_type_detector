# Manage the Tika backend toolchain: Java (via jabba) and the pinned Tika JAR.
#
# Usage:
#   install-tika-tools-windows.ps1 -Action install [-JavaVersion <jabba-ref>] [-TikaVersion <v>]
#   install-tika-tools-windows.ps1 -Action update  [-JavaVersion <jabba-ref>] [-TikaVersion <v>]
#   install-tika-tools-windows.ps1 -Action check
#   install-tika-tools-windows.ps1 -Action remove  [-JarOnly|-JavaOnly]
#
# All versions come from ..\tika-manifest.json unless overridden on the CLI.
# Idempotent: re-running install or update converges to the manifest state.
#Requires -Version 5.1
param(
    [ValidateSet('install', 'update', 'check', 'remove')]
    [string]$Action = 'install',
    [string]$JavaVersion,
    [string]$TikaVersion,
    [string]$Sha512,
    [switch]$JarOnly,
    [switch]$JavaOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not ($IsWindows -or $env:OS -eq 'Windows_NT')) {
    Write-Error 'unsupported: this installer requires Windows'; exit 2
}

$Root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$ManifestPath = Join-Path $Root 'tika-manifest.json'
$Manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json

if (-not $JavaVersion) { $JavaVersion = $Manifest.java.install_version }
if (-not $TikaVersion) { $TikaVersion = $Manifest.tika.version }
$MinJavaMajor = [int]$Manifest.java.min_major

$CacheDir = Join-Path $env:LOCALAPPDATA 'filetype-detector'
$JarName = $Manifest.tika.jar_filename
if ($TikaVersion -ne $Manifest.tika.version) {
    $JarName = "tika-app-$TikaVersion.jar"
    $JarUrl = $Manifest.tika.jar_url_template -replace '\{version\}', $TikaVersion
    $JarSha512 = $Sha512
} else {
    $JarUrl = $Manifest.tika.jar_url; $JarSha512 = $Manifest.tika.jar_sha512
}
$JarPath = Join-Path $CacheDir $JarName
$JabbaDir = if ($env:JABBA_HOME) { $env:JABBA_HOME } else { Join-Path $env:USERPROFILE '.jabba' }

function Test-Jar {
    if (-not (Test-Path $JarPath)) { return $false }
    if (-not $JarSha512) { return $true }
    $hash = (Get-FileHash -Algorithm SHA512 $JarPath).Hash.ToLowerInvariant()
    return $hash -eq $JarSha512.ToLowerInvariant()
}

function Get-JavaMajor {
    $java = Get-Command java -ErrorAction SilentlyContinue
    if (-not $java) { return 0 }
    $line = (& java -version 2>&1 | Select-Object -First 1)
    if ($line -match 'version "(\d+)') { return [int]$Matches[1] }
    return 0
}

function Ensure-Jabba {
    if (Get-Command jabba -ErrorAction SilentlyContinue) { return }
    $jabbaExe = Join-Path $JabbaDir 'bin\jabba.exe'
    if (Test-Path $jabbaExe) { $env:Path = "$(Split-Path $jabbaExe);$env:Path"; return }
    Write-Host 'installing jabba...'
    $installer = Join-Path $env:TEMP 'jabba-install.ps1'
    Invoke-WebRequest -Uri 'https://github.com/Jabba-Team/jabba/raw/main/install.ps1' -OutFile $installer
    & $installer -SkipRC
    $env:Path = "$JabbaDir\bin;$env:Path"
    if (-not (Get-Command jabba -ErrorAction SilentlyContinue)) {
        throw 'jabba installation failed; install it manually from https://github.com/Jabba-Team/jabba'
    }
}

function Ensure-Java {
    $major = Get-JavaMajor
    if ($major -ge $MinJavaMajor) {
        Write-Host "java already present (major=$major); skipping jabba install"
        return
    }
    Ensure-Jabba
    Write-Host "installing Java via jabba: $JavaVersion"
    & jabba install $JavaVersion | Write-Host
    & jabba alias default $JavaVersion | Out-Null
    $newest = (& jabba ls | Select-Object -Last 1).Trim()
    $env:JAVA_HOME = Join-Path $JabbaDir "jdk\$newest"
    $env:Path = "$env:JAVA_HOME\bin;$env:Path"
    $major = Get-JavaMajor
    if ($major -lt $MinJavaMajor) { throw "installed Java major $major < required $MinJavaMajor" }
    Write-Host "java ready: $(& java -version 2>&1 | Select-Object -First 1)"
}

function Ensure-Jar {
    if (Test-Jar) { Write-Host "jar already verified: $JarPath"; return }
    if (-not $JarSha512) { throw "no SHA-512 for $JarName; pass -Sha512 or pin the version in tika-manifest.json" }
    New-Item -ItemType Directory -Force $CacheDir | Out-Null
    $tmp = "$JarPath.download"
    Write-Host "downloading $JarUrl"
    Invoke-WebRequest -Uri $JarUrl -OutFile $tmp
    $hash = (Get-FileHash -Algorithm SHA512 $tmp).Hash.ToLowerInvariant()
    if ($hash -ne $JarSha512.ToLowerInvariant()) {
        Remove-Item $tmp -Force -ErrorAction SilentlyContinue
        throw 'JAR SHA-512 mismatch; refusing to install'
    }
    Move-Item -Force $tmp $JarPath
    Write-Host "jar installed and verified: $JarPath"
}

switch ($Action) {
    { $_ -in 'install', 'update' } { Ensure-Java; Ensure-Jar }
    'check' {
        $ok = $true
        if (Test-Jar) { Write-Host "jar: OK ($JarPath)" } else { Write-Host 'jar: MISSING or hash mismatch'; $ok = $false }
        $major = Get-JavaMajor
        if ($major -ge $MinJavaMajor) { Write-Host "java: OK ($(& java -version 2>&1 | Select-Object -First 1))" }
        else { Write-Host "java: missing or too old (need >= $MinJavaMajor)"; $ok = $false }
        if (-not $ok) { exit 1 }
    }
    'remove' {
        if (-not $JavaOnly) { Remove-Item $JarPath -Force -ErrorAction SilentlyContinue; Write-Host "removed $JarPath" }
        if (-not $JarOnly) {
            Write-Host "note: jabba keeps installed JDKs under $JabbaDir\jdk; run 'jabba uninstall <ref>' or remove $JabbaDir to purge"
        }
    }
}
