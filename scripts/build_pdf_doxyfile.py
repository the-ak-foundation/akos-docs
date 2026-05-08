#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOXYFILE = ROOT / "Doxyfile"
PDF_DOXYFILE = ROOT / "out" / "Doxyfile.pdf"
RESOURCES = ROOT / "resources"

BEGIN = "# BEGIN RESOURCES_INPUT (auto-generated)"
END = "# END RESOURCES_INPUT"


def build_pdf_input() -> list[str]:
    items: list[str] = []
    root_index = RESOURCES / "index.md"
    if root_index.exists():
        items.append(root_index.relative_to(ROOT).as_posix())
    for path in sorted(RESOURCES.glob("*/index.md")):
        items.append(path.relative_to(ROOT).as_posix())
    return items


def main() -> int:
    if not DOXYFILE.exists():
        print(f"error: Doxyfile not found at {DOXYFILE}")
        return 1

    content = DOXYFILE.read_text(encoding="utf-8").splitlines()
    pdf_inputs = build_pdf_input()
    if not pdf_inputs:
        print("error: no Markdown files found under resources/")
        return 1

    try:
        start = content.index(BEGIN)
        end = content.index(END)
    except ValueError:
        print("error: marker block not found in Doxyfile")
        return 1

    if end <= start:
        print("error: invalid marker order in Doxyfile")
        return 1

    pdf_block = [BEGIN, "INPUT                  = " + pdf_inputs[0] + " \\"]
    for item in pdf_inputs[1:]:
        pdf_block.append(f"                         {item} \\")
    pdf_block[-1] = pdf_block[-1].rstrip(" \\")
    pdf_block.append(END)

    overrides = {
        "GENERATE_HTML": "GENERATE_HTML          = NO",
        "GENERATE_LATEX": "GENERATE_LATEX         = YES",
        "LATEX_OUTPUT": "LATEX_OUTPUT           = latex",
        "FILE_PATTERNS": "FILE_PATTERNS          = *.md",
        "INPUT_FILTER": "INPUT_FILTER           =",
        "FILTER_PATTERNS": "FILTER_PATTERNS        =",
        "SOURCE_BROWSER": "SOURCE_BROWSER         = NO",
        "INLINE_SOURCES": "INLINE_SOURCES         = NO",
        "EXTRACT_ALL": "EXTRACT_ALL            = NO",
        "EXTRACT_PRIVATE": "EXTRACT_PRIVATE        = NO",
        "EXTRACT_PRIV_VIRTUAL": "EXTRACT_PRIV_VIRTUAL   = NO",
        "EXTRACT_PACKAGE": "EXTRACT_PACKAGE        = NO",
        "EXTRACT_STATIC": "EXTRACT_STATIC         = NO",
        "EXTRACT_LOCAL_CLASSES": "EXTRACT_LOCAL_CLASSES  = NO",
        "EXTRACT_LOCAL_METHODS": "EXTRACT_LOCAL_METHODS  = NO",
        "EXTRACT_ANON_NSPACES": "EXTRACT_ANON_NSPACES   = NO",
        "SHOW_FILES": "SHOW_FILES             = NO",
        "SHOW_NAMESPACES": "SHOW_NAMESPACES        = NO",
        "SHOW_INCLUDE_FILES": "SHOW_INCLUDE_FILES     = NO",
        "EXAMPLE_PATH": "EXAMPLE_PATH           =",
        "EXAMPLE_PATTERNS": "EXAMPLE_PATTERNS       =",
        "EXAMPLE_RECURSIVE": "EXAMPLE_RECURSIVE      = NO",
        "EXCLUDE": "EXCLUDE                =",
        "EXCLUDE_PATTERNS": "EXCLUDE_PATTERNS       =",
        "EXCLUDE_SYMBOLS": "EXCLUDE_SYMBOLS        =",
        "RECURSIVE": "RECURSIVE              = YES",
    }

    out: list[str] = []
    for line in content[:start] + pdf_block + content[end + 1 :]:
        key = line.split("=", 1)[0].strip() if "=" in line else ""
        if key in overrides:
            out.append(overrides[key])
            continue
        out.append(line)

    PDF_DOXYFILE.parent.mkdir(parents=True, exist_ok=True)
    PDF_DOXYFILE.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {PDF_DOXYFILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
