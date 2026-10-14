"""Chapter 17 - Tools in Depth."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Tools in Depth"
QUESTION = """Do nested calls pass the same gate, and does `deferred` exposure keep a tool
registered but inactive?

The chapter's point: `deferred` exposure means "registered but not declared to the
model" — it stays callable from another tool's execute. And every tool call,
whether from the model or from `ctx.executeTool()`, passes through the same
`tool_call` event."""

CELLS = [
    ("md", heading(17, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "A `deferred`-exposure tool is **registered but not active** at registration — it does not appear in `getActiveToolNames()` until activated.",
                "Nested calls via `ctx.executeTool()` **pass through the same `tool_call` gate** as model-issued calls — the spy sees all three in order.",
                "A tool with `readOnlyHint: true` and `openWorldHint: false` passes the approval gate; one with **no hints is treated as destructive and open-world** and blocked when there is no UI.",
                "A non-zero exit from a command is **data, not a failed tool result** — the tool returns `isError: false` with the exit code in details.",
                "StructuredContent is returned alongside the model-facing content.",
            ],
            [
                "**Annotations are hints, not permission** — a server that lies about `readOnlyHint` passes the gate (`ch17-lim3` / `ch21-lim2`).",
                "**`registerToolRenderer` arrived in 1.0.1** and was not exercised in a running session by the chapter's suite.",
                "**No measurement** of how often a model calls a tool it was offered.",
                "**Parallel tool calls** from one assistant message can race — handlers must be independent.",
            ],
        ),
    ),
    *setup_cells(
        17,
        mode="**Run** — real sessions with the chapter's tools, approval, and dynamic-activation extensions, driven by a scripted model.",
        scope="`in_process_runtime`. The gate, exposure, activation and approval rules are Pi's.",
    ),
    (
        "md",
        """## Baseline: a command tool returns data, not errors

`run_checks` runs `pnpm typecheck` (and optionally tests). A non-zero exit is a
result, not a tool failure.""",
    ),
    (
        "code",
        'TOOLS = pinb.driver_source("ch17-tools.ts")\n'
        'tools = pinb.driver(TOOLS, label="ch17-tools", timeout=300)\n'
        'print(pinb.md_table(\n'
        '    ["tool", "isError", "exit code in details?"],\n'
        '    [["run_checks (skipTests)", tools["basic"]["isError"], "yes" if (tools["basic"].get("details", {}) or {}).get("results", [{}])[0].get("exit_code") is not None else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("run_checks returns isError: false even if the command exits non-zero",\n'
        '               not tools["basic"]["isError"], "isError: false"),\n'
        '    pinb.check("the exit code is in details.results[0].exit_code",\n'
        '               (tools["basic"].get("details", {}) or {}).get("results", [{}])[0].get("exit_code") is not None, "present"),\n'
        "])",
    ),
    (
        "md",
        """## StructuredContent: the tool returns it, but the toolResult message carries content and details

The chapter's test is named "structuredContent is returned" but only asserts on the
model-facing `content` text. The `structuredContent` field from the tool's return
value is not automatically copied to the toolResult message.""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["tool", "content text"],\n'
        '    [["failing_tests", tools["structured"]["content"][:60]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("failing_tests returns content about failing tests",\n'
        '               "failing tests" in tools["structured"]["content"], "content present"),\n'
        "])",
    ),
    (
        "md",
        """## Nested calls: review_diff runs two other tools and reads their outcomes

`review_diff` calls `run_checks` and `failing_tests` via `ctx.executeTool()`.
Both nested calls pass through the same gate.""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["tool", "isError", "nested tools seen"],\n'
        '    [["review_diff", tools["nested"]["isError"], ", ".join(tools["nested"]["nested"])]],\n'
        "))",
    ),
    (
        "code",
        'print("Gate order (what the spy saw):", " -> ".join(tools["nestedGate"]["seen"]))\n'
        'print()\n'
        'pinb.show_checks([\n'
        '    pinb.check("nested calls pass through the same tool_call gate in order",\n'
        '               tools["nestedGate"]["seen"] == ["review_diff", "run_checks", "failing_tests"],\n'
        '               " -> ".join(tools["nestedGate"]["seen"])),\n'
        '    pinb.check("review_diff reads structuredContent from failing_tests",\n'
        '               "src/auth/refresh.ts" in tools["nested"]["content"][1]["text"],\n'
        '               "structuredContent came through"),\n'
        "])",
    ),
    (
        "md",
        """## Approval gate: annotations are hints, not permission

`run_checks` declares `readOnlyHint: true, openWorldHint: false` — no approval
needed. `failing_tests` declares **no hints** — treated as destructive and
open-world, blocked without a UI.""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["tool", "isError", "why"],\n'
        '    [["run_checks (readOnlyHint)", "no" if not tools["approval"]["checksIsError"] else "yes", "no approval needed"],\n'
        '     ["failing_tests (no hints)", "yes" if tools["approval"]["failingIsError"] else "no", "blocked without UI"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("run_checks with readOnlyHint passes approval",\n'
        '               not tools["approval"]["checksIsError"], "allowed"),\n'
        '    pinb.check("failing_tests with no hints is blocked without UI",\n'
        '               tools["approval"]["failingIsError"], "blocked"),\n'
        '    pinb.check("the blocked result has a reason the model can read",\n'
        '               "not approved" in tools["approval"]["failingText"], "reason present"),\n'
        "])",
    ),
    (
        "md",
        """## Dynamic activation: deferred exposure keeps a tool registered but inactive

`failing_tests` is registered with `exposure: "deferred"`. It is not active
until `review_diff` is called, which activates it via `setActiveTools()`.""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["moment", "failing_tests in getActiveToolNames?"],\n'
        '    [["at registration", "yes" if "failing_tests" in tools["dynamic"]["initiallyActive"] else "no"],\n'
        '     ["after review_diff called", "yes" if "failing_tests" in tools["dynamic"]["afterActive"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("deferred tool is NOT active at registration",\n'
        '               "failing_tests" not in tools["dynamic"]["initiallyActive"], "inactive initially"),\n'
        '    pinb.check("deferred tool IS registered at registration",\n'
        '               "failing_tests" in tools["dynamic"]["initiallyRegistered"], "registered but not active"),\n'
        '    pinb.check("after review_diff, the deferred tool is activated",\n'
        '               "failing_tests" in tools["dynamic"]["afterActive"], "active now"),\n'
        '    pinb.check("and it is callable from another tool",\n'
        '               not tools["dynamic"]["reviewDiffIsError"], "no error"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

All seven tests from the chapter's test file.""",
    ),
    *canonical_tests(
        17,
        "ch17-tools/tools.test.ts",
        what="The chapter's canonical evidence",
        show="nested",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** Change `failing_tests` to `exposure: "hidden"` instead of
`"deferred"`. Can `review_diff` still call it via `ctx.executeTool()`?

**Then change one input.** The approval extension checks `destructiveHint`,
`readOnlyHint`, `openWorldHint`. What happens if a tool declares
`destructiveHint: false` but no `readOnlyHint`?

**Predict the boundary.** Parallel tool calls from one assistant message can run
in any order. The spy in `nestedGate` saw them sequentially because the faux
provider serialises them — what happens with a real provider that streams two
tool calls at once?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. hidden: no — a hidden tool is unreachable, even from executeTool().")\n'
        'print("  2. destructiveHint: false alone is not enough — readOnlyHint is what the gate checks.")\n'
        'print("  3. Parallel calls: handlers must be independent; order is not guaranteed.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  deferred initially active: {\"failing_tests\" in tools[\"dynamic\"][\"initiallyActive\"]}")\n'
        'print(f"  deferred after review_diff: {\"failing_tests\" in tools[\"dynamic\"][\"afterActive\"]}")\n'
        'print(f"  nested gate order: {" -> ".join(tools[\"nestedGate\"][\"seen\"])}")\n'
        "print()\n"
        'assert "failing_tests" not in tools["dynamic"]["initiallyActive"]\n'
        'assert "failing_tests" in tools["dynamic"]["afterActive"]\n'
        'assert tools["nestedGate"]["seen"] == ["review_diff", "run_checks", "failing_tests"]\n'
        'print("held: deferred means registered-but-inactive, and nested calls pass the same gate")',
    ),
    (
        "md",
        """## Interpretation

A tool is three things, and the chapter shows the boundaries:

| Property | What it controls | The boundary |
|---|---|---|
| `exposure: "direct"` | Active at registration, declared to model | The default for built-ins |
| `exposure: "deferred"` | Registered, not active, not declared | Activated by `setActiveTools()`; still callable from `executeTool()` |
| `exposure: "codemode"` | Registered, not declared, callable from scripts | The MCP default (ch 21) |
| `exposure: "hidden"` | Registered, unreachable | Never callable |

| Annotation | What it means for approval |
|---|---|
| `readOnlyHint: true, openWorldHint: false` | No approval needed — read-only, closed world |
| No hints declared | **Treated as destructive and open-world** — blocked without UI |
| Lying `readOnlyHint` | **Passes the gate** — annotations are unverified by Pi |

The practical rules:
* **Every tool call passes the same gate** — model calls and `ctx.executeTool()` both fire `tool_call`.
* **Deferred is the pattern for "internal" tools** — the model doesn't see them, but your tools can call them.
* **Annotations are hints, not permission** — chapter 21 shows a lying MCP server passes the gate.
* **Catch inside handlers** — a throwing `tool_call` handler blocks the tool (fail-safe from chapter 16).""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=17,
            mode="**Run** — real sessions with the chapter's tools, approval, and dynamic-activation extensions, driven by a scripted model.",
            scope="`in_process_runtime`. The gate, exposure, activation and approval rules are Pi's.",
            provenance=[
                "**Ran** `drivers/ch17-tools.ts`: six real sessions covering basic, structuredContent, nested, nested-gate, approval, and dynamic activation.",
                "**Ran** `ch17-tools/tools.test.ts` (7 tests).",
                "**Read** `examples/evidence.json`, chapter 17 rows (7 claims).",
            ],
            limits=[
                "**Annotations are hints, not permission.** A tool or server that lies about `readOnlyHint` passes the gate (`ch17-lim3` / `ch21-lim2`).",
                "**`registerToolRenderer` is documented-not-run** by the chapter's suite (`ch17-lim3`); it arrived in 1.0.1.",
                "**No measurement** of how often a model calls a tool it was offered.",
                "**Parallel tool calls** from one assistant message can race — the faux provider serialises them; a real provider may not.",
            ],
        ),
    ),
]