#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOXYFILE = ROOT / "Doxyfile"
RESOURCES = ROOT / "resources"

BEGIN = "# BEGIN RESOURCES_INPUT (auto-generated)"
END = "# END RESOURCES_INPUT"


def list_md_files() -> list[str]:
    files: list[str] = []
    root_index = RESOURCES / "index.md"
    if root_index.exists():
        files.append(root_index.relative_to(ROOT).as_posix())
    for path in sorted(RESOURCES.glob("*/index.md")):
        rel = path.relative_to(ROOT).as_posix()
        files.append(rel)
    return files


def build_block(md_files: list[str]) -> list[str]:
    # Fixed source inputs
    tail = ["akos"]
    items = md_files + tail
    lines = [BEGIN, "INPUT                  = " + items[0] + " \\"]
    for item in items[1:]:
        lines.append(f"                         {item} \\")
    # Remove trailing backslash on last line
    lines[-1] = lines[-1].rstrip(" \\")
    lines.append(END)
    return lines


def main() -> int:
    if not DOXYFILE.exists():
        print(f"error: Doxyfile not found at {DOXYFILE}")
        return 1

    md_files = list_md_files()
    if not md_files:
        print("error: no Markdown files found under resources/")
        return 1

    content = DOXYFILE.read_text(encoding="utf-8").splitlines()
    try:
        start = content.index(BEGIN)
        end = content.index(END)
    except ValueError:
        print("error: marker block not found in Doxyfile")
        return 1

    if end <= start:
        print("error: invalid marker order in Doxyfile")
        return 1

    new_block = build_block(md_files)
    updated = content[:start] + new_block + content[end + 1 :]
    DOXYFILE.write_text("\n".join(updated) + "\n", encoding="utf-8")
    print(f"updated INPUT with {len(md_files)} Markdown files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
