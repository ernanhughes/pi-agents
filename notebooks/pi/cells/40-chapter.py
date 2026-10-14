"""Chapter 40 - Composing Agent Operations."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Composing Agent Operations"
QUESTION = """What is the exact request cost of each route, and does a check placed *after*
the model stop an invented citation before the next call is paid for?

The chapter's point: an agent pipeline is a **composition of typed operations**.
The escalation-only-if-needed route costs exactly one assessment and one summary
on the cheap path, and the agent's escalation is bounded. A citation check placed
after the assessment stops an invented citation **before the summary call**."""

CELLS = [
    ("md", heading(40, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "The **deterministic parts need no model at all** — retrieval and the citation check run without a provider.",
                "The **cheap path** is one assessment call and one summary step — **no agent**, exactly 2 requests.",
                "An **invented citation stops the pipeline** before anything downstream runs — the summary step is not paid for.",
                "A **truthful citation on the escalation path** passes the second check.",
                "**Escalation only pays for the agent when the verdict is insufficient**.",
                "The escalation agent is **bounded**, so a model that keeps searching cannot run away.",
                "An escalation **cut off before it found anything fails loudly** instead of re-deciding on no new evidence.",
            ],
            [
                "**Request counts are exact for the scripted control flow only** (`ch40-lim2`) — a real model may take a different path.",
                "**No real model is called** — this measures the pipeline's control flow, not model ability.",
                "**The citation check is a string match against evidence**, not a semantic one.",
            ],
        ),
    ),
    *setup_cells(
        40,
        mode="**Run** — the chapter's `checkClaim` composition against the scripted provider.",
        scope="`in_process_runtime`. The pipeline's control flow and bounds are the chapter's.",
    ),
    (
        "md",
        """## Baseline: the deterministic parts need no model""",
    ),
    (
        "code",
        'PIPE = pinb.driver_source("ch40-composition.ts")\n'
        'pipe = pinb.driver(PIPE, label="ch40-composition", timeout=180)\n'
        'd = pipe["deterministic"]\n'
        'print(pinb.md_table(\n'
        '    ["check", "value"],\n'
        '    [["retrieve found the evidence", d["retrieved"]],\n'
        '     ["an invented citation fails the check", d["citationOk"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("retrieval returns the matching evidence",\n'
        '               d["retrieved"] == ["The release shipped on 4 October."], "retrieved"),\n'
        '    pinb.check("an invented citation is not real",\n'
        '               d["citationOk"] is False, "not real"),\n'
        "])",
    ),
    (
        "md",
        """## The cheap path: no agent, two requests""",
    ),
    (
        "code",
        'c = pipe["cheapPath"]\n'
        'print(pinb.md_table(\n'
        '    ["check", "value"],\n'
        '    [["route", c["route"]],\n'
        '     ["request count", c["callCount"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("the cheap path is a single assessment and a summary",\n'
        '               c["route"] == "single call" and c["callCount"] == 2, "2 requests, no agent"),\n'
        "])",
    ),
    (
        "md",
        """## A check after the model stops an invented citation""",
    ),
    (
        "code",
        'i, et, ec = pipe["inventedCitation"], pipe["escalationTruthful"], pipe["escalationCost"]\n'
        'print(pinb.md_table(\n'
        '    ["case", "result", "requests"],\n'
        '    [["invented citation", "rejected" if i["rejected"] else "accepted", i["callCount"]],\n'
        '     ["escalation, truthful citation", f"route={et[\'route\']}", et["callCount"]],\n'
        '     ["escalation, supported verdict", f"route={ec[\'route\']}, verdict={ec[\'verdict\']}", ec["callCount"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("an invented citation stops before the summary is paid for",\n'
        '               i["rejected"] and i["callCount"] == 1, "1 request, stopped"),\n'
        '    pinb.check("a truthful citation on the escalation path passes",\n'
        '               et["route"] == "agent escalation", "escalated and passed"),\n'
        '    pinb.check("escalation only pays for the agent when the verdict is insufficient",\n'
        '               ec["route"] == "agent escalation" and ec["verdict"] == "supported", "agent used once"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

All eight pipeline tests.""",
    ),
    *canonical_tests(
        40,
        "ch40-composition/pipeline.test.ts",
        what="The chapter's canonical evidence",
        show="escalation",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** The cheap path costs 2 requests. What does the escalation path
cost when the verdict is `insufficient` and the agent finds evidence on its
first turn?

**Then change one input.** The citation check matches evidence **by content
overlap**. What happens with a citation that is a paraphrase of the evidence —
passes or fails?

**Predict the boundary.** The escalation agent is bounded by `ESCALATION_TURNS`.
What happens if the model keeps searching to the bound and never finds
evidence?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. Escalation cost: 1 assess + 1 agent turn + 1 assess + 1 summary = 4.")\n'
        'print("  2. A paraphrase: fails the string-based check (semantic checking is not here).")\n'
        'print("  3. Bound reached with no evidence: the pipeline fails loudly.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  deterministic: retrieved={d[\'retrieved\']}, citationOk={d[\'citationOk\']}")\n'
        'print(f"  cheap path: route={c[\'route\']}, requests={c[\'callCount\']}")\n'
        'print(f"  invented citation: rejected={i[\'rejected\']}, requests={i[\'callCount\']}")\n'
        'print(f"  escalation truthful: route={et[\'route\']}, requests={et[\'callCount\']}")\n'
        "print()\n"
        'assert c["route"] == "single call" and c["callCount"] == 2\n'
        'assert i["rejected"] and i["callCount"] == 1\n'
        'assert et["route"] == "agent escalation"\n'
        'print("held: cheap path costs 2; an invented citation stops before the summary; escalation is bounded")',
    ),
    (
        "md",
        """## Interpretation

Composition is a set of decisions with known costs, and the chapter shows each:

| Route | Request cost | What stops it |
|---|---|---|
| **Cheap path** | 1 assessment + 1 summary = 2 | A `supported` verdict with real citations |
| **Invented citation** | 1 assessment | The check **after** the model, before the summary |
| **Agent escalation** | 1 + agent turns + 1 + 1 | A verifiable verdict; bounded by `ESCALATION_TURNS` |
| **Cut off** | 1 + agent turns | Fails loudly, never re-decides on no evidence |

The practical rules:
1. **Put the cheap check before the expensive call** — the citation check stops the summary request.
2. **Escalate only when needed** — an `insufficient` verdict is the only thing that pays for the agent.
3. **Bound the escalation** — a model that keeps searching cannot run away.
4. **Fail loudly on no evidence** — do not re-decide on nothing.
5. **Count requests** — the pipeline's cost is exact for the scripted control flow; a real model may diverge.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=40,
            mode="**Run** — the chapter's `checkClaim` composition against the scripted provider.",
            scope="`in_process_runtime`. The pipeline's control flow and bounds are the chapter's.",
            provenance=[
                "**Ran** `drivers/ch40-composition.ts`: deterministic parts, cheap path, invented citation, escalation truthful, escalation cost.",
                "**Ran** `ch40-composition/pipeline.test.ts` (8 tests).",
                "**Read** `examples/evidence.json`, chapter 40 rows (8 claims).",
            ],
            limits=[
                "**Request counts are exact for the scripted control flow only** (`ch40-lim2`) — a real model may take a different path.",
                "**No real model is called** — this measures the pipeline's control flow, not model ability.",
            ],
        ),
    ),
]