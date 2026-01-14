#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd "$(dirname "$0")/.." && pwd)
OUT_DIR="$ROOT_DIR/docs"
TEX_FILE="$OUT_DIR/analysis.tex"

if ! command -v xelatex >/dev/null 2>&1; then
  echo "xelatex not found in PATH" >&2
  exit 1
fi

if ! command -v rsvg-convert >/dev/null 2>&1; then
  echo "rsvg-convert not found in PATH (install librsvg)" >&2
  exit 1
fi

rm -rf "$ROOT_DIR/svg-inkscape"
rm -f "$OUT_DIR/analysis.aux" \
  "$OUT_DIR/analysis.log" \
  "$OUT_DIR/analysis.out" \
  "$OUT_DIR/analysis.toc"

xelatex --shell-escape -output-directory="$OUT_DIR" "$TEX_FILE"
xelatex --shell-escape -output-directory="$OUT_DIR" "$TEX_FILE"

rm -rf "$ROOT_DIR/svg-inkscape"
rm -f "$OUT_DIR/analysis.aux" \
  "$OUT_DIR/analysis.log" \
  "$OUT_DIR/analysis.out" \
  "$OUT_DIR/analysis.toc"
