#!/usr/bin/env bash
# Manage the Tika backend toolchain: Java (via jabba) and the pinned Tika JAR.
#
# Usage:
#   install-tika-tools-linux.sh install [--java-version <jabba-ref>] [--tika-version <v>]
#   install-tika-tools-linux.sh update  [--java-version <jabba-ref>] [--tika-version <v>]
#   install-tika-tools-linux.sh check
#   install-tika-tools-linux.sh remove  [--jar-only|--java-only]
#
# All versions come from ../tika-manifest.json unless overridden on the CLI.
# Idempotent: re-running install or update converges to the manifest state.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
MANIFEST="$ROOT/tika-manifest.json"
unsupported() { echo "unsupported: $*" >&2; exit 2; }
fail() { echo "error: $*" >&2; exit 1; }

[[ "$(uname -s)" == Linux ]] || unsupported 'this installer requires Linux'

command -v python3 >/dev/null || unsupported 'python3 is required to read tika-manifest.json'

manifest_value() {
  python3 - "$MANIFEST" "$1" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1]))
node = doc
for key in sys.argv[2].split('.'):
    node = node[key]
print(node if isinstance(node, str) else json.dumps(node))
PY
}

ACTION="${1:-install}"; shift || true
JAVA_REF="$(manifest_value java.install_version)"
JAR_URL="$(manifest_value tika.jar_url)"
JAR_URL_TEMPLATE="$(manifest_value tika.jar_url_template)"
JAR_SHA512="$(manifest_value tika.jar_sha512)"
JAR_NAME="$(manifest_value tika.jar_filename)"
MIN_JAVA_MAJOR="$(manifest_value java.min_major)"
REMOVE_TARGET=all

while (($#)); do
  case "$1" in
    --java-version) JAVA_REF=$2; shift 2 ;;
    --tika-version) JAR_NAME="tika-app-$2.jar"; JAR_URL="${JAR_URL_TEMPLATE//\{version\}/$2}"; JAR_SHA512=""; shift 2 ;;
    --sha512) JAR_SHA512=$2; shift 2 ;;
    --jar-only) REMOVE_TARGET=jar; shift ;;
    --java-only) REMOVE_TARGET=java; shift ;;
    --help|-h) sed -n '2,12p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) unsupported "unknown argument: $1" ;;
  esac
done

CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/filetype-detector"
JAR_PATH="$CACHE_DIR/$JAR_NAME"
JABBA_DIR="${JABBA_HOME:-$HOME/.jabba}"

tika_sha() { sha512sum "$1" | awk '{print $1}'; }

jar_ok() { [[ -f $JAR_PATH && ( -z $JAR_SHA512 || $(tika_sha "$JAR_PATH") == "$JAR_SHA512" ) ]]; }

java_major() {
  command -v java >/dev/null || { echo 0; return; }
  java -version 2>&1 | sed -n 's/.*version "\([0-9]*\).*/\1/p' | head -1
}

ensure_jabba() {
  if command -v jabba >/dev/null; then return; fi
  [[ -s "$JABBA_DIR/jabba.sh" ]] && source "$JABBA_DIR/jabba.sh" && command -v jabba >/dev/null && return
  echo "installing jabba..."
  curl -fsSL https://github.com/Jabba-Team/jabba/raw/main/install.sh | bash -s -- --skip-rc
  source "$JABBA_DIR/jabba.sh"
}

ensure_java() {
  local major; major="$(java_major)"
  if (( major >= MIN_JAVA_MAJOR )); then
    echo "java already present (major=$major); skipping jabba install"
    return
  fi
  ensure_jabba
  echo "installing Java via jabba: $JAVA_REF"
  jabba install "$JAVA_REF"
  jabba alias default "$JAVA_REF" >/dev/null
  local newest; newest="$(jabba ls | tail -1 | tr -d ' ')"
  export JAVA_HOME="$JABBA_DIR/jdk/$newest"
  export PATH="$JAVA_HOME/bin:$PATH"
  major="$(java_major)"
  (( major >= MIN_JAVA_MAJOR )) || fail "installed Java major $major < required $MIN_JAVA_MAJOR"
  echo "java ready: $(java -version 2>&1 | head -1)"
}

ensure_jar() {
  if jar_ok; then echo "jar already verified: $JAR_PATH"; return; fi
  [[ -n $JAR_SHA512 ]] || fail "no SHA-512 for $JAR_NAME; pass --sha512 or pin the version in tika-manifest.json"
  mkdir -p "$CACHE_DIR"
  local tmp="$JAR_PATH.download"
  echo "downloading $JAR_URL"
  curl -fsSL "$JAR_URL" -o "$tmp"
  if [[ $(tika_sha "$tmp") != "$JAR_SHA512" ]]; then
    rm -f "$tmp"; fail "JAR SHA-512 mismatch; refusing to install"
  fi
  mv -f "$tmp" "$JAR_PATH"
  echo "jar installed and verified: $JAR_PATH"
}

do_check() {
  local ok=0
  if jar_ok; then echo "jar: OK ($JAR_PATH)"; else echo "jar: MISSING or hash mismatch"; ok=1; fi
  local major; major="$(java_major)"
  if (( major >= MIN_JAVA_MAJOR )); then echo "java: OK ($(java -version 2>&1 | head -1))"; else echo "java: missing or too old (need >= $MIN_JAVA_MAJOR)"; ok=1; fi
  return $ok
}

do_remove() {
  if [[ $REMOVE_TARGET != java ]]; then rm -f "$JAR_PATH"; echo "removed $JAR_PATH"; fi
  if [[ $REMOVE_TARGET != jar ]]; then
    echo "note: jabba keeps installed JDKs under $JABBA_DIR/jdk; run 'jabba uninstall <ref>' or remove $JABBA_DIR to purge"
  fi
}

case "$ACTION" in
  install|update) ensure_java; ensure_jar ;;
  check) do_check ;;
  remove) do_remove ;;
  *) unsupported "unknown action: $ACTION (install|update|check|remove)" ;;
esac
