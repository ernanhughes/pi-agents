"""Build the Pi Agents notebook companions from their per-chapter cell sources.

Each chapter's cells live in ``notebooks/pi/cells/NN-chapter.py`` as a
``CELLS`` list. A cell is ``("md", text)`` or ``("code", source)``. Keeping the
cells as importable Python means a notebook is built, validated and executed
by the same code path a reader gets, and a syntax error surfaces before the
reader ever opens the file.

    python tools/build.py            # write every NN-chapter.ipynb
    python tools/build.py 04 31      # only those chapters

Notebook identity, provenance and the setup cell are injected here so that all
44 notebooks declare the pin, the evidence scope and the repository marker the
same way, in one place.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
NB_DIR = HERE.parent
CELLS_DIR = NB_DIR / "cells"

sys.path.insert(0, str(NB_DIR))
sys.path.insert(0, str(CELLS_DIR))
import pinb  # noqa: E402

TITLE_RE = None


def load_cells(chapter: int) -> list[tuple[str, str]]:
    path = CELLS_DIR / f"{chapter:02d}-chapter.py"
    if not path.is_file():
        raise FileNotFoundError(f"No cell source for chapter {chapter}: {path}")
    spec = importlib.util.spec_from_file_location(f"nbcells_{chapter:02d}", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cells = getattr(mod, "CELLS", None)
    if not isinstance(cells, list) or not cells:
        raise ValueError(f"{path} must define a non-empty CELLS list")
    for c in cells:
        if not (isinstance(c, tuple) and len(c) == 2 and c[0] in ("md", "code")):
            raise ValueError(f"{path}: every cell must be ('md', str) or ('code', str); got {c!r}")
    return cells


def _as_source(text: str) -> list[str]:
    """nbformat stores source as a list of lines that each keep their newline."""
    if text == "":
        return []
    lines = text.splitlines(keepends=True)
    if not lines[-1].endswith("\n"):
        pass  # a final line without a newline is valid and preserved as-is
    return lines


def build(chapter: int) -> Path:
    title = pinb.chapter_title(chapter)
    cells = load_cells(chapter)
    out_cells: list[dict[str, Any]] = []
    for i, (kind, text) in enumerate(cells):
        if kind == "md":
            out_cells.append({"cell_type": "markdown", "id": f"c{i:02d}", "metadata": {}, "source": _as_source(text)})
        else:
            out_cells.append(
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "id": f"c{i:02d}",
                    "metadata": {},
                    "outputs": [],
                    "source": _as_source(text),
                }
            )

    nb = {
        "cells": out_cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": pinb.python_version(),
            },
            "pi_notebook": {
                "book": "Pi Agents",
                "book_slug": "pi",
                "chapter": chapter,
                "chapter_file": pinb.rel(pinb.chapter_file(chapter)),
                "chapter_title": title,
                "pinned_pi_version": pinb.PIN,
                "support_module": "notebooks/pi/pinb.py",
                "runtime": "Python orchestrates; Pi runs in Node against examples/node_modules",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    dest = NB_DIR / f"{chapter:02d}-chapter.ipynb"
    dest.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return dest


def main(argv: list[str]) -> int:
    chapters = [int(a) for a in argv] if argv else list(range(1, 45))
    for ch in chapters:
        dest = build(ch)
        print(f"built {dest.name:20s} {pinb.chapter_title(ch)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))