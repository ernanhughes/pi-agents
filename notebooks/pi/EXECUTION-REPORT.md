# EXECUTION-REPORT — Pi Agents notebook companions

This historical report was carried into the [development repository](../../README.md)
from the combined book checkout. It has not been rerun after migration; see
[the notebook guide](README.md) for current manuscript dependencies.

Report of the actual execution of all 44 notebook companions in fresh kernels,
with runtime versions, execution modes, and what was left unrun. Every notebook
was executed top-to-bottom in one fresh kernel with `allow_errors=False` via
`notebooks/pi/tools/execute.py`; saved outputs are genuinely from those runs.

## Runtime used for this report

| Component | Version |
|---|---|
| Python | 3.13.15 (kernel `python3`) |
| Node | v25.8.2 (type-stripping runs the examples directly) |
| `@earendil-works/pi-ai` | **1.0.4** |
| `@earendil-works/pi-agent-core` | **1.0.4** |
| `@earendil-works/pi-coding-agent` | **1.0.4** |
| Platform | win32 |
| Model | faux (scripted) — no credential, no network |

The Node pin matches the manuscript (AGENTS.md and `examples/package.json`).

## Results at a glance

| Nb | Mode | Result | What ran | Unrun / limits |
|---|---|---|---|---|
| 01 | Run | PASS | ch01-agent-core + driver | scripted model only |
| 02 | Run + Manual | PASS | `pi --version`, offline `--print` runs, session groups | install itself unrun; no `--continue` |
| 03 | Run | PASS | `ModelRuntime.getAuth` + real sessions | literal keys; scripted |
| 04 | Run | PASS | `shouldCompact` across threshold, `getContextUsage` | token numbers are faux's |
| 05 | Run | PASS | three persisted JSONL sessions read directly | three turns |
| 06 | Run | PASS | tool inventory + `--tools` shipped-binary runs | no MCP server present |
| 07 | Run | PASS | `SettingsManager.create` over real files | getter ≠ loader |
| 08 | Run | PASS | Pi's trust predicate + headless `pi --print` runs | print cannot ask |
| 09 | Run (live shell) | PASS | one command both ways + alias case | shell-dependent |
| 10 | Run | PASS | shipped-binary input runs + 120 ms tool | phrasing not measured |
| 11 | Run | PASS | guard + pre-fix version, filesystem checked | guard ≠ containment |
| 12 | Run | PASS | four real sessions, captured `user` messages | substitution ≠ sandbox |
| 13 | Run | PASS | six skill fixtures + system prompt read-back | local skills filtered out |
| 14 | Run (live shell) | PASS | real git repo, `run-checks.sh`, strict/lax | six tests skip without bash |
| 15 | Run | PASS | both extensions, no-arg call | renderer documented-not-run |
| 16 | Run | PASS | guard + counting variant + throwing handler | timing/order in-process only |
| 17 | Run | PASS | tools/approval/dynamic sessions + nested gate order | annotations unverified |
| 18 | Run | PASS | active↔disabled↔re-enabled + provider prompt | `session.systemPrompt` omits section |
| 19 | Run | PASS | persisted session, model invisibility, branch nav | no size limit established |
| 20 | Run + Manual | PASS | commands in three modes + component widths | drawing unrun |
| 21 | Run | PASS | in-memory MCP server; 1.0.4 `--tools` rule | no network |
| 22 | Run | PASS | shipped binary: install/list/remove/-e/--local | no npm/git source |
| 23 | Run | PASS | custom-summary compaction + navigate back | no summary quality |
| 24 | Run | PASS | tree/fork/clone; entries vs messages; labels | summary quality unrun |
| 25 | Run | PASS | steering/follow-up/queue/modes/clearQueue | latency not measured |
| 26 | Inspect | PASS | `tsc` + static read of declaration + shipped JS | not a runtime claim |
| 27 | Run + Inspect | PASS | real session file + chapter reader child process | header version moves |
| 28 | Run | PASS | `DefaultResourceLoader` over fixture tree | merge order unspecified |
| 29 | Run | PASS | overflow normalisation, no-handler, rate-limit | retry timings unverified |
| 30 | Demonstrate | PASS | replacement test on faux + sessions | method is proposed |
| 31 | Run + Inspect | PASS | shipped binary 3 drivers + fresh 1.0.4 trace + recorded 1.0.2 | recording is historical |
| 32 | Run | PASS | 6+ shipped-binary runs; `--tools` filesystem check | `--no-mcp` needed at 1.0.4 |
| 33 | Run | PASS | LF framing, U+2028, deltas, reconstruction | representative records |
| 34 | Run | PASS | SDK: streaming, forged history, dispose | createAgentSession snippets unrun |
| 35 | Run | PASS | RPC id matching, UI subprotocol, cursor | clear_queue/abort unrun |
| 36 | Run | PASS | `assess` four ways | real-model unmeasured |
| 37 | Run + Inspect | PASS | research agent loop + miss | agent_settled reading |
| 38 | Run | PASS | step(): 7 scenarios; canonical 14 tests | bounds are proposed |
| 39 | Run + Inspect | PASS | seam order/block/rewrite + fresh trace + recorded 1.0.2 | matrix cells mostly declared |
| 40 | Run | PASS | composition routes + exact call counts | scripted control flow only |
| 41 | Run + Reproduce | PASS | pass@1 = 0.86, pass^5 = 0.45; thrown step | real-model level 3 unrun |
| 42 | Run + Inspect | PASS | replay scan + anti-vacuity | containers unrun |
| 43 | Inspect | PASS | docs count, ledger matrix, bibliography counts | no arXiv fetched |
| 44 | Run + Manual | PASS | pi-tui width funcs + ch20 component tests | layers 1–2 NOT RUN |

**44/44 notebooks execute PASS** with `allow_errors=False` — confirmed by a single
fresh-kernel top-to-bottom run of the whole set (see `tools/execution-notebooks.json`).
Fastest chapter 1.1 s (43), slowest 13.6 s (08); the whole set passes without a
cell left unexecuted.

## Execution and evidence scope, reported separately

| Scope | Notebooks | Notes |
|---|---|---|
| **Run** (fresh execution) | 01–25, 27–29, 31–42, 44 | The output was produced by this run |
| **Inspect** (recorded / static) | 26 (`tsc` + static), 31 & 39 (the 1.0.2 recordings), 43 (ledger/docs counts) | Artifacts named; recordings labelled historical |
| **Demonstrate** | 30 | The book's proposed method, on real machinery |
| **Manual / optional live (NOT RUN)** | 02 (install), 20 (drawing), 42 (containers/VM), 44 (layers 1–2) | Written as a checklist with prerequisites; reported NOT RUN |
| **`real_model`** | none | The book has no accepted real-model evidence |

A notebook can pass an evidence-inspection run while its optional live section
remains **NOT RUN** — that is the intended state, and each such notebook says so
in its sources-and-limits cell.

## Skipped / optional cells

- **Chapter 02**: the actual install of Pi is a manual step (the binary and the
  pinned packages are already in `examples/`); the notebook reports it as the
  one thing it does not do.
- **Chapter 20**: drawing the custom screen in a real terminal is manual.
- **Chapter 31 / 39**: the published 1.0.2 recording is inspected only when its
  directory is present (default sibling guess, or `PIN_EXPERIENCES`); otherwise
  reported NOT INSPECTED.
- **Chapter 42**: container / micro-VM / credential-proxy recipes — documented,
  not run.
- **Chapter 44**: layers 1–2 (Shift+Enter reporting, Kitty negotiation, tmux
  passthrough, hardware cursor/IME, the ≤100 ms theme timeout) — NOT RUN,
  needs the real terminal.

## Failures encountered and corrected during the build (all resolved)

All notebooks in the table above execute PASS. During development, the usual
failures were: JavaScript syntax (`===`, `?.`, `.some()` arrow bodies, `JSON.stringify`)
written into Python cells by mistake; expecting tool-result fields that the tool
result does not carry (ch 17); and assuming `truncateToWidth` returns a bare
substring (it returns styled text with an ellipsis — ch 44). Each was corrected
in the driver or the cell, and the correction is recorded in
`NOTEBOOK-FINDINGS.md` where it touches a chapter's claim.

## How to reproduce

```bash
cd examples && npm ci
python -m pip install -r ../notebooks/pi/requirements.txt
cd ..
python notebooks/pi/tools/execute.py 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 --timeout 900
```

`tools/execute.py` writes `tools/execution-notebooks.json` with the per-notebook
row (status, executed cells, outputs, errors). The saved `.ipynb` files contain
the genuine outputs from the last PASS run.
