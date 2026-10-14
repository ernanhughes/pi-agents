# Local Codex implementation brief — Pi Agents capstone

## Assignment

Implement a runnable, evidence-backed end-to-end capstone for the *Pi Agents* book in `https://github.com/ernanhughes/pi`, using the detailed companion specification **`pi-patch-desk-capstone-design.md`**. Read that specification in full before touching code.

The project is **Pi Patch Desk**: a developer submits a bug report for a tiny committed TypeScript repository fixture, Pi investigates and produces a minimal patch in an isolated working copy, a deterministic host runs checks, and the user receives a reviewable patch and evidence dossier. **Human approval is separate. No automatic commit, push, PR or production deployment.**

## Read first; do not assume API details

1. Inspect `AGENTS.md`, `README.md`, `examples/README.md`, `examples/package.json`, `examples/verify.mjs`, `content/books/pi/_index.md`, chapters 11, 16, 17, 20, 21, 31–42, and `planning/` notes on evidence and real-model tests.
2. Review and reuse the existing `examples/ch36-model-access`, `ch37-agent-core`, `ch38-typed-step`, `ch39-seams`, `ch40-composition`, `ch41-testing` and shared harness modules. Avoid copying them into a second divergent implementation.
3. Inspect **installed** `@earendil-works/pi-ai`, `pi-agent-core`, and `pi-coding-agent` **1.0.4** declarations/docs under `examples/node_modules/`. Use `npm ci` if dependencies are not installed. Do not substitute upstream package names or change the package pin.
4. Confirm the book's executable-evidence rules and chapter embedding markers. Keep all technical claims classified as **DOCUMENTED**, **OBSERVED**, or **PROPOSED**.
5. Inspect current `git status`. Preserve unrelated changes. No commits or pushes unless explicitly requested.

## Scope and delivery sequence

**Phase 1 — implement one runnable vertical slice before any enhancements.** Create a small local repository fixture with a specifically failing test for `parseRecords()` blank-line handling. Make a Node CLI / script, callable from the `examples/` package, that:

- creates a fresh disposable run workspace and records the pristine fixture revision;
- uses scripted `fauxProvider` responses to drive **actual Pi loop/tool behavior** (not a handcrafted fake trace);
- inspects the fixture, makes the documented minimal change in the disposable copy, runs the real test/typecheck commands through a fixed host allowlist, and collects the exact patch;
- writes `manifest.json`, `run.json`, `tests.json`, `evidence.json`, bounded `events.jsonl`, `patch.diff`, and `review.md`;
- marks successful outcomes solely from deterministic host checks and source references, not model prose;
- leaves the original fixture and original repository completely unchanged.

Start with the smallest implementation able to satisfy this. The initial offline demonstration must not require a network, API keys, MCP servers, global Pi installation, or a UI. The runner must use Pi 1.0.4's documented API calls and the actual fixture files; do not write an agent simulator.

**Phase 2 — enforce and test refusals.** Add tests for out-of-scope path, symlink/path traversal, nested tool-call bypass, malicious prompt instructions in repository content, nonexistent citations, empty citations on a conclusive answer, failed tests, model refusal/errors, abort, and budget exhaustion. All failure states must yield evidence and never apply a patch to the real repository. Tool-selection restriction and in-process `beforeToolCall`/`tool_call` checks are defense-in-depth and **not** a claim of containment. The host must hold policy outside mutable workspace files.

**Phase 3 — demonstrate Pi as an application.** Expose the *same* workflow through an appropriate prompt template and skill, a minimal extension or host tool if actually necessary, and a deterministic headless event/JSON driver. Include a straightforward interactive walkthrough. A terminal UI component is optional and must be omitted unless it materially improves operation; do not create one for decorative completeness. Do not duplicate core logic across interactive and headless paths.

**Phase 4 — only after scripted success, optional real-model path.** Design an explicitly opted-in, credentialed run against only an isolated disposable fixture with verified restrictions and limits. Record model/provider identification, Pi version, requests, tokens/usage when available, and every failure. Ensure a watchdog terminates underlying work on timeout (not just a rejected Promise). Define a held-out evaluation suite with an independent grader and report `pass@1` and `pass^k` without implying independent samples when they are not. Keep the real-model path out of ordinary CI and do not claim real-model success without actual runs.

**Phase 5 — book chapter.** Add a reader-facing, unnumbered **Capstone: Pi Patch Desk** manuscript page, plus any required metadata, navigation and links. Keep 42 existing numbered chapters and appendix paths intact. Determine ordering through actual Hugo configuration rather than using a speculative fractional weight. The chapter must demonstrate the one-command offline run, expected artifacts, both a successful run and a prohibited action, major architecture choices, code embedded with the repository's `<!-- example: ... -->` / `<!-- excerpt: ... -->` marker discipline, tests, and limitations. Update `examples/README.md`, the main index, and the example verifier as required by the existing conventions. Avoid treating this as an unrelated product inside the book repo.

## Constraints that must not be weakened

- Pi release/pin: `@earendil-works/*` at **1.0.4** unless a separate explicit re-grounding is authorized.
- Minimize context and log growth. Bounded artifacts, explicit retention, no ambient context mutation, no always-on third-party plugins, and no silent external service calls.
- Clean provider and extension environment for runs; default with MCP disabled. Consult the pinned docs: `--tools` alone does **not** reliably remove MCP tools in 1.0.4.
- Avoid arbitrary `bash` execution for checks; use a fixed approved set of test commands. Agent-authored shell strings are not commands the host should trust.
- Do not treat an agent-managed temp directory or Git worktree as a security boundary. Confirm the actual sandbox/OS controls or qualify the run's limits visibly.
- No access to production credentials, home-directory files, unrelated user repositories, or network beyond narrowly approved model calls in the optional isolated real-model mode.
- Any operation modifying real user files must be a distinct, explicit human-authorized step and is outside the default demo.
- Fail closed if required policy, isolation, verification, or evidence hooks fail to initialize. Optional display helpers may degrade without blocking the workflow.
- Keep a single central decision function for authorization of all tool operations; test nested calls and aliases for bypasses. Model-provided `approved` flags, tool annotations, and `replay: safe` do not confer authority.
- Deterministic checks prove scripted control flow, never spontaneous real-model behavior. The evidence ledger must say so.
- Keep docs truthful; if an API or technique cannot be verified in the pinned release, narrow the claim rather than invent a feature.
- No autonomous retries across the entire pipeline; explicit, bounded retry budget owned at one layer.

## Success criteria — gate before saying complete

- A single documented command under `examples/` runs the full scripted fixture demonstration and returns a useful set of files without credentials.
- Test runner actually executes the fixture's failing test first and the corrected test and typecheck after editing, recording real exit codes.
- `patch.diff` only references allowed fixture files and can be reviewed without opening the transcript.
- Deterministic tests cover the refusal cases, model/tool failure and abort, and clean original-worktree invariants.
- Real `npm run verify-examples` passes after any embedded-code changes, and Hugo builds with the new capstone page.
- A generated `review.md` clearly distinguishes **verified**, **source-supported**, and **not measured** claims.
- All resource growth is capped: model/tool calls, turns, time, artifact bytes and logs; timeout behavior is tested at least once with work that would otherwise continue.
- Book page makes the end-to-end user benefit immediately visible before teaching the parts.
- Do not claim `pass@1`, `pass^k` or real-model reliability without actual real-model evaluation.

## Required report from Codex

At the end, provide: modified/new file inventory; command the reader runs; exact tested commands and results; output artifact example; documented Pi APIs reused and evidence; tested failure modes; any unsupported or untested feature clearly marked; isolation actually achieved; limitations and next steps. Say explicitly if the task is only partially complete. Do not conceal failing checks behind a summary.

**Build the vertical slice first. Avoid creating a large generic framework, multi-agent orchestration, a database, an event bus, or a plugin system. The book needs one complete and trustworthy demonstration.**
