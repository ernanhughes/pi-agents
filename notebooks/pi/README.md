# Pi Agents — Jupyter notebook companions

These companions live in the [PI Agents development repository](../../README.md).
Read [the book online](https://programmer.ie/books/pi/); its manuscript is
maintained separately in the `pi` repository.

**Migration status:** the current support module requires a combined root with
`content/books/pi/` and the pinned packages in `examples/node_modules/`. Some
cells also read manuscript metadata and recorded site assets. Those book files
are not included here, so a standalone clone cannot yet execute the whole set.
`PIN_REPO` selects a combined checkout; it does not bridge separate manuscript
and examples roots. Use the original combined layout until the support code
accepts separate locations. The execution report records the original runs,
not a rerun after the move.

One executable Jupyter notebook per chapter of *Pi Agents*: `01-chapter.ipynb`
through `44-chapter.ipynb` (42 chapters plus Appendices A and B).

A notebook exists to move you from a chapter to a concrete question: run or
inspect an experiment, change an input, and see what the result establishes. It
demonstrates **its own** chapter — it does not repeat the prose and it does not
run a generic example.

## What the notebooks are

| Thing | What it is |
|---|---|
| Kernel | **Python 3** — presents, tables, checks, orchestrates |
| Pi | **Node/TypeScript**, called through the real pinned packages |
| Model | **scripted** (`faux`) — no network, no credential, no cost |
| Authority | `examples/node_modules/@earendil-works/*` at **1.0.4** (`declarations` beat prose) |
| Claim ledger | `examples/evidence.json` — the book's `claim_class` × `evidence_scope` |
| Published experiences | `/tools/ai/pi/31-chapter/` and `39-chapter/` — the two browser replays, inspected as *recorded* evidence |

**There is no Python re-implementation of Pi's loop, context loader, session
projection, permissions or protocol anywhere in this set.** Every Pi rule that
appears is demonstrated by the book's own code under `examples/`, called through
Node. Python only orchestrates, formats and asserts.

## Prerequisites

| Requirement | Why | Check |
|---|---|---|
| **Python 3.11+** | The notebooks' kernel | `python --version` |
| **Node.js 22.19+** | Type-stripping runs the examples directly | `node --version` |
| **pinned npm packages** | `@earendil-works/pi-*` at **1.0.4** | `cd examples && npm ci` |
| A POSIX shell (`bash`) where noted | ch 9, 14 — shell/exit-code rows | `bash --version` |

## Install

```bash
cd examples
npm ci            # the pinned pi-ai / pi-agent-core / pi-coding-agent @ 1.0.4
cd ..
python -m pip install -r notebooks/pi/requirements.txt
```

The Node packages come from the book's existing pin and lockfile. The Python
side is deliberately minimal: `nbformat`, `nbclient`, `ipykernel` and friends.
There is no plotting or dataframe library, because nothing in the set needs one.

## Run a notebook

Any notebook server works — `jupyter lab`, `jupyter notebook`, VS Code. A
notebook runs correctly with the working directory set either to
`notebooks/pi/` or to the repository root; `pinb.py` finds the repo from the
marker (an ancestor containing `content/books/pi/` *and*
`examples/node_modules/@earendil-works/pi-coding-agent`). Override with
`PIN_REPO`; `PIN_NOTEBOOKS` overrides the notebook directory.

Run the cells top to bottom in a fresh kernel. Nothing depends on cells executed
out of order; the setup cell in every notebook checks the pin and the ledger.

### Executing the whole set from a fresh kernel (the way the reports were made)

```bash
python notebooks/pi/tools/build.py       # writes every NN-chapter.ipynb
python notebooks/pi/tools/execute.py     # fresh kernel, allow_errors=False, saves outputs
```

`execute.py` prints one line per notebook and `N/N notebooks PASSED`. If a driver
fails, fix the driver; if an assertion fails, check whether the assertion or the
expectation was wrong — never weaken an assertion to make it pass, and never
change a chapter to fit output.

## The chapter index

| Nb | Chapter | Reader's question answered by the output | Mode |
|---|---|---|---|
| 01 | The Loop You Are Writing For | What ends one turn, and where is that decision visible? | Run |
| 02 | Install, First Session, First Task | Is the working directory the identity key for discovery *and* resume? | Run + Manual (install unrun) |
| 03 | Models and Thinking Level | With four credential sources, which wins, and does the key form matter? | Run |
| 04 | The Context Window Is a Budget | Is compaction arithmetic? Find the exact turn. | Run |
| 05 | Sessions and Where They Live | Which lines are on disk and which ever reach the model? | Run |
| 06 | The Built-In Tools | What does a plain session have, and what does `--tools` remove? | Run |
| 07 | Settings and Where Configuration Comes From | Scalars replace, lists merge — can a project file switch off your config? | Run |
| 08 | The Project .pi Directory and Trust | Which project paths are gated, and who decides? | Run |
| 09 | Shells, Processes, and Environment Variables | Do the model's `bash` and your `!` share an environment? | Run (live shell) |
| 10 | Writing a Task Pi Can Finish | What actually reaches the first prompt, and where does a mid-turn message land? | Run |
| 11 | Four Ways to Change Pi | Which rules can a person wave through, and what does a blocked call do? | Run |
| 12 | Prompt Templates | What reached the provider, and who saw the raw text first? | Run |
| 13 | Skills | Does the context carry the body, or only enough to decide? | Run |
| 14 | Skills That Carry Files | Which repository does a bundled script resolve, and does `set -euo pipefail` matter? | Run (live shell) |
| 15 | Your First Extension | Does registering a `direct` tool make it active, and does `{}` validate? | Run |
| 16 | Events and the Extension Lifecycle | With no UI to ask, does a guard leave the filesystem untouched? | Run |
| 17 | Tools in Depth | Do nested calls pass the same gate, and does `deferred` stay inactive? | Run |
| 18 | Changing What Pi Knows | Does an active-tool section disappear when the tool is disabled? | Run |
| 19 | Extension State and Persistence | Does a `custom` entry ever reach the model, and does it follow the branch? | Run |
| 20 | Slash Commands and Custom UI | Are `hasUI` and `mode === "tui"` different guards? | Run + Manual (drawing) |
| 21 | MCP Servers | Does a bare-name gate miss `mcp__jira__transition_issue`, and does a lie pass? | Run |
| 22 | Packages: Shipping an Agent | Does `pi install ./pkg` record a relative path and copy nothing? | Run |
| 23 | Compaction | After compaction, which history did the next request contain, and what is still in the file? | Run |
| 24 | Branching and Forking | What is still in the tree, what stops reaching the model, what does a fork write? | Run |
| 25 | Steering, Queuing, and Changing Direction | Where does a queued message land relative to a turn's tool calls? | Run |
| 26 | Message Types | Do the types match the declarations, and does `SystemMessage.replace` exist? | Inspect |
| 27 | The Session File Format | Is it JSONL with a header, and two timestamp formats on one field name? | Run + Inspect |
| 28 | Context Admission Is Application Policy | Which `AGENTS.md` are admitted, and does an override stay local? | Run |
| 29 | Failures, Retries, and Recovery | Does a normalised overflow compact-and-retry, and leave a `context_edit`? | Run |
| 30 | Debugging by Layer | Which layer does a symptom survive when the layer below is replaced? | Demonstrate |
| 31 | The Interface Is Not the Agent | Do print, JSON and RPC give the same answer and events? | Run + Inspect (recorded 1.0.2) |
| 32 | Headless Pi | Is a failure an exit status or only in the stream — and does `--tools` stop `bash`? | Run |
| 33 | The JSON Event Stream | Is the framing LF-only, and do three reconstruction levels agree? | Run |
| 34 | SDK Sessions | Does assigning `agent.state.messages` change what is sent? | Run |
| 35 | RPC | Does a successful `prompt` mean *finished*, and does the UI subprotocol block? | Run |
| 36 | Model Access Without the Coding Agent | Can one `complete()` become a typed value, and what breaks the schema? | Run |
| 37 | The Agent Core on Its Own | One prompt → four messages and exactly two requests? | Run + Inspect |
| 38 | A Stochastic Step Is a Typed Function | Does `maxTurns` hold *after* a valid submission in a mixed batch? | Run |
| 39 | Seams, Hooks, and Irreversible Decisions | In what order do the hooks fire; can a block undo, a rewrite not? | Run + Inspect (recorded 1.0.2) |
| 40 | Composing Agent Operations | What is each route's exact request cost, and does the check stop a citation? | Run |
| 41 | Testing Stochastic Software | How far apart are pass@1 and pass^5, and what does the gap hide? | Run + Reproduce |
| 42 | Authority, Isolation, and What Makes an Agent Worth Building | Can a self-chosen value gate the inspection? | Run + Inspect |
| 43 | Appendix A — References and Further Reading | What does the pin contain and what does the ledger record? | Inspect |
| 44 | Appendix B — The Terminal Interface, in Detail | Which of the six layers can be checked without a terminal? | Run + Manual (layers 1–2) |

### Execution modes

| Mode | Meaning |
|---|---|
| **Run** | The pinned runtime is executed (the chapter's example or a notebook driver calling the same packages and harness). Output is from this execution. |
| **Inspect/reproduce** | Preserved evidence is read and a result derived/checked from it. The artifact's version and provenance are named. A recording is never presented as a current run. |
| **Demonstrate** | A deterministic illustration of a pattern **this book proposes**, clearly labelled. Chapter 30 is the only chapter in this category. |
| **Manual/optional live** | Needs a terminal, container, credential or real model. Written as a checklist; reported **NOT RUN** unless actually run. |

## Evidence limitations

- **The model is scripted everywhere.** A notebook shows that the code *around* a
  model is correct — never how a real model behaves. Request counts are exact for
  the scripted control flow only.
- **Recorded ≠ fresh.** The published browser experiences (ch 31, 39) were
  captured on **Pi 1.0.2** and stay labelled 1.0.2. The notebooks regenerate a
  *fresh* 1.0.4 trace from the chapter's own exporters, and inspect the old
  recording (when present) as historical.
- **`real_model` scope is empty.** The book has no accepted real-model evidence.
  Optional live sections, if added by a reader, must be explicitly enabled
  (`PIN_LIVE=1`), state prerequisites and cost, and take credentials from the
  environment — never from a cell.
- **Documented-not-run stays documented-not-run.** Anything marked
  `documented-not-run` in the book (e.g. `registerToolRenderer`, `onPayload`) is
  not executed here.
- **Containers and micro-VMs are not containment evidence.** Chapter 42 labels
  them unrun unless actually exercised; a schematic sandbox is not a proof.

## Layout

```text
notebooks/pi/
  NN-chapter.ipynb      the deliverable (built + executed, outputs saved)
  pinb.py               shared support: locate repo, run drivers, tables, checks
  drivers/chNN-*.ts     real TypeScript drivers, run inside examples/ by Node
  cells/NN-chapter.py   per-chapter cell sources (CELLS list)
  tools/build.py        cells -> ipynb
  tools/execute.py      fresh-kernel execution, allow_errors=False
  tools/lint_cells.py   cell lint
  requirements.txt      minimal Python deps
  NOTEBOOK-PLAN.md      the chapter map
  EXECUTION-REPORT.md   actual results, versions, skipped/optional cells
  NOTEBOOK-FINDINGS.md  discrepancies between prose, code and evidence
```
