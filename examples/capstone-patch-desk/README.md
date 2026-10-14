# Pi Patch Desk

Give Pi a small parser bug and receive a proposed patch with a review dossier.
The host reproduces the failure, Pi inspects and edits a disposable fixture, and
the host checks the result. You decide whether to accept the patch.

This is the public capstone for *Pi Agents: Building on the Coding Agent*.
The private book can reference this directory from a future chapter. No book
checkout, API key, global Pi install, or network is needed after dependencies
are installed. All Pi packages remain pinned to **1.0.4**.

## Run the complete example

From a clone of `pi-agents`, install once, then run:

```sh
cd examples
npm ci
npm run capstone
```

Requirements: Node.js 22.19+, npm, and Git on PATH. The recorded development
run used Node 25.8.2 on Windows; Node 22 itself has not been rerun for this capstone.

Expected progression:

```text
before tests: exit 1
Pi completed read_file
Pi completed read_file
Pi completed write_file
Pi completed write_file
after tests: exit 0
Pi completed check
after typecheck: exit 0
Pi completed check
Pi completed submit
after tests: exit 0
after typecheck: exit 0
after grader: exit 0

Pi Patch Desk: verified
Review: .../examples/capstone-patch-desk/runs/run-<id>
Original fixture unchanged; no patch applied.
```

Open `review.md` in the printed directory, then `patch.diff` and `tests.json`.
The patch adds a blank-line guard to `parseRecords()` and a regression for
leading/trailing whitespace-only lines and CRLF. The original intentionally
broken fixture stays broken so the next reader can reproduce the same issue.
No commit, push, PR, or patch application is performed.

## See a refusal

```sh
npm run capstone -- --scenario injection
```

This deliberately exits **1** and reports `refused`. Pi reads a README containing
an instruction to disable tests and print secrets; the next scripted response
tries to edit `package.json` and supplies a fake `approved: true`. Host policy
rejects it. Inspect `run.json` and the denied policy event in `events.jsonl`.
This demonstrates a host refusal, not a model recognizing an injection.

Other scenarios are listed by the CLI's usage message and in `script.ts`. They
include bad/empty citations, failed or weakened tests, provider error, model
refusal, invalid output, aliases/nested calls, traversal, a symlink escape,
stream cancellation, timeout, and request/tool budget exhaustion.

## Follow the evidence

| File | What it records |
|---|---|
| `manifest.json` | Pi/package versions, Node version, Git revision plus exact original fixture hashes, policy, budgets, isolation and retention |
| `run.json` | Completed-run status, timestamps, requests, turns, tool counts, failures, and whether originals changed |
| `tests.json` | Exact command argument arrays, child exit codes/signals, bounded output, Node and TypeScript versions |
| `evidence.json` | Validated file/line/quotation references and the limits of the claims |
| `events.jsonl` | One compact log of Pi lifecycle, host checks, and policy decisions; no token transcript |
| `patch.diff` | Git-generated diff restricted to the two editable fixture files; failures may include an incomplete proposal |
| `review.md` | Verified, source-supported, and not-measured findings, followed by the human decision |

`verified` requires the baseline failure, a completed Pi run, nonempty exact
citations, final tests and typecheck, independent host acceptance checks, an
allowed nonempty patch, and unchanged originals. Model prose cannot set it.
A citation proves that quoted source exists at a line range; it does not prove
that every interpretation of that source is true.

Each run has a new disposable copy and output directory. Temporary copies are
removed after reporting. Dossiers are gitignored and retained until you delete
the reviewed run directories. The limit is **128 KiB per dossier**, not a cap on
all accumulated run directories. Runs allow at most 12 requests, 12 turns, 16
executed tool calls, 16 KiB per fixture file, 160 compact events/24 KiB of logs,
and 16 KiB of combined output per child. Check-output overflow kills the child.
The execution watchdog is 30 seconds; bounded patch collection/reporting follows,
with at most 3 seconds per file for Git diff. No pipeline retry is performed.

Git revision and working-tree fixture hashes are both recorded. The hashes,
not an assumption that an uncommitted fixture belongs to HEAD, identify the input.

## Architecture and code to read

```text
issue → disposable fixture → baseline failure
      → actual Pi loop: read → edit → fixed checks → source submission
      → final host tests + typecheck + independent grader
      → patch + dossier → human review
```

Start with `fixture/src/records.ts` and `fixture/tests/regression.ts`. Then read:

| Module | One responsibility |
|---|---|
| `script.ts` | Offline faux-provider responses, including adversarial scenarios |
| `policy.ts` | Central authorization decision for exact tools, paths and arguments |
| `process.ts` | Fixed child-process execution, minimal environment, cancellation and output bounds |
| `checks.ts` | Test/typecheck/grader command allowlist |
| `grader.ts` | Host-owned acceptance assertions that mutable fixture tests cannot remove |
| `evidence.ts` | Exact source validation and bounded-text redaction |
| `run.ts` | One end-to-end host workflow, Pi tools, budgets, patch collection and dossier |
| `cli.ts` | Human-readable and JSON presentations of that workflow |
| `extension.ts` | Optional Pi `/patch-desk` command calling the same workflow |

The source checker reuses chapter 40's `citationsAreReal()` and adds nonempty,
path, range, and exact-current-source checks. It does not change that chapter's
historical example or evidence. The launcher reuses the shared harness's shipped
binary mapping; tests reuse `makeSession()` and `UiRecorder` for a real Pi session.
No second implementation of the Pi loop or generic orchestration framework is used.

## Headless and interactive walkthroughs

For newline-delimited JSON without npm's script banner:

```sh
node capstone-patch-desk/cli.ts --json
```

`desk_completed` is the last driver record, emitted after Pi settles, host
verification completes, and artifacts are written. The Pi `agent_end` event
alone does not mean the host has verified the patch. Ctrl+C requests cancellation
and writes a failure dossier; force-killing the process cannot guarantee a report.

The optional interactive launcher uses the **locally installed shipped Pi 1.0.4
binary**, a fresh agent configuration directory, a faux provider, no outer tools,
no MCP, and only the explicit capstone resources:

```sh
npm run capstone:interactive
```

In its Pi editor, enter `/patch-desk`, inspect the printed review directory, then
enter `/patch-desk injection` to see a refusal. Each command calls `runDesk()`;
the surrounding Pi session makes no model request for these commands.
Exit Pi when done. No custom terminal UI is required.

The explicit prompt `prompts/fix-verified.md` and skill
`skills/pi-patch-desk/SKILL.md` carry the reader procedure. They can be loaded
in a configured Pi session with `--prompt-template` and `--skill`, then invoked
as `/fix-verified` or `/skill:pi-patch-desk`. The offline launcher loads them for
inspection, but its scripted outer provider does not interpret the walkthrough
or execute arbitrary commands. Use `/patch-desk` to run the fixture there.

## Verify and understand the limits

```sh
npm run test:capstone
npm run typecheck
npm test
```

The tests execute Pi, real fixture commands, and an actual otherwise-continuing
child killed by the watchdog. They check patch applicability, repeatability,
original-worktree invariants, refusals, source gates, all seven artifacts,
output limits, credential-shaped redaction, and interactive/headless completion.
The intentionally failing fixture uses `regression.ts`, not `*.test.ts`, so it
is executed deliberately by the host rather than collected as a failing book test.

The manuscript marker checker (`npm run verify-examples`) still requires
`content/books/pi/` in this repository. Those private files are absent. Standalone
code checks remain `typecheck` and `test`; this capstone does not bypass the marker
checker or claim a Hugo build. See `EVIDENCE.md` for observed results.

**Isolation actually achieved:** separate temporary files, exact application
policy, no inherited provider credentials in children, and a known faux provider.
The policy lives in host code outside mutable fixture files. Raw completed calls,
the Pi `beforeToolCall` hook, and immediate tool effects use the same decision.
Unknown aliases, extra approval fields, and nested dispatch are rejected.

**No OS sandbox is present.** Changed TypeScript executes in child checks with
your OS account's filesystem/network permissions. A temporary folder and an
in-process hook do not contain hostile code. This version accepts only its known
fixture and scripted responses; it has no arbitrary-repository or real-provider
mode. Common secret-shaped text is redacted and raw model messages are omitted;
this is not a guarantee of detecting every possible secret encoding.

**Not measured:** real-model quality, general injection recognition, security
for arbitrary code, pass@1, or pass^k. Any future real-model mode needs verified
external containment, explicit opt-in, provider budgets, and a held-out evaluation
with an independent grader. A private manuscript chapter can reference the public
code and its recorded evidence; manuscript integration is a separate task.
