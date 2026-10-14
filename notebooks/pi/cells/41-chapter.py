"""Chapter 41 - Testing Stochastic Software."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Testing Stochastic Software"
QUESTION = """How far apart are pass@1 and pass^5, and what does the gap hide?

The chapter's point: an agent is stochastic. **pass@1** (the average over single
runs) hides run-to-run reliability. **pass^k** — succeeded on all k independent
runs — exposes the gap. On a simulated 85% step across 40 tasks and 5 runs, the
book reproduces `pass@1 = 0.86` and `pass^5 = 0.45`."""

CELLS = [
    ("md", heading(41, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "**Level 1 (scripted)**: a scripted response drives the code deterministically — it tests the code around the model.",
                "**Level 2 (structural)**: assert on the event stream, not on the wording — `tool:submit:ok`, one `turn_start`, one request.",
                "**Level 3 (evaluation)**: `pass@1 = 0.86` and `pass^5 = 0.45` are reproduced from a seeded 85% step over 40 tasks × 5 runs.",
                "A **thrown step counts as a failed run** and does not crash the evaluation.",
            ],
            [
                "**The 'forty tasks' are one task repeated forty times** — the figure is about the arithmetic, not a real workload.",
                "**The figures describe a simulation, not any real model** (`ch41-lim2`).",
                "**`pass^k` provenance is cited, not verified** in this notebook.",
                "**Level 3 with a real model is optional live work** — it needs a credential and costs money.",
            ],
        ),
    ),
    *setup_cells(
        41,
        mode="**Run** + Reproduce — the chapter's own `evaluate()` over the seeded simulation; the real-model level 3 is absent.",
        scope="`in_process_runtime`. The evaluation arithmetic is the chapter's.",
    ),
    (
        "md",
        """## Baseline: levels 1 and 2, then the question level 3 answers""",
    ),
    (
        "code",
        'TESTING = pinb.driver_source("ch41-testing.ts")\n'
        'tst = pinb.driver(TESTING, label="ch41-testing", timeout=420)\n'
        'pk = tst["passK"]\n'
        'print(pinb.md_table(\n'
        '    ["metric", "value"],\n'
        '    [["pass@1 (average over single runs)", pk["passAt1"]],\n'
        '     ["pass^5 (succeeded on all 5 runs)", pk["passPowK"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("pass@1 reproduces 0.86 on the seeded 85% simulation",\n'
        '               pk["passAt1"] == 0.86, f"{pk[\'passAt1\']}"),\n'
        '    pinb.check("pass^5 reproduces 0.45",\n'
        '               pk["passPowK"] == 0.45, f"{pk[\'passPowK\']}"),\n'
        '    pinb.check("the gap is large: pass^5 is 0.4 below pass@1",\n'
        '               pk["passPowK"] < pk["passAt1"] - 0.35, "the average hides reliability"),\n'
        "])",
    ),
    (
        "code",
        'gap = pk["passAt1"] - pk["passPowK"]\n'
        'print(f"The gap: pass@1 - pass^5 = {gap:.2f}")\n'
        'print()\n'
        'print("What the gap hides: a run that is right 85% of the time on average")\n'
        'print("succeeds on all 5 independent runs less than half the time.")',
    ),
    (
        "md",
        """## A thrown step is a failed run, not a crash""",
    ),
    (
        "code",
        'ts = tst["thrownStep"]\n'
        'print(pinb.md_table(\n'
        '    ["check", "value"],\n'
        '    [["runs completed after the throw", ts["calls"]],\n'
        '     ["pass@1 over the two tasks", round(ts["passAt1"], 3)],\n'
        '     ["pass^5", ts["passPowK"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("the evaluation kept going after the throw",\n'
        '               ts["calls"] == 5, f"{ts[\'calls\']} calls"),\n'
        '    pinb.check("a thrown run counts as a failure",\n'
        '               ts["passPowK"] == 0, "pass^5 = 0"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

All four testing tests.""",
    ),
    *canonical_tests(
        41,
        "ch41-testing/testing.test.ts",
        what="The chapter's canonical evidence",
        show="level",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** The simulation is seeded with 42. What happens to pass@1 and
pass^5 if you change the seed to 0 — do the pinned figures move?

**Then change one input.** Make the simulated model 95% reliable instead of 85%.
Which metric moves faster, pass@1 or pass^5?

**Predict the boundary.** Level 3 with a *real* model is the only level that
says anything about the model. What would it cost, and what must be frozen before
a run?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. A different seed moves both figures - the pinned values are for seed 42.")\n'
        'print("  2. pass^5 moves faster: it is a power, so a small change in p compounds.")\n'
        'print("  3. Real-model level 3 needs a credential and a frozen contract (planning/real-model-plan.md).")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  pass@1={pk[\'passAt1\']}, pass^5={pk[\'passPowK\']}")\n'
        'print(f"  thrown step: calls={ts[\'calls\']}, pass^5={ts[\'passPowK\']}")\n'
        "print()\n"
        'assert pk["passAt1"] == 0.86 and pk["passPowK"] == 0.45\n'
        'assert ts["calls"] == 5 and ts["passPowK"] == 0\n'
        'print("held: pass@1 = 0.86, pass^5 = 0.45; a thrown step is a failed run, not a crash")',
    ),
    (
        "md",
        """## Interpretation

Three levels of testing, and what each establishes:

| Level | What it does | What it cannot show |
|---|---|---|
| **1. Scripted** | Drives the code deterministically | Anything about a real model |
| **2. Structural** | Asserts on the event stream | Wording; model quality |
| **3. Evaluation** | Measures pass rates over repeated runs | Anything real, until the model is real |

The arithmetic: `pass@1 = 0.86` and `pass^5 = 0.45` on a simulated 85% step.
`pass@1` is the average; `pass^k` requires success on all k runs. The gap is
reliability, and it is the number a production decision should look at.

Practical rules:
1. **Use level 1 to test your code** — determinism around a model is scriptable.
2. **Use level 2 to pin structure** — events and request counts, not words.
3. **Use level 3 to make claims about reliability** — and read `pass^k`, not the average.
4. **A thrown run is a failure** — count it, do not crash the sheet.
5. **Real-model evaluation is separate** — a contract and a credential, never a cell.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=41,
            mode="**Run** + Reproduce — the chapter's own `evaluate()` over the seeded simulation; the real-model level 3 is absent.",
            scope="`in_process_runtime`. The evaluation arithmetic is the chapter's.",
            provenance=[
                "**Ran** `drivers/ch41-testing.ts`: the seeded 40×5 evaluation, reproducing pass@1 = 0.86, pass^5 = 0.45, and the thrown-step case.",
                "**Ran** `ch41-testing/testing.test.ts` (4 tests).",
                "**Read** `examples/evidence.json`, chapter 41 rows (4 claims).",
            ],
            limits=[
                "**The 'forty tasks' are one task repeated forty times** — the figure is about the arithmetic.",
                "**The figures describe a simulation, not any real model** (`ch41-lim2`).",
                "**`pass^k` provenance is cited, not verified**.",
            ],
            unrun=[
                "Real-model level 3 evaluation — needs a credential, a frozen contract, and costs money.",
            ],
        ),
    ),
]