#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOXYFILE="$ROOT_DIR/Doxyfile"
OUT_DIR="$ROOT_DIR/out"

usage() {
  cat <<'USAGE'
Usage: ./build_docs.sh [--clean] [--pdf]

Options:
  --clean   Remove previous output before running doxygen
  --pdf     Build the PDF output from the bootcamp Markdown pages
USAGE
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if ! command -v doxygen >/dev/null 2>&1; then
  echo "error: doxygen is not installed or not on PATH" >&2
  exit 1
fi

if [ ! -f "$DOXYFILE" ]; then
  echo "error: Doxyfile not found at $DOXYFILE" >&2
  exit 1
fi

# Validate required assets referenced by Doxyfile.
for f in \
  "$ROOT_DIR/doxygen/awesome_doxygen/header.html" \
  "$ROOT_DIR/doxygen/awesome_doxygen/doxygen-awesome.css" \
  "$ROOT_DIR/doxygen/awesome_doxygen/doxygen-awesome-sidebar-only.css" \
  "$ROOT_DIR/doxygen/awesome_doxygen/doxygen-awesome-darkmode-toggle.js" \
  "$ROOT_DIR/doxygen/awesome_doxygen/doxygen-awesome-fragment-copy-button.js" \
  "$ROOT_DIR/doxygen/awesome_doxygen/doxygen-awesome-paragraph-link.js" \
  "$ROOT_DIR/doxygen/awesome_doxygen/doxygen-awesome-nav-sync.js" \
  "$ROOT_DIR/resources/search.html" \
  "$ROOT_DIR/resources/extra_style.css"
do
  if [ ! -f "$f" ]; then
    echo "error: missing required file: $f" >&2
    exit 1
  fi
done

if [ "${1:-}" = "--clean" ]; then
  rm -rf "$OUT_DIR/html" "$OUT_DIR/latex"
  exit 1
elif [ "${1:-}" = "--pdf" ]; then
  python3 "$ROOT_DIR/scripts/update_doxy_inputs.py"
  python3 "$ROOT_DIR/scripts/build_pdf_doxyfile.py"
  PDF_DOXYFILE="$OUT_DIR/Doxyfile.pdf"
  trap 'rm -f "$PDF_DOXYFILE"' EXIT
  rm -rf "$OUT_DIR/latex"
  echo "Generating PDF docs..."
  doxygen "$PDF_DOXYFILE"
  perl -0pi -e 's/\\begin\{center\}%\n/\\begin{center}%\n  \\includegraphics[width=4cm]{.\/ak_logo.png}\\\\[2ex]\n/' "$OUT_DIR/latex/refman.tex"
  make -C "$OUT_DIR/latex"
  echo "Done. PDF output: $OUT_DIR/latex/refman.pdf"
  exit 0
fi

python3 "$ROOT_DIR/scripts/update_doxy_inputs.py"

echo "Generating docs..."
doxygen "$DOXYFILE"
echo "Done. Output: $OUT_DIR/html/index.html"
