"""Chapter 37 - The Agent Core on Its Own."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "The Agent Core on Its Own"
QUESTION = """Does one prompt produce a four-message transcript and exactly two provider
requests — and is a lookup miss data or a failure?

The chapter's point: `pi-agent-core` is the loop with **no coding agent, no host,
no terminal**. A tool-using prompt produces a four-message transcript
(user → assistant-with-call → toolResult → assistant-answer), exactly one
provider request per turn, and events in order. A lookup that finds nothing is
**data, not a failure**."""

CELLS = [
    ("md", heading(37, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "One tool-using prompt produces a **four-message transcript**: user, assistant (tool call), toolResult, assistant (answer).",
                "Two turns cost **exactly two provider requests** — one per turn.",
                "Events arrive in order: `tool_execution_start` before `tool_execution_end`, and the run ends with `agent_end`.",
                "A tool that finds nothing returns **data, not a failure** — `isError: false` with `no matches`.",
            ],
            [
                "**The absence of `agent_settled` from the core's types is a reading of declarations** (`ch37-lim3`), not a runtime observation here.",
                "**'What the host was providing' is the book's summary** (`ch37-lim2`) — the core runs alone by design.",
                "**The model is scripted** — request counts are exact for the scripted control flow only.",
            ],
        ),
    ),
    *setup_cells(
        37,
        mode="**Run** + Inspect (declarations) — the chapter's research agent against the scripted provider, plus a static count of the core's imports.",
        scope="`in_process_runtime` + `declarations`.",
    ),
    (
        "md",
        """## Baseline: the loop, in four messages and two requests""",
    ),
    (
        "code",
        'CORE = pinb.driver_source("ch37-agent-core.ts")\n'
        'core = pinb.driver(CORE, label="ch37-agent-core", timeout=180)\n'
        'l = core["loop"]\n'
        'print("Role sequence:", " -> ".join(l["roles"]))\n'
        'print(pinb.md_table(\n'
        '    ["check", "value"],\n'
        '    [["request count", l["callCount"]],\n'
        '     ["tool events in order", l["toolOrder"]],\n'
        '     ["last event", l["lastEvent"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("the transcript has the four-message shape",\n'
        '               l["roles"] == ["user", "assistant", "toolResult", "assistant"], " -> ".join(l["roles"])),\n'
        '    pinb.check("two turns cost exactly two requests",\n'
        '               l["callCount"] == 2, f"{l[\'callCount\']} requests"),\n'
        '    pinb.check("tool_execution_start precedes tool_execution_end",\n'
        '               l["toolOrder"], "ordered"),\n'
        '    pinb.check("the run ends with agent_end",\n'
        '               l["lastEvent"] == "agent_end", "agent_end"),\n'
        "])",
    ),
    (
        "md",
        """## A lookup miss is data, not a failure""",
    ),
    (
        "code",
        'm = core["miss"]\n'
        'print(pinb.md_table(\n'
        '    ["check", "value"],\n'
        '    [["isError", m["isError"]],\n'
        '     ["content", m["content"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("a lookup that finds nothing is not a failure",\n'
        '               m["isError"] is False, "isError false"),\n'
        '    pinb.check("it returns the data the tool gives: no matches",\n'
        '               "no matches" in m["content"], "content"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

Both agent-core tests.""",
    ),
    *canonical_tests(
        37,
        "ch37-agent-core/research-agent.test.ts",
        what="The chapter's canonical evidence",
        show="loop",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** The chapter's research agent runs `lookup_evidence` then answers.
What would the role sequence be if the model called the tool **twice** before
answering?

**Then change one input.** The corpus has two entries. Add a third that also
matches the query. Does the tool return more than one entry — and does the
four-message shape change?

**Predict the boundary.** The core's event stream ends with `agent_end`. Where does
`agent_settled` come from — the core, or the host?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. Two tool calls: user, assistant, toolResult, toolResult, assistant - five messages.")\n'
        'print("  2. More matches: the tool returns what it has; the shape is unchanged.")\n'
        'print("  3. agent_settled is a host concept; the core ends with agent_end.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  roles: {\" -> \".join(l[\'roles\'])}")\n'
        'print(f"  requests: {l[\'callCount\']}, tool order ok: {l[\'toolOrder\']}, last: {l[\'lastEvent\']}")\n'
        'print(f"  miss: isError={m[\'isError\']}, content={m[\'content\']}")\n'
        "print()\n"
        'assert l["roles"] == ["user", "assistant", "toolResult", "assistant"]\n'
        'assert l["callCount"] == 2 and l["toolOrder"] and l["lastEvent"] == "agent_end"\n'
        'assert m["isError"] is False and "no matches" in m["content"]\n'
        'print("held: the core loops tool-then-answer; a miss is data; events are ordered")',
    ),
    (
        "md",
        """## Interpretation

The agent core alone is the loop, with the boundaries the chapter shows:

| Claim | Evidence |
|---|---|
| **Four-message transcript** | user → assistant (tool call) → toolResult → assistant |
| **One request per turn** | Two turns, `callCount == 2` |
| **Events in order** | `tool_execution_start` < `tool_execution_end`, ends with `agent_end` |
| **A miss is data** | `isError: false`, content `no matches` |

The practical rules:
1. **The core is host-free** — no terminal, no context loader, no permissions. The host supplies those.
2. **Count requests to find loop bugs** — a turn should cost one request.
3. **A tool result is data** — read `isError` and the content, not the shape.
4. **`agent_end` is the core's terminal event** — `agent_settled` belongs to the host.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=37,
            mode="**Run** + Inspect (declarations) — the chapter's research agent against the scripted provider, plus a static count of the core's imports.",
            scope="`in_process_runtime` + `declarations`.",
            provenance=[
                "**Ran** `drivers/ch37-agent-core.ts`: the chapter's research agent twice (tool-using loop, lookup miss).",
                "**Ran** `ch37-agent-core/research-agent.test.ts` (2 tests).",
                "**Read** `examples/evidence.json`, chapter 37 rows (2 claims).",
            ],
            limits=[
                "**The absence of `agent_settled` from the core's types is a reading of declarations** (`ch37-lim3`).",
                "**The model is scripted** — request counts are exact for the scripted control flow only.",
            ],
        ),
    ),
]