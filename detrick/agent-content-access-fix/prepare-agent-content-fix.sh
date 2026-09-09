#!/usr/bin/env sh
set -eu

# Read the module from the supplied API image, refuse unknown source bytes, and
# produce a persistent host-side module plus a Compose override.  This script
# never starts an application container and never connects to the Dify database.

EXPECTED_SHA256=a55bde316d9550353d2f2b4f3c9aa83f9085cbe34cc1f01767d50c6b11c11d9c
SOURCE_PATH=/app/api/controllers/common/wraps.py
API_IMAGE=${1:?usage: $0 API_IMAGE [OUTPUT_DIR]}
OUTPUT_DIR=${2:-"$PWD/agent-content-access-fix-applied"}
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

case "$OUTPUT_DIR" in
  /*) ;;
  *) printf '%s\n' "OUTPUT_DIR must be an absolute path: $OUTPUT_DIR" >&2; exit 2 ;;
esac

if [ -e "$OUTPUT_DIR/wraps.original.py" ] || [ -e "$OUTPUT_DIR/wraps.patched.py" ]; then
  printf '%s\n' "refusing to overwrite an existing preparation directory: $OUTPUT_DIR" >&2
  exit 2
fi

umask 077
stage=$(mktemp -d "${TMPDIR:-/tmp}/dify-agent-content-fix.XXXXXX")
cleanup() {
  find "$stage" -type f -delete 2>/dev/null || true
  find "$stage" -depth -type d -empty -delete 2>/dev/null || true
}
trap cleanup EXIT HUP INT TERM

if ! docker run --rm --network none --entrypoint cat "$API_IMAGE" "$SOURCE_PATH" > "$stage/wraps.original.py"; then
  printf '%s\n' "could not read $SOURCE_PATH from image $API_IMAGE; no patch was written" >&2
  exit 3
fi

actual_sha256=$(sha256sum "$stage/wraps.original.py" | awk '{print $1}')
if [ "$actual_sha256" != "$EXPECTED_SHA256" ]; then
  printf '%s\n' "module fingerprint mismatch; expected $EXPECTED_SHA256, got $actual_sha256" >&2
  printf '%s\n' "no patched module or service change was made" >&2
  exit 4
fi

mkdir -p "$stage/app/controllers/common"
cp "$stage/wraps.original.py" "$stage/app/controllers/common/wraps.py"
chmod 0644 "$stage/app/controllers/common/wraps.py"
(cd "$stage/app" && patch --batch --forward -p1 < "$SCRIPT_DIR/common-wraps.py.patch")

if ! docker run --rm --network none --entrypoint python \
  -v "$stage/app/controllers/common/wraps.py:/tmp/wraps.py:ro" \
  "$API_IMAGE" -c 'from pathlib import Path; compile(Path("/tmp/wraps.py").read_text(), "/tmp/wraps.py", "exec")'; then
  printf '%s\n' "patched module failed the API image's Python compiler; no patch was installed" >&2
  exit 5
fi

patched_sha256=$(sha256sum "$stage/app/controllers/common/wraps.py" | awk '{print $1}')
mkdir -p "$OUTPUT_DIR"
chmod 0755 "$OUTPUT_DIR"
cp "$stage/wraps.original.py" "$OUTPUT_DIR/wraps.original.py"
cp "$stage/app/controllers/common/wraps.py" "$OUTPUT_DIR/wraps.patched.py"
chmod 0600 "$OUTPUT_DIR/wraps.original.py"
chmod 0644 "$OUTPUT_DIR/wraps.patched.py"

cat > "$OUTPUT_DIR/agent-content-access.override.yml" <<'EOF'
version: "3.8"
services:
  api:
    volumes:
      - "${AGENT_FIX_OUTPUT_DIR:?set AGENT_FIX_OUTPUT_DIR to the preparation directory}/wraps.patched.py:/app/api/controllers/common/wraps.py:ro"
  api_websocket:
    volumes:
      - "${AGENT_FIX_OUTPUT_DIR:?set AGENT_FIX_OUTPUT_DIR to the preparation directory}/wraps.patched.py:/app/api/controllers/common/wraps.py:ro"
EOF
chmod 0644 "$OUTPUT_DIR/agent-content-access.override.yml"

printf '%s\n' "source_sha256=$actual_sha256" > "$OUTPUT_DIR/manifest.txt"
printf '%s\n' "patched_sha256=$patched_sha256" >> "$OUTPUT_DIR/manifest.txt"
printf '%s\n' "source_path=$SOURCE_PATH" >> "$OUTPUT_DIR/manifest.txt"
printf '%s\n' "api_image=$API_IMAGE" >> "$OUTPUT_DIR/manifest.txt"
chmod 0644 "$OUTPUT_DIR/manifest.txt"

printf '%s\n' "prepared=$OUTPUT_DIR"
printf '%s\n' "source_sha256=$actual_sha256"
printf '%s\n' "patched_sha256=$patched_sha256"
printf '%s\n' "next=read README.md; set AGENT_FIX_OUTPUT_DIR=$OUTPUT_DIR before Compose config/recreate"
