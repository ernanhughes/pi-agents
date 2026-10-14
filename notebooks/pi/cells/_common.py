"""Shared cell templates for the Pi Agents notebook companions.

Every notebook declares its identity, its pin, its execution mode and its
evidence provenance the same way. Keeping that text here means there is one
place to be wrong, and one place to fix.

Per-chapter cells live in ``cells/NN-chapter.py`` as ``CELLS``.
"""

from __future__ import annotations

BOOK = "Pi Agents"
BOOK_URL = "/books/pi/"
SITE = "https://programmer.ie"


# --------------------------------------------------------------------------
# Markdown fragments
# --------------------------------------------------------------------------
def heading(chapter: int, title: str, question: str) -> str:
    slug = f"{chapter:02d}-chapter"
    return f"""# Chapter {chapter:02d} — {title}

**Companion to *{BOOK}*** · [`{BOOK}` chapter {chapter:02d}]({SITE}{BOOK_URL}{slug}/)

| | |
|---|---|
| Chapter | `{slug}.md` · weight {chapter} · `{BOOK_URL}{slug}/` |
| Notebook | `notebooks/pi/{slug}.ipynb` |
| Pin | `@earendil-works/pi-*` **{_pin()}** (`examples/package.json`) |
| Ground truth | `docs/*.md` and `dist/*.d.ts` **at the pin**, under `examples/node_modules/` |

> **Where the authority lives.** Every claim below is checked against the
> packages installed under `examples/node_modules/@earendil-works/`, not against
> a globally installed Pi and not from memory. When prose and an exported
> declaration disagree, the declaration wins.

## The question

{question}
"""


def _pin() -> str:
    from importlib import import_module

    return import_module("pinb").PIN


def establishes(does: list[str], does_not: list[str]) -> str:
    rows = "\n".join(f"- {d}" for d in does)
    rows2 = "\n".join(f"- {d}" for d in does_not)
    return f"""## What this notebook establishes

{rows}

## What this notebook does **not** establish

{rows2}
"""


def sources_and_limits(
    *,
    chapter: int,
    mode: str,
    scope: str,
    provenance: list[str],
    limits: list[str],
    unrun: list[str] | None = None,
) -> str:
    rows = ["- " + p for p in provenance]
    lim = "\n".join(f"- {x}" for x in limits)
    out = f"""## Sources, execution mode and limitations

**Execution mode:** {mode}

**Evidence scope:** {scope}

### What was read or run

{chr(10).join(rows)}

### Limitations

{lim}
"""
    if unrun:
        out += "\n### Optional work that was NOT run\n\n" + "\n".join(f"- {u}" for u in unrun) + "\n"
    out += f"""
Every technical statement in this notebook is about Pi **{_pin()}**. A later
release can change any of it; the book's drift protocol in `AGENTS.md` is the
procedure for finding out whether it did.
"""
    return out


# --------------------------------------------------------------------------
# The setup cell - identical in every notebook, on purpose
# --------------------------------------------------------------------------
SETUP = '''# --- Locate the shared support module and the pinned packages -----------------
# Two documented markers, both overridable:
#   PIN_REPO       -> the checkout of the pi repository
#   PIN_NOTEBOOKS  -> this notebook directory
# Because both searches walk upwards from the working directory, this cell
# works whether you launched Jupyter from notebooks/pi/ or from the repo root.
import sys
from pathlib import Path


def _find_support() -> Path:
    for c in (Path.cwd(), *Path.cwd().parents):
        if (c / "pinb.py").is_file():
            return c
        nested = c / "notebooks" / "pi"
        if (nested / "pinb.py").is_file():
            return nested
    raise SystemExit(
        "Could not find notebooks/pi/pinb.py from " + str(Path.cwd()) + ".\\n"
        "Open this notebook from notebooks/pi/, or set PIN_NOTEBOOKS."
    )


sys.path.insert(0, str(_find_support()))
import pinb  # noqa: E402  (a local module, deliberately after the path fix)

pinb.self_check()
'''

SETUP_PRINT = '''pinb.show_environment("This notebook's runtime")

print()
print("Repository marker: an ancestor directory holding both")
print("  content/books/pi/                          (the manuscript)")
print("  examples/node_modules/@earendil-works/pi-coding-agent   (the pin)")
print("Every path below is shown relative to that repository; no absolute")
print("path is printed, so the saved output is portable.")
print()
print(pinb.md_table(
    ["resource", "repository-relative path"],
    [["manuscript", pinb.rel(pinb.chapter_file(CHAPTER))],
     ["examples tree", "examples/"],
     ["claim ledger", "examples/evidence.json"],
     ["pinned docs", "examples/node_modules/@earendil-works/pi-coding-agent/docs/"],
     ["pinned declarations", "examples/node_modules/@earendil-works/*/dist/"],
     ["support module", "notebooks/pi/pinb.py"]],
))
'''


def canonical_tests(
    chapter: int,
    files: str | list[str],
    *,
    what: str,
    show: str | None = None,
    timeout: int = 300,
) -> list[tuple[str, str]]:
    """A cell that executes the chapter's own tests in examples/.

    This is the book's canonical evidence run, not a re-implementation of it:
    `node --test` with Node's own runner and TAP output, parsed here. The
    assertion boundaries live in the test file; this cell runs them and reports
    what happened.
    """
    pattern = files if isinstance(files, str) else files
    shown = f', show="{show}"' if show else ""
    label = pattern if isinstance(pattern, str) else ", ".join(pattern)
    return [
        (
            "md",
            f"""## {what}

These are the chapter's own tests, executed unmodified through Node's test
runner. Every ledger row the chapter quotes comes from a named case in this
file, so running it here is running the chapter's evidence, not a copy of it.""",
        ),
        (
            "code",
            f"PATTERNS = {pattern!r}\n"
            f"tap = pinb.run_tests(PATTERNS, timeout={timeout})\n"
            f"pinb.show_tap(tap, files={label!r}{shown})",
        ),
    ]


def setup_cells(chapter: int, mode: str, scope: str) -> list[tuple[str, str]]:
    return [
        ("md", f"""## Setup

This notebook runs the book's own examples. **Pi is Node/TypeScript**; Python
only presents, orchestrates and checks. There is no Python re-implementation
of Pi's loop, context loader, session projection, permissions or protocol
anywhere in this set — where a mechanism is demonstrated, the code that runs is
the code in `examples/`.

* **Execution mode:** {mode}
* **Evidence scope:** {scope}
* **Credentials:** none. The model is a scripted stand-in (`faux`) supplied by
  the book's harness, so nothing here reaches the network, spends money, or
  says anything about how a real model behaves.
"""),
        ("code", SETUP),
        ("code", SETUP_PRINT.replace("CHAPTER", str(chapter))),
    ]