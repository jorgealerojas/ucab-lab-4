#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="${1:-$REPO_ROOT/build}"

command -v zip >/dev/null 2>&1 || { echo "ERROR: falta zip" >&2; exit 1; }
mkdir -p "$OUTPUT_DIR"
OUTPUT_DIR="$(cd "$OUTPUT_DIR" && pwd)"
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT

mkdir -p "$TEMP_DIR/faas" "$TEMP_DIR/api" "$TEMP_DIR/iaas"
cp "$REPO_ROOT/app/common/processor.py" "$TEMP_DIR/faas/processor.py"
cp "$REPO_ROOT/app/faas/lambda_function.py" "$TEMP_DIR/faas/lambda_function.py"
cp "$REPO_ROOT/app/common/processor.py" "$TEMP_DIR/api/processor.py"
cp "$REPO_ROOT/app/data_api/lambda_function.py" "$TEMP_DIR/api/lambda_function.py"
cp "$REPO_ROOT/app/common/processor.py" "$TEMP_DIR/iaas/processor.py"
cp "$REPO_ROOT/app/iaas/worker.py" "$TEMP_DIR/iaas/worker.py"

rm -f "$OUTPUT_DIR/faas-worker.zip" "$OUTPUT_DIR/data-api.zip" "$OUTPUT_DIR/iaas-worker.tar.gz"
(cd "$TEMP_DIR/faas" && zip -q "$OUTPUT_DIR/faas-worker.zip" lambda_function.py processor.py)
(cd "$TEMP_DIR/api" && zip -q "$OUTPUT_DIR/data-api.zip" lambda_function.py processor.py)
tar -czf "$OUTPUT_DIR/iaas-worker.tar.gz" -C "$TEMP_DIR/iaas" worker.py processor.py

for artifact in faas-worker.zip data-api.zip iaas-worker.tar.gz; do
  test -s "$OUTPUT_DIR/$artifact" || { echo "ERROR: artefacto vacio: $artifact" >&2; exit 1; }
done
echo "Artefactos creados en $OUTPUT_DIR"
