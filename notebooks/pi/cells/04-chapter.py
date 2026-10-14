"""Chapter 04 - The Context Window Is a Budget."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "The Context Window Is a Budget"
QUESTION = """Is compaction an opinion or arithmetic? **Find the exact turn at which
Pi decides to compact** and check it against the one-line rule the chapter states.

The rule is `contextTokens > contextWindow - reserveTokens`. If that is what runs,
the boundary is inspectable — you can call the decision function yourself at every
token count and find where it flips."""

CELLS = [
    ("md", heading(4, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "The trigger is arithmetic and its boundary is exact: Pi compacts when "
                "`contextTokens > contextWindow - reserveTokens`, and not one turn "
                "earlier. The exported `shouldCompact` is the function that decides, and "
                "the cell below walks it across the boundary.",
                "A larger `reserveTokens` compacts earlier on the *same* conversation. It "
                "is not a preference — it moves the turn.",
                "The percentage in the footer is `tokens / contextWindow`, checked against "
                "the real `getContextUsage()` of a real session.",
                "Only **active** tools are declared to the model. Narrowing the set "
                "with `tools:` reduces what the model is told *and* what is registered; "
                "the registered-but-not-active gap comes from `deferred` exposure, "
                "which is chapter 17.",
            ],
            [
                "**Token counts come from the faux provider's scripted usage.** They are "
                "real numbers produced by a real agent, but a real model's usage would "
                "differ and the *turn* at which compaction fires would differ with it.",
                "**Nothing about summary quality.** Compaction here is about the cut point "
                "and the arithmetic; chapter 23 is about what is kept.",
                "**Nothing about provider context-overflow recovery**, which is a repair "
                "path rather than a strategy — chapter 29.",
                "**No guidance for choosing `reserveTokens`.** `metadata/04-chapter.yaml` "
                "records that the chapter gives none, and neither does this notebook.",
            ],
        ),
    ),
    *setup_cells(
        4,
        mode="**Run** — Pi's exported `shouldCompact` across its boundary, a real session's "
        "context accounting, and the chapter's own tests.",
        scope="`in_process_runtime`, plus a `declarations` reading of the exported "
        "signature. The provider is scripted.",
    ),
    (
        "md",
        """## Baseline: the decision function, read from the pin

`shouldCompact` is exported from `@earendil-works/pi-coding-agent` at the pin. Its
declaration is the contract; calling it is how you find the boundary rather than
inferring it from a log.""",
    ),
    (
        "code",
        'DRIVER = r"""\n'
        'import { shouldCompact } from "@earendil-works/pi-coding-agent";\n'
        "\n"
        "const WINDOW = 100_000;\n"
        "const RESERVE = 16_384;\n"
        "const settings = { enabled: true, reserveTokens: RESERVE, keepRecentTokens: 8_000 };\n"
        "const threshold = WINDOW - RESERVE;\n"
        "\n"
        "const around = [threshold - 2, threshold - 1, threshold, threshold + 1, threshold + 2];\n"
        "\n"
        'console.log(JSON.stringify({\n'
        '  window: WINDOW,\n'
        '  reserveTokens: RESERVE,\n'
        '  threshold,\n'
        '  aroundThreshold: around.map((t) => ({ tokens: t, compacts: shouldCompact(t, WINDOW, settings as any) })),\n'
        '  reserveMovesTheLine: [16_384, 32_000, 64_000].map((r) => ({ reserveTokens: r, firstTokenThatCompacts: WINDOW - r + 1 })),\n'
        '  disabled: [threshold, threshold + 10_000].map((t) => ({ tokens: t, compacts: shouldCompact(t, WINDOW, { ...settings, enabled: false } as any) })),\n'
        "}));\n"
        '"""\n'
        'boundary = pinb.driver(DRIVER, label="ch04-should-compact", timeout=120)\n'
        'print(f"contextWindow {boundary[\'window\']:,}   reserveTokens {boundary[\'reserveTokens\']:,}   "\n'
        '      f"threshold {boundary[\'threshold\']:,}")\n'
        "print()\n"
        'print(pinb.table(["contextTokens", "compacts?"], [[f"{row[\'tokens\']:,}", \"yes\" if row[\"compacts\"] else \"no\"] for row in boundary["aroundThreshold"]], indent=""))\n'
        'print()\n'
        'print(pinb.table(["reserveTokens", "first token count that compacts"],\n'
        '                 [[f"{row[\'reserveTokens\']:,}", f"{row[\'firstTokenThatCompacts\']:,}"] for row in boundary["reserveMovesTheLine"]], indent=""))',
    ),
    (
        "md",
        """The flip is exactly where the chapter says it is: `threshold` does not compact,
`threshold + 1` does. There is no tolerance band and no hysteresis at this layer.

The second table is the practical consequence. `reserveTokens` is not slack for
being wrong — it is the distance between *the point of no return* and *the point at
which you compact*, and doubling it doubles how early compaction happens.""",
    ),
    (
        "code",
        "t = boundary[\"threshold\"]\n"
        "\n"
        "pinb.show_checks([\n"
        '    pinb.check("threshold - 1 does not compact", not boundary["aroundThreshold"][1][\"compacts\"], \"no\"),\n'
        '    pinb.check("threshold itself does not compact", not boundary["aroundThreshold"][2][\"compacts\"], "the comparison is strict >"),\n'
        '    pinb.check("threshold + 1 does compact", boundary["aroundThreshold"][3][\"compacts\"], \"yes\"),\n'
        '    pinb.check("threshold == window - reserve", t == boundary["window"] - boundary["reserveTokens\"], str(t)),\n'
        '    pinb.check("enabled: false compacts at no token count",\n'
        '               not any(r["compacts"] for r in boundary["disabled"]), str(boundary[\"disabled\"])),\n'
        '    pinb.check("a larger reserve moves the line earlier",\n'
        '               [r["firstTokenThatCompacts"] for r in boundary["reserveMovesTheLine"]] == sorted(\n'
        '                   [r["firstTokenThatCompacts"] for r in boundary["reserveMovesTheLine"]], reverse=True),\n'
        '               "monotonically earlier"),\n'
        "])",
    ),
    (
        "md",
        """## Experiment: the same conversation, real context accounting

Now the arithmetic against a *real* session. A short conversation is run with a
scripted model, and the session's own `getContextUsage()` is read after each turn.

Two things are being checked: that the percent really is tokens over window, and
that only **active** tools are declared to the model — the other boundary this
chapter draws.""",
    ),
    (
        "code",
        'DRIVER2 = r"""\n'
        'import { fauxAssistantMessage, fauxText } from "@earendil-works/pi-ai";\n'
        'import { makeSession } from "../harness/session.ts";\n'
        'import { pad } from "../harness/history.ts";\n'
        "\n"
        "const say = (t: string) => fauxAssistantMessage([fauxText(t)]);\n"
        "\n"
        "async function conversation(tools?: string[]) {\n"
        "\tconst h = await makeSession({ extensions: [], tools });\n"
        "\tconst turns: any[] = [];\n"
        "\tlet declared: string[] | null = null;\n"
        "\tfor (let i = 0; i < 5; i++) {\n"
        "\t\tconst answer = say(pad(`answer ${i}`, 10 * (i + 1)));\n"
        "\t\tif (declared === null) {\n"
        "\t\t\th.faux.appendResponses([\n"
        "\t\t\t\t(ctx: any) => {\n"
        "\t\t\t\t\tconst sys: any = ctx.messages.find((m: any) => m.role === 'system');\n"
        "\t\t\t\t\tdeclared = (sys?.toolsAdded ?? []).map((t: any) => t.name);\n"
        "\t\t\t\t\treturn answer;\n"
        "\t\t\t\t},\n"
        "\t\t\t]);\n"
        "\t\t}\n"
        "\t\telse {\n"
        "\t\t\th.faux.setResponses([answer]);\n"
        "\t\t}\n"
        "\t\tawait h.session.prompt(`question ${i}`);\n"
        "\t\tconst u = h.session.getContextUsage();\n"
        "\t\tturns.push({ turn: i + 1, tokens: u?.tokens ?? null, contextWindow: u?.contextWindow ?? null, percent: u?.percent ?? null, messages: h.session.messages.length });\n"
        "\t}\n"
        "\tconst active = h.session.getActiveToolNames();\n"
        "\tconst registered = h.session.getAllTools().map((t: any) => t.name);\n"
        "\th.dispose();\n"
        "\treturn { turns, declared, active, registered };\n"
        "}\n"
        "\n"
        "console.log(JSON.stringify({ default: await conversation(), narrowed: await conversation(['read']) }));\n"
        '"""\n'
        'usage = pinb.driver(DRIVER2, label="ch04-context-usage", timeout=240)\n'
        'print("A default session, five turns (each answer padded, so the conversation really grows):")\n'
        'print(pinb.table(["turn", "messages", "context tokens", "contextWindow", "percent"],\n'
        '                 [[t["turn"], t["messages"], f"{t[\'tokens\']:,}" if t["tokens"] else "-", f"{t[\'contextWindow\']:,}",\n'
        '                   f"{t[\'percent\']:.2f}" if t["percent"] is not None else "-"]\n'
        '                  for t in usage["default"]["turns"]], indent=""))\n'
        'print()\n'
        "print(pinb.md_table(\n"
        '    ["session", "tools declared to the model", "active", "registered"],\n'
        '    [["default", ", ".join(usage["default"]["declared"]), ", ".join(usage["default"]["active"]), len(usage["default"]["registered"])],\n'
        '     ["tools: [read]", ", ".join(usage["narrowed"]["declared"]), ", ".join(usage["narrowed"]["active"]), len(usage["narrowed"]["registered"])]],\n'
        "))",
    ),
    (
        "code",
        'd = usage["default"]\n'
        'n = usage["narrowed"]\n'
        "pcts_ok = all(\n"
        "    t[\"percent\"] is not None and abs(t[\"percent\"] - (t[\"tokens\"] / t[\"contextWindow\"]) * 100) < 0.01\n"
        "    for t in d[\"turns\"] if t[\"tokens\"]\n"
        ")\n"
        'grew = [t["tokens"] for t in d["turns"] if t["tokens"]]\n'
        "from_turn_2 = grew[1:]\n"
        "\n"
        "pinb.show_checks([\n"
        '    pinb.check("the window is the faux model\'s declared 100,000",\n'
        '               all(t["contextWindow"] == 100_000 for t in d["turns"]), "100000"),\n'
        '    pinb.check("percent is exactly tokens / window", pcts_ok, "within 0.01 of the ratio"),\n'
        '    pinb.check("context grows strictly from turn 2 on",\n'
        '               from_turn_2 == sorted(from_turn_2) and len(set(from_turn_2)) == len(from_turn_2),\n'
        '               f"{from_turn_2[0]:,} -> {from_turn_2[-1]:,} over {len(from_turn_2)} turns"),\n'        '    pinb.check("a default session declares bash to the model", "bash" in d["declared"], ", ".join(d["declared"])),\n'
        '    pinb.check("tools: [read] declares exactly one tool", n["declared"] == ["read"], ", ".join(n["declared"])),\n'
        '    pinb.check("the tools option narrows registration as well as declaration",\n'
        '               len(n["registered"]) == len(n["active"]) == 1,\n'
        '               f"registered {len(n[\'registered\'])}, active {len(n[\'active\'])}"),\n'
        "])",
    ),
    (
        "md",
        """## Contrasting case: `enabled: false` is not "never"

The boundary function refuses at every token count when `enabled: false`. But the
chapter's test asserts something sharper: the **manual** `/compact` still works
with automatic compaction off. Automatic triggering and the ability to compact are
two different switches, and only one of them is a setting.""",
    ),
    *canonical_tests(
        4,
        "ch04-budget/budget.test.ts",
        what="The chapter's canonical evidence",
        show="compaction",
    ),
    (
        "md",
        """The second table is the other half of the chapter's tool boundary, and it is
worth reading carefully: passing `tools: ["read"]` reduced **both** the tools the
model is told about *and* the registered set. The registered-but-not-active gap
this book keeps returning to is not created by narrowing at startup; it is created
by `deferred` exposure (chapter 17), or by an extension that registers a tool and
then sets the active set itself.

## Your turn: predict, then run

**Predict first.** Set `reserveTokens` above the window. At what token count does
the line move, and does `shouldCompact` ever return true below the window?

**Then change one input.** `RESERVE` below feeds the same boundary walk. Try
`100_000` (equal to the window) and `120_000` (larger than it).

**Predict the practical effect.** With `reserveTokens: 100_000` on a 100,000-token
window, when would compaction fire in a real conversation?""",
    ),
    (
        "code",
        'RESERVE = 100_000\n'
        "\n"
        "EXERCISE = DRIVER.replace(\"const RESERVE = 16_384;\", \"const RESERVE = Number(process.env.NB_RESERVE);\")\n"
        "edge = pinb.driver(EXERCISE, label=\"ch04-edge-reserve\", timeout=120, env={\"NB_RESERVE\": str(RESERVE)})\n"
        'print(f"reserveTokens = {RESERVE:,}  on a {edge[\'window\']:,}-token window")\n'
        'print(f"threshold = {edge[\'threshold\']:,}")\n'
        'print()\n'
        'print(pinb.table(["contextTokens", "compacts?"],\n'
        '                 [[f"{row[\'tokens\']:,}", "yes" if row["compacts"] else "no"] for row in edge["aroundThreshold"]], indent=""))\n'
        "\n"
        'print()\n'
        'if edge["threshold"] <= 0:\n'
        '    print("A non-positive threshold means the window is already over budget at zero tokens:")\n'
        '    print("every non-negative token count compacts, so a conversation can never start.")\n'
        "else:\n"
        '    print(f"The line sits {edge[\'threshold\']:,} tokens below the window, so compaction is {edge[\'window\'] - edge[\'threshold\']:,} tokens away.")',
    ),
    (
        "md",
        """## Interpretation: a budget with one moving part

The context window is not a limit you hit; it is a threshold you choose, and three
numbers decide it:

```
compact when:   contextTokens  >  contextWindow  -  reserveTokens
                      what Pi sends     the model's ceiling      your choice
```

The two consequences worth carrying forward:

1. **Compaction is early by design.** `reserveTokens` exists so there is room to
   summarise *and* to answer. It is not a safety margin against the provider
   rejecting the request — that is what `keepRecentTokens` and the overflow repair
   path are for (chapter 29).
2. **Compaction does not shrink the system prompt or the tool declarations.** The
   chat turns get smaller; the instructions do not. A long tool-heavy session can
   therefore approach the threshold faster than a long chat session, which the
   chapter states and this notebook does not measure.

### What this chapter does not settle

`metadata/04-chapter.yaml` records two limits that survive here: there is no
guidance for choosing `reserveTokens` or `keepRecentTokens` when the window is
unknown or a provider misreports it, and token estimation *before* the cut point
is chosen is undocumented. Both are honest gaps in the documentation, not things
this notebook can fill.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=4,
            mode="**Run** — the exported `shouldCompact` across its boundary, a real session's "
            "`getContextUsage()`, and the chapter's own test file.",
            scope="`in_process_runtime` for the sessions; the boundary walk is a direct call "
            "into the pinned package's own decision function.",
            provenance=[
                "**Ran** `shouldCompact` from `@earendil-works/pi-coding-agent` at the pin, "
                "across `threshold - 2 .. threshold + 2`, with `enabled` both true and false.",
                "**Ran** two real `AgentSession`s (default tools, and `tools: [read]`), "
                "reading `getContextUsage()` after each of five turns and capturing the "
                "system message the provider received.",
                "**Ran** `ch04-budget/budget.test.ts` (8 tests), which is where the "
                "multi-turn growth runs, the per-model override and the manual `/compact` case.",
                "**Read** `examples/evidence.json`, chapter 4 rows (8 claims).",
            ],
            limits=[
                "**Token numbers are the faux provider's.** They are produced by a real "
                "agent through a real budget, but the growth rate is a property of the "
                "scripted answers, not of a real model. The *turn* at which compaction "
                "fires would differ with a real conversation.",
                "**The percentage identity is a definition, not a discovery.** "
                "`percent == tokens / window` is what the footer computes; asserting it "
                "shows the footer is not lying, not that the token estimate is accurate.",
                "**No summary quality is assessed.** The boundary is the subject; what "
                "compaction keeps is chapter 23.",
            ],
        ),
    ),
]
