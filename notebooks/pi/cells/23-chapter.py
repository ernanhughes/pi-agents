"""Chapter 23 - Compaction."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Compaction"
QUESTION = """After a manual compaction, which history did the next request contain, and what
is still in the file?

The chapter's point: compaction **appends a summary entry** and **rebuilds the
context** for the next request from that summary plus the kept messages. The
session file is **never deleted** — navigating back to before the compaction
sends the original messages again."""

CELLS = [
    ("md", heading(23, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "Compaction finds a **cut point** by walking backwards until `keepRecentTokens` is reached, then summarizes the replaced messages and appends a `compaction` entry with `firstKeptEntryId`.",
                "The **next request** is built from the summary plus messages from `firstKeptEntryId` onwards — the oldest messages are replaced by the summary.",
                "The session file **never loses entries** — navigating to before the compaction sends the original messages again.",
                "The **cut point is never a tool result** — tool calls and their results stay together (overshooting the budget if needed).",
                "Compaction is **iterative**: the second compaction receives the first's summary as `previousSummary`.",
                "An extension can **supply the summary** via `session_before_compact` (cut point stays Pi's, `fromHook: true`), or **cancel** a manual `/compact`.",
                "A **split user-message span** produces `isSplitTurn: true`, `messagesToSummarize` empty, and `turnPrefixMessages` for the early part — the shipped `custom-compaction.ts` joins both lists.",
            ],
            [
                "**No summary quality is evaluated** (`ch23-lim2`) — the extension's custom summary is a placeholder, and the test only checks that it arrived.",
                "**The split-turn counts in the prose** come from a `console.log`, not an assertion.",
                "**File operations tracking** (`readFiles`, `modifiedFiles`) is cumulative only for Pi-generated summaries; extension summaries with `fromHook: true` must manage their own `details`.",
                "**The `keepRecentTokens` value** in the driver is controlled by `NB_KEEP` (default 900) to make the test exercise compaction quickly.",
            ],
        ),
    ),
    *setup_cells(
        23,
        mode="**Run** — a real persisted session with the chapter's custom-summary extension, `keepRecentTokens` lowered so a short scripted conversation has something to summarise.",
        scope="`in_process_runtime`. The compaction arithmetic, cut point rules, and extension hook are Pi's.",
    ),
    (
        "md",
        """## Baseline: before compaction""",
    ),
    (
        "code",
        'COMP = pinb.driver_source("ch23-replace.ts")\n'
        'comp = pinb.driver(COMP, label="ch23-replace", timeout=300, env={"NB_KEEP": "900"})\n'
        'print(pinb.md_table(\n'
        '    ["metric", "before", "after"],\n'
        '    [["entries", comp["before"]["entries"], comp["after"]["entries"]],\n'
        '     ["lines in file", comp["before"]["lines"], comp["after"]["lines"]],\n'
        '     ["messages", comp["before"]["messages"], comp["after"]["messages"]],\n'
        '     ["compactions", comp["before"]["compactions"], comp["after"]["compactions"]],\n'
        '     ["question A in file", "yes" if comp["before"]["questionAInFile"] else "no", "yes" if comp["after"]["questionAInFile"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("compaction adds one entry", comp["after"]["entries"] == comp["before"]["entries"] + 1, "entry count +1"),\n'
        '    pinb.check("file grows by one line", comp["after"]["lines"] == comp["before"]["lines"] + 1, "file line +1"),\n'
        '    pinb.check("question A still in file after compaction", comp["after"]["questionAInFile"], "not deleted"),\n'
        "])",
    ),
    (
        "md",
        """## The compaction entry""",
    ),
    (
        "code",
        'c = comp["compaction"]\n'
        'print(pinb.md_table(\n'
        '    ["field", "value"],\n'
        '    [["fromHook", "yes" if c["fromHook"] else "no"],\n'
        '     ["summary is extension\'s", "yes" if c["summaryIsTheExtensions"] else "no"],\n'
        '     ["has firstKeptEntryId", "yes" if c["hasFirstKeptEntryId"] else "no"],\n'
        '     ["firstKept role", c["firstKeptRole"] or "null"],\n'
        '     ["firstKept is toolResult", "yes" if c["firstKeptIsToolResult"] else "no"],\n'
        '     ["tokensBefore positive", "yes" if c["tokensBeforeIsPositive"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("extension supplied the summary", c["fromHook"], "fromHook: true"),\n'
        '    pinb.check("summary text is from the extension", c["summaryIsTheExtensions"], "custom summary used"),\n'
        '    pinb.check("firstKeptEntryId is set", c["hasFirstKeptEntryId"], "cut point recorded"),\n'
        '    pinb.check("firstKept is a user message (legal cut point)", not c["firstKeptIsToolResult"], "not a tool result"),\n'
        '    pinb.check("tokensBefore was recalculated", c["tokensBeforeIsPositive"], "tokensBefore > 0"),\n'
        "])",
    ),
    (
        "md",
        """## What the next request contained""",
    ),
    (
        "code",
        's = comp["sent"]\n'
        'print(pinb.md_table(\n'
        '    ["metric", "value"],\n'
        '    [["roles in request", " -> ".join(s["roles"])],\n'
        '     ["user texts (truncated)", ", ".join(s["userTexts"])],\n'
        '     ["question A sent", "yes" if s["questionASent"] else "no"],\n'
        '     ["question C sent", "yes" if s["questionCSent"] else "no"],\n'
        '     ["summary arrived as user message", "yes" if s["summaryArrivedAsUserMessage"] else "no"],\n'
        '     ["tool calls in request", s["toolCalls"]],\n'
        '     ["tool results in request", s["toolResults"]],\n'
        '     ["system still declares bash", "yes" if s["systemStillDeclaresBash"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("oldest question (A) is NOT sent — replaced by summary", not s["questionASent"], "A replaced"),\n'
        '    pinb.check("newest question (C) IS sent — in kept range", s["questionCSent"], "C kept"),\n'
        '    pinb.check("summary arrives as user-role message", s["summaryArrivedAsUserMessage"], "user message"),\n'
        '    pinb.check("tool calls = tool results (no half calls)", s["toolCalls"] == s["toolResults"], "balanced"),\n'
        '    pinb.check("system prompt still declares bash (not shrunk)", s["systemStillDeclaresBash"], "bash declared"),\n'
        "])",
    ),
    (
        "md",
        """## Navigating back to before compaction""",
    ),
    (
        "code",
        'nb = comp["navigatedBack"]\n'
        'print(pinb.md_table(\n'
        '    ["what was sent", "value"],\n'
        '    [["question A sent again", "yes" if nb["questionASentAgain"] else "no"],\n'
        '     ["summary sent", "yes" if nb["summarySent"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("navigating back sends original question A", nb["questionASentAgain"], "original restored"),\n'
        '    pinb.check("navigating back does NOT send the summary", not nb["summarySent"], "summary not sent"),\n'
        '    pinb.check("file still has question A entry", comp["fileStillHasQuestionA"], "file unchanged"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

All tests from both test files.""",
    ),
    *canonical_tests(
        23,
        ["ch23-compaction/compaction.test.ts", "ch23-compaction/state.test.ts"],
        what="The chapter's canonical evidence",
        show="compaction",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** What happens if you set `NB_KEEP=20000` (the default) instead of
900? Does compaction still fire for the same three-turn history?

**Then change one input.** The extension's custom summary includes only the first
500 characters of the serialized conversation. What happens if you increase that
limit or use the full serialization?

**Predict the boundary.** The split-turn case: one user message followed by six
tool-calling turns. The driver doesn't exercise this — what would the extension
need to do differently to handle `turnPrefixMessages`?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. NB_KEEP=20000: no compaction — the short history fits in the budget.")\n'
        'print("  2. Larger summary limit: more detail in summary, but output token cap still binds.")\n'
        'print("  3. Split turn: extension must join turnPrefixMessages + messagesToSummarize, not just the latter.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  keepRecentTokens: {comp[\"keepRecentTokens\"]}")\n'
        'print(f"  compaction entry: fromHook={comp[\"compaction\"][\"fromHook\"]}, firstKept={comp[\"compaction\"][\"firstKeptRole\"]}")\n'
        'print(f"  next request: A sent={comp[\"sent\"][\"questionASent\"]}, C sent={comp[\"sent\"][\"questionCSent\"]}")\n'
        'print(f"  navigate back: A again={comp[\"navigatedBack\"][\"questionASentAgain\"]}, summary={comp[\"navigatedBack\"][\"summarySent\"]}")\n'
        "print()\n"
        'assert comp["compaction"]["fromHook"]\n'
        'assert not comp["sent"]["questionASent"]\n'
        'assert comp["sent"]["questionCSent"]\n'
        'assert comp["navigatedBack"]["questionASentAgain"]\n'
        'assert not comp["navigatedBack"]["summarySent"]\n'
        'print("held: compaction replaces old messages with summary; file is unchanged; navigate back restores originals")',
    ),
    (
        "md",
        """## Interpretation

Compaction is three things, and the chapter shows the boundaries:

| Mechanism | What it does | The boundary |
|---|---|---|
| Cut point search | Walk back until `keepRecentTokens` | **Never cuts at tool results** — overshoots budget to keep call+result together |
| Summary generation | LLM call with structured format | **Iterative** — `previousSummary` passed to next compaction |
| Context rebuild | Summary + kept messages | **Original entries stay in file** — navigate back restores them |

The extension hook (`session_before_compact`):
* **Supply summary**: return `{ compaction: { summary, firstKeptEntryId, tokensBefore } }` — Pi keeps the cut point, marks `fromHook: true`
* **Cancel**: return `{ cancel: true }` — only for `reason === "manual"`

The split-turn case:
* One long user-message span exceeding `keepRecentTokens` → `isSplitTurn: true`
* `messagesToSummarize` empty, early part in `turnPrefixMessages`
* Pi generates two summaries and merges them
* **Extension must handle both lists** — the shipped `custom-compaction.ts` joins them

Practical rules:
1. **Compaction does not delete** — navigate back and the originals are there.
2. **Put durable facts in context files (ch 28)** — history is summarised, context files travel with every request.
3. **If you supply a summary, include file lists** — `details.readFiles`/`modifiedFiles` are not auto-recovered from `fromHook: true` summaries.
4. **`keepRecentTokens` controls granularity** — lower = more frequent, smaller summaries; higher = fewer, larger summaries.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=23,
            mode="**Run** — a real persisted session with the chapter's custom-summary extension, `keepRecentTokens` lowered so a short scripted conversation has something to summarise.",
            scope="`in_process_runtime`. The compaction arithmetic, cut point rules, and extension hook are Pi's.",
            provenance=[
                "**Ran** `drivers/ch23-replace.ts`: real session with custom summary, compaction, navigation back.",
                "**Ran** `ch23-compaction/compaction.test.ts` and `ch23-compaction/state.test.ts` (tests across multiple `keepRecentTokens` values).",
                "**Read** `examples/evidence.json`, chapter 23 rows (12 claims).",
            ],
            limits=[
                "**No summary quality is evaluated** (`ch23-lim2`) — the extension's custom summary is a placeholder.",
                "**The split-turn counts in the prose** come from a `console.log`, not an assertion.",
                "**File operations tracking** is cumulative only for Pi-generated summaries; extension summaries with `fromHook: true` must manage their own `details`.",
            ],
        ),
    ),
]