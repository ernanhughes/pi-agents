"""Chapter 39 - Seams, Hooks, and Irreversible Decisions."""

import json

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Seams, Hooks, and Irreversible Decisions"
QUESTION = """In what order do the hooks fire — and does a block mean the body never ran,
while a rewrite cannot undo the effect?

The chapter's point: the hooks sit at named points in the run, in a **fixed
order**. `beforeToolCall` can **refuse before** the effect; `afterToolCall` can
**rewrite the result but cannot undo the effect**; `transformContext` changes
what the provider receives, not what the agent stored; `finishTurn` can end the
run early."""

CELLS = [
    ("md", heading(39, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "The hooks fire in a **fixed order** in one tool-using run: prepareRequest → transformContext → convertToLlm → tool.execute starts → beforeToolCall → afterToolCall → finishTurn → turn_end.",
                "`beforeToolCall` can **refuse**, and then the effect never happens — `counter.runs` stays 0.",
                "`afterToolCall` can **rewrite the result but cannot undo the effect** — the write already happened.",
                "`transformContext` changes what the provider receives, **not what the agent stored**.",
                "`finishTurn` can **end the run early** (saving the follow-up request), the tool in the finished turn still ran.",
                "`prepareRequest` can **swap the model** for one request.",
                "`runToolCall` passes **nested calls through `beforeToolCall`**, and a blocked one never executes.",
            ],
            [
                "**Most seam-matrix cells are readings of declared result types, not runs** (`ch39-lim2`).",
                "**'Refuse' is relative to a named decision** — a hook can refuse the thing it is placed before, and nothing else.",
                "**The published 1.0.2 recording is inspected as historical**, not re-grounded.",
                "**The model is scripted** — request counts are exact for the scripted control flow only.",
            ],
        ),
    ),
    *setup_cells(
        39,
        mode="**Run** + **Inspect** — the chapter's seam cases against a real `Agent`, a fresh trace from the chapter's exporter, and (when present) the published 1.0.2 recording.",
        scope="`in_process_runtime`. The hooks are Pi's.",
    ),
    (
        "md",
        """## Baseline: the hook order in a tool-using run""",
    ),
    (
        "code",
        'SEAMS = pinb.driver_source("ch39-seams.ts")\n'
        'seams = pinb.driver(SEAMS, label="ch39-seams", timeout=180)\n'
        'print("Hook order:")\n'
        'for i, name in enumerate(seams["order"]["orderNames"], 1):\n'
        '    print(f"  {i}. {name}")\n'
        'print()\n'
        'expected = ["prepareRequest", "transformContext", "convertToLlm", "tool.execute starts", "beforeToolCall", "afterToolCall", "finishTurn", "turn_end"]\n'
        'first_turn = seams["order"]["orderNames"][:8]\n'
        'pinb.show_checks([\n'
        '    pinb.check("the first turn follows the documented hook order",\n'
        '               first_turn == expected, " -> ".join(first_turn)),\n'
        '    pinb.check("two turns cost two requests",\n'
        '               seams["order"]["calls"] == 2, f"{seams[\'order\'][\'calls\']} requests"),\n'
        "])",
    ),
    (
        "md",
        """## Block before, rewrite after""",
    ),
    (
        "code",
        'bl, rw = seams["block"], seams["rewrite"]\n'
        'print(pinb.md_table(\n'
        '    ["case", "effect ran?", "tool result"],\n'
        '    [["beforeToolCall blocks .env", f"{bl[\'runs\']} runs", f"isError={bl[\'isError\']}, {bl[\'text\']}"],\n'
        '     ["afterToolCall rewrites", f"{rw[\'runs\']} runs", f"isError={rw[\'isError\']}, {rw[\'text\']}"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("a block means the effect never happened",\n'
        '               bl["runs"] == 0 and bl["isError"] and "protected path" in bl["text"], "blocked, 0 runs"),\n'
        '    pinb.check("a rewrite cannot undo the effect",\n'
        '               rw["runs"] == 1, "1 run, already done"),\n'
        '    pinb.check("the rewrite changed the result the model sees",\n'
        '               rw["text"] == "[redacted]" and rw["isError"], "redacted"),\n'
        "])",
    ),
    (
        "md",
        """## transformContext and finishTurn""",
    ),
    (
        "code",
        'tc, fe = seams["transformContext"], seams["finishTurnEarly"]\n'
        'print(pinb.md_table(\n'
        '    ["check", "value"],\n'
        '    [["sent user messages after transformContext", tc["sentUsers"]],\n'
        '     ["stored user messages", tc["storedUsers"]],\n'
        '     ["finishTurn end: requests", fe["callCount"]],\n'
        '     ["finishTurn end: tool runs in the finished turn", fe["runs"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("transformContext changed what was sent, not what was stored",\n'
        '               tc["sentUsers"] == 1 and tc["storedUsers"] == 2, "sent 1, stored 2"),\n'
        '    pinb.check("finishTurn ended the run early (one request)",\n'
        '               fe["callCount"] == 1, "1 request"),\n'
        '    pinb.check("the tool in the finished turn still ran: finishTurn is after the effect",\n'
        '               fe["runs"] == 1, "1 run"),\n'
        "])",
    ),
    (
        "md",
        """## The published recording (historical, Pi 1.0.2)

The browser experience at `/tools/ai/pi/39-chapter/` replays a recording captured
on **Pi 1.0.2**. It is historical and stays labelled so.""",
    ),
    (
        "code",
        'import json\n'
        'exp = pinb.experience_dir(39)\n'
        'if exp is None:\n'
        '    pinb.unrun("the published 1.0.2 recording", "not present in this checkout; set PIN_EXPERIENCES to the site repo\'s content/tools/ai/pi")\n'
        'else:\n'
        '    meta = json.loads((exp / "experiment.json").read_text(encoding="utf-8"))\n'
        '    print("Published experience:", meta["id"])\n'
        '    print("Pinned version:", meta["pinnedVersion"])\n'
        '    print("RECORDED inspection of 1.0.2 evidence, not a fresh run.")',
    ),
    (
        "md",
        """## The chapter's own tests

All eight seam tests.""",
    ),
    *canonical_tests(
        39,
        "ch39-seams/seams.test.ts",
        what="The chapter's canonical evidence",
        show="beforeToolCall",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** A block in `beforeToolCall` stops the effect. What does the
model see — a failed result, or nothing?

**Then change one input.** `afterToolCall` in the demonstration rewrites to
`isError: true`. Rewrite it to `isError: false` with the original text. Does the
effect count change?

**Predict the boundary.** The seam matrix distinguishes observe / transform /
refuse / effect-done. Which cell does `transformContext` occupy — and which does
`afterToolCall`?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. A block in beforeToolCall: the model sees a failed toolResult with the reason.")\n'
        'print("  2. Rewriting to isError false: the effect count does not change - it already ran.")\n'
        'print("  3. transformContext transforms; afterToolCall is effect-done + transform.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  order first turn: {\" -> \".join(seams[\'order\'][\'orderNames\'][:8])}")\n'
        'print(f"  block: runs={bl[\'runs\']}, isError={bl[\'isError\']}")\n'
        'print(f"  rewrite: runs={rw[\'runs\']}, result={rw[\'text\']}")\n'
        'print(f"  transformContext: sent={tc[\'sentUsers\']}, stored={tc[\'storedUsers\']}")\n'
        "print()\n"
        'assert bl["runs"] == 0 and rw["runs"] == 1\n'
        'assert tc["sentUsers"] == 1 and tc["storedUsers"] == 2\n'
        'assert fe["callCount"] == 1 and fe["runs"] == 1\n'
        'print("held: hooks fire in order; a block precedes the effect; a rewrite cannot undo it")',
    ),
    (
        "md",
        """## Interpretation

The seam matrix, with the cells this chapter's probes run:

| Hook | Observe | Transform | Refuse | Effect done? |
|---|---|---|---|---|
| `beforeToolCall` | yes | args | **block** | **no** — the effect never runs |
| `afterToolCall` | result | result | no | **yes** — cannot undo |
| `transformContext` | messages | messages | no | n/a (before the request) |
| `finishTurn` | turn | action | `end` | yes — after the effect |

Practical rules:
1. **Place the refusal before the effect.** `beforeToolCall` is the only gate that stops it.
2. **Do not let `afterToolCall` pretend to undo.** The write already happened; a rewrite changes only what the model sees.
3. **`transformContext` is a view, not storage.** What the agent stored differs from what the provider received.
4. **`finishTurn` after the effect** — the tool ran; only the follow-up request is saved.
5. **The recording is historical.** The 1.0.2 experience is inspected, not re-grounded.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=39,
            mode="**Run** + **Inspect** — the chapter's seam cases against a real `Agent`, a fresh trace from the chapter's exporter, and (when present) the published 1.0.2 recording.",
            scope="`in_process_runtime`. The hooks are Pi's.",
            provenance=[
                "**Ran** `drivers/ch39-seams.ts`: the chapter's order, block, rewrite, transformContext and finishTurn cases against a real `Agent`.",
                "**Ran** `ch39-seams/seams.test.ts` (8 tests).",
                "**Inspected** the published 1.0.2 recording at `/tools/ai/pi/39-chapter/` when `PIN_EXPERIENCES` resolves it (recorded, not fresh).",
                "**Read** `examples/evidence.json`, chapter 39 rows (8 claims).",
            ],
            limits=[
                "**Most seam-matrix cells are readings of declared result types, not runs** (`ch39-lim2`).",
                "**The published 1.0.2 recording is inspected as historical**, not re-grounded.",
            ],
            unrun=[
                "The published browser experience is inspected only when its directory is present.",
            ],
        ),
    ),
]