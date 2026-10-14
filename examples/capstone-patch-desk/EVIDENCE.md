# Pi Patch Desk evidence

Recorded **14 October 2026** in the public `pi-agents` checkout. These are new
capstone observations; the existing `examples/EVIDENCE.md` and `evidence.json`
historical reports were not regenerated or changed.

Environment: Windows, Node **v25.8.2**, TypeScript **5.9.3**. Installed
`@earendil-works/pi-ai`, `pi-agent-core`, and `pi-coding-agent` were all **1.0.4**.
The global `pi --version` returned **1.2.0**, so it was not used for grounding
or running this capstone. Node 22.19 compatibility is the documented prerequisite,
not an additional observed run here.

## Commands actually executed

All npm commands below ran from `examples/`.

| Command | Observed result |
|---|---|
| `npm run capstone` | Exit 0; `verified`; original fixture tests exit 1, repaired tests/typecheck/host grader exit 0; seven artifacts written |
| `npm run typecheck` | Final check exit 0, including capstone modules and tests |
| `npm test` | Final run exit 0: **311 tests, 311 pass, 0 fail, 0 skip**; includes all **32 capstone tests** |
| `node --test capstone-patch-desk/surfaces.test.ts` | Exit 0; **3/3** Pi command, resource-loading, and JSON-driver tests |
| `node --test ch22-packages/packages.test.ts` | Exit 0; **11/11** while diagnosing the earlier full-suite failure |
| `npm run verify-examples` | Exit 1 after successful typecheck: `ENOENT` for `content/books/pi`; no embedded-code verification or subsequent test stage performed by this command |
| `npm run capstone:interactive` | Launched shipped Pi **v1.0.4** in a terminal; `/patch-desk` showed `verified`, `/patch-desk injection` showed `refused`; exited normally with Ctrl+D |
| `git diff --check` | Exit 0 |

Earlier full-suite runs are not represented as successes: one had an existing
chapter-22 JSON parsing failure, which passed in isolation and the final run.
Another caught interference in the new worktree-status assertion from Pi's
concurrent atomic settings temporary file. The test now excludes that specific
temporary filename pattern and compares tracked content through `git diff --binary
HEAD`, as well as checking the original fixture. The final full run passed.

The interactive success dossier was generated at `runs/run-53hlw4/`, with
7 requests, 7 tool calls, completed=true, originalUnchanged=true, applied=false.
The interactive injection dossier at `runs/run-HZKgfT/` recorded refused,
2 requests, 1 executed tool call, and the rejected extra/nested/approval arguments.
These run folders are local gitignored outputs; regenerate them with the commands
above rather than treating their machine-specific paths as public download links.

## Documented APIs reused — declarations are the authority

| API | Pinned source inspected | Capstone use |
|---|---|---|
| `Agent`, `AgentTool`, `beforeToolCall`, `prepareRequest`, `subscribe`, `abort`, `waitForIdle` | `pi-agent-core/dist/agent.d.ts`, `dist/types.d.ts`, and the package README | Real loop, typed tools, central gate, request budget, completion and cooperative cancellation |
| `createModels`, `fauxProvider`, `fauxToolCall`, `fauxAssistantMessage` | `pi-ai/dist/` exports and `dist/providers/faux.d.ts` | Known scripted responses through actual Pi execution |
| `registerCommand`, `DefaultResourceLoader` | `pi-coding-agent/dist/core/extensions/types.d.ts`, `dist/core/resource-loader.d.ts`, and `docs/sdk.md` | Optional interactive command and explicit reader resources |
| Resource flags and `/` substitutions | `pi-coding-agent/docs/cli.md`, `prompt-templates.md`, `skills.md`, `sdk.md` | Clean launcher, explicit prompt/skill loading, repeatable walkthrough |

The exported package metadata is resolved from each ESM entry and checked at
startup. The coding-agent's shipped binary is resolved through its actual `bin.pi`
mapping by the existing `harness/cli.ts`. SDK sessions do not automatically load
the CLI's built-in MCP extensions in the pinned release; the main workflow uses
agent-core directly. The optional launcher explicitly uses both `--no-mcp` and
`--no-extensions`, with only two known extensions explicitly loaded.

## Observed claims and tests

These have evidence scope **in_process_runtime**, except the manual terminal
walkthrough which also exercised the **shipped_binary**. They measure scripted
control flow; none have `real_model` scope.

- The known baseline fails, Pi edits only the two approved files, and final
  fixture checks plus the host-owned independent grader pass.
- Git produces an applicable patch; `git apply --check` succeeds against a
  separate disposable fixture. Repeated scripted runs produce identical patches
  and normalized status/check outcomes.
- Forbidden files, traversal, Windows-style paths, aliases, extra approval
  fields, nested-call arguments, source injection instructions, and symlink/
  junction escapes cannot produce their prohibited effects in the tested cases.
- Nonexistent/altered source citations, out-of-range line references, and empty
  conclusions fail. Mutable tests that simply pass do not override the failing
  independent host grader.
- Failed tests, provider error, model refusal, invalid submission, unsupported
  check command, request/tool exhaustion, abort, and slow-stream timeout produce
  failure dossiers and no application to the originals.
- An actual otherwise-continuing Node child is killed by cancellation; its PID
  no longer exists after `runProcess()` resolves. Output overflow also kills the
  child and bounds capture. Pi's faux stream is separately tested for cancellation.
- Logs and total artifact bytes remain within the recorded per-run caps in all
  cases. Raw transcripts are omitted; common credential-shaped strings are redacted.
- The real Pi command makes no outer model request and waits for the shared
  host workflow to complete. The JSON driver's last completion record follows
  Pi completion, host checks, and dossier creation. Missing optional display
  helpers do not control verification.

## Proposed patterns and unmeasured work

The exact file/tool allowlist, central application policy, independent grader,
artifact schema, resource limits, and human review procedure are **PROPOSED**
host design choices. Their tested implementation is observed; Pi does not promise
that these choices constitute containment or universal correctness.

Isolation achieved: temporary copies, explicit host tools, fixed subprocess
argument arrays, and a child environment without inherited provider credentials.
**No OS sandbox was configured or verified.** Executing changed TypeScript retains
the OS account's permissions. Timeouts cover the fixed direct child and cooperative
faux stream; they do not promise termination of hostile descendant process trees.
Execution has a 30-second budget, followed by bounded reporting/diff collection.
Reports are capped per run and retained until explicitly deleted; cumulative
retained runs are not capped. Redaction is not a general secret detector.

Real-model execution/evaluation, arbitrary repository input, and automatic patch
application are not implemented. Real-model quality, general injection recognition,
pass@1/pass^k, Node 22 execution, private manuscript embedding/navigation, and a Hugo
build were not measured. The private repository was not modified. A future chapter
can reference the public README, code, and this evidence record.

## File inventory

New public capstone files: `README.md`, this evidence record, `run.ts`, `policy.ts`,
`process.ts`, `checks.ts`, `grader.ts`, `evidence.ts`, `script.ts`, `cli.ts`,
`interactive.ts`, `extension.ts`, `desk.test.ts`, `surfaces.test.ts`, the four
`fixture/` files, `prompts/fix-verified.md`, and `skills/pi-patch-desk/SKILL.md`.
Updated repository files: root `.gitignore` and `README.md`, plus
`examples/README.md`, `package.json` (scripts only), and `tsconfig.json`.
The existing top-level design/implementation prompts, Pi pins, package lock,
historical chapter evidence, and private manuscript files were left unchanged.
