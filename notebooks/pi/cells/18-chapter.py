"""Chapter 18 - Changing What Pi Knows."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Changing What Pi Knows"
QUESTION = """Does a section derived from *active* tools disappear when the tool is disabled,
while `getAllTools()` still reports it?

The chapter's point: the system prompt describes the **active** set, not the
registered set. `getAllTools()` reports everything registered; `getActiveTools()`
reports what the model can actually call. The two disagree exactly when a tool
is registered but not active."""

CELLS = [
    ("md", heading(18, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "The `tool_guidance` section is derived from **active tools only** — a tool that is not active is not described.",
                "A section derived from an active tool **disappears when the tool is disabled** and **reappears when re-enabled** — the condition is evaluated per run.",
                "`getAllTools()` reports the **registered** set; `getActiveTools()` reports the **active** set. They disagree exactly when a tool is registered but not active.",
                "`agent_before_settle` can append a `custom_message` entry and return `continue: true` — exactly one continuation, not a loop.",
            ],
            [
                "**`session.systemPrompt` omits the section on 1.0.4** — observed, and the reason the provider's copy is read instead of the session's (`ch18-lim1`).",
                "**No token cost measured** for the tool guidance section (`ch18-lim2`).",
                "**The settle-guard only nudges once** — the `custom_message` entry is a guard against an infinite loop.",
                "**The chapter's tests use `--tools` to filter at registration**, but the active/disabled case uses `setActiveTools()` which is different — `tools` on the session filters at registration, so `run_checks` would never be registered there.",
            ],
        ),
    ),
    *setup_cells(
        18,
        mode="**Run** — real sessions walking active → disabled → re-enabled, reading the provider's system prompt via `systemPromptSeenByProvider`.",
        scope="`in_process_runtime`. The active-set rule and `agent_before_settle` behaviour are Pi's.",
    ),
    (
        "md",
        """## Baseline: the tool_guidance section comes from active tools

`prompt-customizer` reads `options.selectedTools` and builds a section only for
tools that are active.""",
    ),
    (
        "code",
        'KNOW = pinb.driver_source("ch18-knowledge.ts")\n'
        'know = pinb.driver(KNOW, label="ch18-knowledge", timeout=300)\n'
        'print(pinb.md_table(\n'
        '    ["session", "has tool_guidance?", "has read?", "has bash?"],\n'
        '    [["all tools active", "yes" if know["promptCustomizer"]["hasToolGuidance"] else "no", "yes" if know["promptCustomizer"]["hasRead"] else "no", "yes" if know["promptCustomizer"]["hasBash"] else "no"],\n'
        '     ["only read active", "yes" if know["promptCustomizerOnlyRead"]["hasRead"] else "no", "yes" if know["promptCustomizerOnlyRead"]["hasRead"] else "no", "yes" if know["promptCustomizerOnlyRead"]["hasBash"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("tool_guidance section is delivered when tools are active",\n'
        '               know["promptCustomizer"]["hasToolGuidance"], "section present"),\n'
        '    pinb.check("only active tools are described: read yes, bash no",\n'
        '               know["promptCustomizerOnlyRead"]["hasRead"] and not know["promptCustomizerOnlyRead"]["hasBash"], "read yes, bash no"),\n'
        "])",
    ),
    (
        "md",
        """## The review-guard section: appears when `run_checks` is active, disappears with it

`review-guard-section` checks `pi.getActiveTools()` for `run_checks`. It deletes
the section rather than leaving stale content.""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["session", "has review_guard section?"],\n'
        '    [["tools + review_guard_section (run_checks active)", "yes" if know["reviewGuardWithTool"]["hasSection"] else "no"],\n'
        '     ["review_guard_section alone (run_checks not registered)", "yes" if know["reviewGuardWithoutTool"]["hasSection"] else "no"],\n'
        '     ["tools + review_guard_section, tools=[read, run_checks] (active)", "yes" if know["reviewGuardActive"]["hasSection"] else "no"],\n'
        '     ["tools + review_guard_section, tools=[read] (disabled)", "yes" if know["reviewGuardDisabled"]["hasSection"] else "no"],\n'
        '     ["tools + review_guard_section, tools=[read, run_checks] (re-enabled)", "yes" if know["reviewGuardReenabled"]["hasSection"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("with tools, run_checks is active and section appears",\n'
        '               know["reviewGuardWithTool"]["hasSection"], "appears"),\n'
        '    pinb.check("without tools, section does not appear",\n'
        '               not know["reviewGuardWithoutTool"]["hasSection"], "absent"),\n'
        '    pinb.check("with tools but only read active, section is absent",\n'
        '               not know["reviewGuardDisabled"]["hasSection"], "absent when disabled"),\n'
        '    pinb.check("re-enabling run_checks makes section reappear",\n'
        '               know["reviewGuardReenabled"]["hasSection"], "reappears"),\n'
        "])",
    ),
    (
        "md",
        """## The accessor probe: `getAllTools()` vs `getActiveTools()`

The two accessors disagree exactly when a tool is registered but not active.""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["accessor", "includes run_checks?"],\n'
        '    [["before narrowing (active)", "yes" if "run_checks" in (know["accessor"]["beforeNarrow"] or []) else "no"],\n'
        '     ["getAllTools() (registered)", "yes" if "run_checks" in (know["accessor"]["registered"] or []) else "no"],\n'
        '     ["getActiveTools() after narrowing (active)", "yes" if "run_checks" in (know["accessor"]["active"] or []) else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("before narrowing, run_checks is active",\n'
        '               "run_checks" in (know["accessor"]["beforeNarrow"] or []), "active initially"),\n'
        '    pinb.check("getAllTools() reports run_checks (registered)",\n'
        '               "run_checks" in (know["accessor"]["registered"] or []), "registered"),\n'
        '    pinb.check("getActiveTools() does NOT report run_checks (not active)",\n'
        '               "run_checks" not in (know["accessor"]["active"] or []), "not active after narrowing"),\n'
        "])",
    ),
    (
        "md",
        """## Settle guard: `agent_before_settle` buys exactly one continuation

If the model answers without running `run_checks`, the guard nudges once with a
`custom_message` entry and `continue: true`. A second answer without checks is
not nudged again.""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["scenario", "requests", "nudge sent?"],\n'
        '    [["model never runs run_checks", know["settleNoChecks"]["callCount"], "yes" if know["settleNoChecks"]["hasNudge"] else "no"],\n'
        '     ["model runs run_checks", know["settleWithChecks"]["callCount"], "yes" if know["settleWithChecks"]["hasNudge"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("never running checks -> exactly 2 requests (one continuation)",\n'
        '               know["settleNoChecks"]["callCount"] == 2 and know["settleNoChecks"]["hasNudge"], "2 requests, nudge sent"),\n'
        '    pinb.check("running checks -> 2 requests, no nudge",\n'
        '               know["settleWithChecks"]["callCount"] == 2 and not know["settleWithChecks"]["hasNudge"], "2 requests, no nudge"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

All seven tests from the chapter's test file.""",
    ),
    *canonical_tests(
        18,
        "ch18-knowledge/knowledge.test.ts",
        what="The chapter's canonical evidence",
        show="active",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** What happens if `agent_before_settle` returns `continue: true`
**unconditionally**? Does it loop forever?

**Then change one input.** The `review-guard-section` uses `delete
event.systemPromptOptions.sections.review_guard` when the tool is not active.
What happens if it leaves the section but sets it to an empty string instead?

**Predict the boundary.** The chapter says `session.systemPrompt` omits the
section on 1.0.4. The driver reads `systemPromptSeenByProvider` — what does
`session.systemPrompt` actually contain at this pin?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. Unconditional continue: true -> infinite loop (the chapter guards against this).")\n'
        'print("  2. Empty string section: probably still sent to provider as empty section.")\n'
        'print("  3. session.systemPrompt omits the section; provider copy is the ground truth.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  active tools: read={know[\"promptCustomizerOnlyRead\"][\"hasRead\"]}, bash={know[\"promptCustomizerOnlyRead\"][\"hasBash\"]}")\n'
        'print(f"  disabled run_checks: section={\"yes\" if know[\"reviewGuardDisabled\"][\"hasSection\"] else \"no\"}")\n'
        'print(f"  accessor: registered={len(know[\"accessor\"][\"registered\"] or [])}, active={len(know[\"accessor\"][\"active\"] or [])}")\n'
        'print(f"  settle no checks: {know[\"settleNoChecks\"][\"callCount\"]} requests, nudge={know[\"settleNoChecks\"][\"hasNudge\"]}")\n'
        "print()\n"
        'assert know["promptCustomizerOnlyRead"]["hasRead"] and not know["promptCustomizerOnlyRead"]["hasBash"]\n'
        'assert not know["reviewGuardDisabled"]["hasSection"]\n'
        'assert know["reviewGuardReenabled"]["hasSection"]\n'
        'assert "run_checks" in (know["accessor"]["registered"] or [])\n'
        'assert "run_checks" not in (know["accessor"]["active"] or [])\n'
        'assert know["settleNoChecks"]["callCount"] == 2\n'
        'print("held: active set controls the prompt, registered set is larger, settle guard nudges once")',
    ),
    (
        "md",
        """## Interpretation

What the model knows comes from three sources, and each has a boundary:

| Source | What it contributes | The boundary |
|---|---|---|
| `tool_guidance` section | One line per active built-in tool | Inactive tools are not described — the model cannot call them |
| Extension sections (`before_agent_start`) | Arbitrary text from extensions | Evaluated per run; stale sections must be deleted |
| `agent_before_settle` | `custom_message` entries + `continue: true` | **One continuation max** — the entry is the loop guard |

The practical rules:
* **Describe what the model can call** — the active set, not the registered set. `getAllTools()` is for tooling; `getActiveTools()` is for the prompt.
* **Delete stale sections** — a section written for a previous turn outlives the condition that produced it. Use `delete`, not empty string.
* **`agent_before_settle` is the last actionable boundary** — it can append entries and buy one more request. `agent_settled` is notification-only.
* **The provider's copy is the ground truth** — `session.systemPrompt` may omit sections; always read what the provider actually received.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=18,
            mode="**Run** — real sessions walking active → disabled → re-enabled, reading the provider's system prompt via `systemPromptSeenByProvider`.",
            scope="`in_process_runtime`. The active-set rule and `agent_before_settle` behaviour are Pi's.",
            provenance=[
                "**Ran** `drivers/ch18-knowledge.ts`: ten real sessions covering prompt-customizer, review-guard-section, accessor probe, and settle-guard.",
                "**Ran** `ch18-knowledge/knowledge.test.ts` (7 tests).",
                "**Read** `examples/evidence.json`, chapter 18 rows (7 claims).",
            ],
            limits=[
                "**`session.systemPrompt` omits the section on 1.0.4** — observed, and the reason the provider's copy is read instead (`ch18-lim1`).",
                "**No token cost measured** for the tool guidance section (`ch18-lim2`).",
                "**The settle-guard only nudges once** — the `custom_message` entry is the loop guard.",
                "**`tools` on the session filters at registration** — the active/disabled case uses `setActiveTools()` which produces a different boundary (registered but not active).",
            ],
        ),
    ),
]