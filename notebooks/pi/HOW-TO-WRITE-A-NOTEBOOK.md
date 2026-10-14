# How to write a Pi Agents notebook companion

You are adding notebook companions to `notebooks/pi/` in the PI Agents development
repository. See [the notebook guide](README.md) for manuscript dependencies that
still require a combined checkout after the move.
Every notebook must be built **and executed green** before you report back.

Read this whole file first. Then read, in this order:

1. `cells/11-chapter.py` — a finished cell file, relative to this guide.
2. `cells/13-chapter.py` — the same, with a different shape.
3. `cells/_common.py` — the shared helpers you must use.
4. `pinb.py` — the support module (read the function list).
5. The chapter itself, and the example directory that backs it.

## The two files you write per chapter

### `notebooks/pi/drivers/chNN-<name>.ts`

A TypeScript driver. It runs **inside `examples/`** (copied to a scratch directory at
call time) so Node resolves `@earendil-works/*` from `examples/node_modules`. It
imports the book's own harness and the chapter's example files. It communicates by
**exactly one `console.log(JSON.stringify(x))`** at the end.

```ts
// Chapter NN - one sentence saying what this establishes.
import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession, UiRecorder } from "../harness/session.ts";
import myExtension from "../chNN-example/my-extension.ts";

... build the thing ...

console.log(JSON.stringify({ /* the observations the notebook asserts on */ }));
```

Rules for drivers:

* **Never re-implement a Pi rule.** Call Pi. A driver orchestrates; it does not model.
* **Assert on boundaries, not on echoes.** Request counts, files that exist or do not,
  messages stored vs messages sent, errors, protocol frames.
* **Read the filesystem** when the claim is about an effect.
* **Compute booleans in the driver** when the notebook masks machine paths (session
  files, temp dirs). A check like `/\.jsonl/.test(text)` survives masking; a check on
  the path itself does not.
* **Parameterise the exercise through `process.env`** (`NB_TOOLS`, `NB_COMMAND`, …) with
  sensible defaults, so the notebook's exercise never has to edit the driver source.
* Prefer `drivers/chNN-a.ts` + `chNN-b.ts` over one long driver when the chapter has two
  distinct experiments.
* Keep it under ~120 lines. If it is longer, the notebook should have two cells.

### `notebooks/pi/cells/NN-chapter.py`

```python
"""Chapter NN - <title>."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "..."
QUESTION = """...the one question a reader can answer by looking at the output..."""

CELLS = [
    ("md", heading(NN, TITLE, QUESTION)),
    ("md", establishes([...what it establishes...], [...what it does not...])),
    *setup_cells(NN, mode="...", scope="..."),
    ("md", "## ..."),
    ("code", 'DRIVER = pinb.driver_source("chNN-name.ts")\n...'),
    ...
    *canonical_tests(NN, "chNN-example/name.test.ts", what="...", show="keyword"),
    ("md", "## Your turn: predict, then run"),
    ("code", "# exercise\n"),
    ("md", "## Interpretation\n\n..."),
    ("md", sources_and_limits(chapter=NN, mode="...", scope="...", provenance=[...], limits=[...], unrun=[...])),
]
```

## The section shape every notebook follows

1. `heading(...)` — identity, links, the pin, where the authority lives.
2. `establishes(...)` — what this notebook establishes, and what it does **not**.
3. `setup_cells(...)` — do not write your own setup cell.
4. A baseline: the smallest real run that shows the mechanism working.
5. The experiment, with real assertions (`pinb.show_checks`).
6. A contrasting / failure case.
7. `canonical_tests(...)` — run the chapter's own test files.
8. `## Your turn: predict, then run` — one prediction, one input to change, one question.
9. Interpretation — connect the output back to the chapter's practical decision.
10. `sources_and_limits(...)`.

## The `pinb` API you may use

```
pinb.driver_source(name)            # read a driver from notebooks/pi/drivers/
pinb.driver(src, label=, timeout=, env=, keep=)   # run it, return the parsed JSON
pinb.run_tests(patterns, timeout=)  # node --test, TAP parsed
pinb.show_tap(result, files=, show=)              # report a canonical run
pinb.show_checks([pinb.check(label, cond, detail)])  # report assertions
pinb.table(headers, rows, indent=)   # fixed-width, printed
pinb.md_table(headers, rows)          # markdown, printed
pinb.diagram(lines, title=)           # ASCII box, printed
pinb.bars(rows, width=)               # ASCII bars, printed
pinb.evidence_rows(chapter)           # rows from examples/evidence.json
pinb.evidence_versions()
pinb.chapter_file(n) / chapter_text(n) / chapter_title(n) / chapter_headings(n)
pinb.chapter_metadata(n) / metadata_block(n, key)
pinb.workspace(prefix)                # a temp dir, removed on exit
pinb.live_status()                    # (enabled, reason) for optional live sections
pinb.unrun(title, reason)             # print an honest NOT RUN block
pinb.show_environment(title) / pinb.environment() / pinb.self_check()
pinb.rel(path) / pinb.mask(text)      # no absolute machine paths in output
pinb.PIN                               # "1.0.4"
pinb.NB_DIR / pinb.REPO / pinb.EXAMPLES / pinb.EVIDENCE_JSON
```

Output rules:

* Never print an absolute path. Use `pinb.rel()` or a `<tmp>`-style label.
  `pinb.mask()` is applied to driver payloads and subprocess output automatically.
* Every code cell must run top-to-bottom in a fresh kernel with no cell above it
  needed out of order.
* Assertions must be strict by default (`show_checks` raises on failure). If a result is
  genuinely platform-dependent, use `strict=False` **and say why in a markdown cell**.

## Verifying your work

```powershell
cd notebooks/pi
python tools\lint_cells.py          # catches the "" typo at the end of a markdown cell
python tools\build.py 14 15 16     # writes NN-chapter.ipynb
python tools\execute.py 14 15 16   # fresh kernel, allow_errors=False
```

Both must be clean. `execute.py` prints one line per notebook and `N/N notebooks
PASSED`. Do not report done until it says that. If a driver fails, fix the driver; if
an assertion fails, **check whether your assertion or your expectation was wrong** —
never weaken an assertion to make it pass, and never change a chapter to fit the
output. If the chapter and the code genuinely disagree, say so in your report and in
`NOTEBOOK-FINDINGS`-style language inside the notebook's limits.

## Content rules that are not negotiable

* The pin is **1.0.4**. Never read the globally installed Pi as authority. Never
  change `examples/package.json`.
* **The model is scripted** (`faux`). Everything you run is evidence about the code
  *around* a model, never about model behaviour. Say so in the notebook.
* Distinguish **recorded inspection** from **fresh execution**. If you read preserved
  evidence (a recorded trace, `evidence.json`, a metadata block), say that is what you
  did.
* If a chapter has **no example directory** (`ch02`, `ch06`, `ch10`, `ch30`), say so
  explicitly and use the evidence that does exist — usually another chapter's tests
  plus this notebook's own driver runs. Do not pretend the chapter has evidence it
  does not have.
* If something is **documented but not run**, mark it as such. Chapter 42's container
  and VM recipes are documented, not run. Nothing may claim otherwise.
* Prefer one honest `Inspect/reproduce` or `Demonstrate` notebook over a fabricated
  result. A notebook that inspects old evidence says "recorded on 1.0.2, from the
  published experience" and does not present it as current.

## What to report back

For each chapter: the reader's question in one line, the execution mode, the evidence
scope, the canonical example/test file you ran, the assertion boundaries you used, and
anything surprising — especially any place where **the code and the chapter's prose
disagree**, or where a version-sensitive claim (1.0.1 / 1.0.2 / 1.0.3 / 1.0.4) turned
out to be wrong or unverifiable.
