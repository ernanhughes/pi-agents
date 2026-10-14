"""Execute the Pi Agents notebook companions in fresh kernels and save the outputs.

    python tools/execute.py                 # every chapter, cwd = the notebook directory
    python tools/execute.py --cwd repo      # the same set with cwd = the repository root
    python tools/execute.py 04 31           # only those chapters
    python tools/execute.py --timeout 900

Each notebook runs top-to-bottom in one fresh kernel with `allow_errors=False`:
a cell that raises fails the notebook, and nothing is saved as if it had passed.
A wall-clock bound is applied to every cell so a subprocess cannot hang a run.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
NB_DIR = HERE.parent
sys.path.insert(0, str(NB_DIR))
import pinb  # noqa: E402

import nbformat  # noqa: E402
from nbclient import NotebookClient  # noqa: E402
from nbclient.exceptions import CellExecutionError, CellTimeoutError  # noqa: E402


def execute_one(path: Path, cwd: Path, timeout: int) -> dict:
    nb = nbformat.read(str(path), as_version=4)
    client = NotebookClient(
        nb,
        timeout=timeout,
        kernel_name="python3",
        allow_errors=False,
        resources={"metadata": {"path": str(cwd)}},
        record_timing=True,
    )
    t0 = time.perf_counter()
    status, error = "PASS", ""
    try:
        client.execute()
    except CellTimeoutError as exc:
        status = "TIMEOUT"
        error = f"a cell exceeded {timeout}s: {exc}"
    except CellExecutionError as exc:
        status = "FAIL"
        error = str(exc)
    except Exception as exc:  # kernel start failure, bad notebook, ...
        status = "ERROR"
        error = f"{type(exc).__name__}: {exc}"
    elapsed = time.perf_counter() - t0

    nbformat.write(nb, str(path))
    code = [c for c in nb.cells if c.cell_type == "code"]
    ran = [c for c in code if c.get("execution_count") is not None]
    outputs = sum(len(c.get("outputs", [])) for c in code)
    errors = [o for c in code for o in c.get("outputs", []) if o.get("output_type") == "error"]
    tracebacks = [
        "".join(o.get("traceback", [])).replace("\x1b\\[[0-9;]*m", "") for o in errors
    ]
    return {
        "notebook": path.name,
        "chapter": int(path.name[:2]),
        "title": nb.metadata.get("pi_notebook", {}).get("chapter_title", ""),
        "cwd": pinb.rel(cwd),
        "status": status,
        "seconds": round(elapsed, 1),
        "code_cells": len(code),
        "executed": len(ran),
        "outputs": outputs,
        "error_outputs": len(errors),
        "error": pinb.mask(error)[:1500],
        "tracebacks": tracebacks,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("chapters", nargs="*", type=int)
    ap.add_argument("--cwd", choices=["notebooks", "repo"], default="notebooks")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--summary", default=None)
    args = ap.parse_args(argv)

    cwd = NB_DIR if args.cwd == "notebooks" else pinb.REPO
    chapters = args.chapters or list(range(1, 45))
    print(f"cwd: {pinb.rel(cwd)}   per-cell timeout: {args.timeout}s")
    print()

    rows = []
    for ch in chapters:
        path = NB_DIR / f"{ch:02d}-chapter.ipynb"
        if not path.is_file():
            print(f"{ch:02d}  MISSING {path.name}")
            rows.append({"notebook": path.name, "chapter": ch, "status": "MISSING"})
            continue
        row = execute_one(path, cwd, args.timeout)
        rows.append(row)
        flag = {"PASS": "ok  ", "FAIL": "FAIL", "TIMEOUT": "T/O ", "ERROR": "ERR "}[row["status"]]
        print(
            f"{ch:02d}  {flag} {row['seconds']:6.1f}s  "
            f"{row['executed']}/{row['code_cells']} cells, {row['outputs']} outputs  {row['title']}"
        )
        if row["error"]:
            print("      " + row["error"].splitlines()[0][:150])
            if row["status"] == "ERROR":
                print("      " + traceback.format_exc(limit=2).replace("\n", "\n      ")[:400])
        if row["status"] != "PASS":
            for tb in row.get("tracebacks", [])[:1]:
                print("      " + tb.replace("\n", "\n      ")[:2500])

    ok = sum(1 for r in rows if r["status"] == "PASS")
    print()
    print(f"{ok}/{len(rows)} notebooks PASSED with cwd={pinb.rel(cwd)}")
    bad = [r for r in rows if r["status"] != "PASS"]
    for r in bad:
        print(f"  {r['status']:8s} {r['notebook']}: {r.get('error', '')[:200]}")

    summary = Path(args.summary) if args.summary else HERE / f"execution-{args.cwd}.json"
    summary.write_text(
        json.dumps({"cwd": pinb.rel(cwd), "timeout": args.timeout, "rows": rows}, indent=1),
        encoding="utf-8",
    )
    print(f"\nwrote {summary.name}")
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))