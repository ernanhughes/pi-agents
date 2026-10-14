"""Chapter 38 - A Stochastic Step Is a Typed Function."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "A Stochastic Step Is a Typed Function"
QUESTION = """Does `maxTurns` still bound a run **after** a valid submission was stored in a
mixed batch?

The chapter's point: a stochastic step is a **typed function** — input, schema,
bounds, and a typed value out. `maxAttempts` bounds repairs, `maxTurns` bounds
the run. The mixed-batch rule is the sharp edge: a submission in a batch with a
non-terminating tool cannot outlive `maxTurns`."""

CELLS = [
    ("md", heading(38, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "A **valid submission** ends the run after one request and returns a typed value.",
                "An **invalid submission is returned to the model**, which repairs it, costing one request per attempt.",
                "**Repeated invalid submissions stop at `maxAttempts`**; a model that never submits is stopped by `maxTurns`.",
                "**Prose with no submit** is a `StepFailed` (kind `no-submit`), not a silent empty value.",
                "A **failed request** is a provider failure (kind `provider`), not the model choosing prose.",
                "In a **mixed batch**, a submission with a non-terminating tool cannot outlive `maxTurns` — the bound fires after a submission, not just before one.",
                "The **first valid submission wins** when the model submits more than once.",
                "An invalid submission in a mixed batch **costs one attempt, not one per tool**.",
            ],
            [
                "**`maxAttempts` and `maxTurns` are proposed bounds, not Pi's contract** (`ch38-lim2`).",
                "**Every case is a case someone anticipated** — a scripted test cannot show an autonomous surprise.",
                "**The model is scripted** — request counts are exact for the scripted control flow only.",
            ],
        ),
    ),
    *setup_cells(
        38,
        mode="**Run** — the chapter's `step()` against the scripted provider, all the boundary cases.",
        scope="`in_process_runtime`. Schema validation, repair, and the batch rule are the chapter's step.",
    ),
    (
        "md",
        """## Baseline: valid, repair, and the bound""",
    ),
    (
        "code",
        'STEP = pinb.driver_source("ch38-typed-step.ts")\n'
        'st = pinb.driver(STEP, label="ch38-typed-step", timeout=180)\n'
        'v, r, a, n = st["valid"], st["repair"], st["attemptExhaustion"], st["neverSubmits"]\n'
        'print("valid submission:   severity=" + str(v["out"]["severity"]) + f", requests={v["callCount"]}")\n'
        'print("invalid then repair: severity=" + str(r["severity"]) + f", requests={r["callCount"]}")\n'
        'print("attempt exhaustion:  kind=" + str(a["kind"]) + f", requests={a["callCount"]}")\n'
        'print("never submits:       kind=" + str(n["kind"]) + f", requests={n["callCount"]}")\n'
        "print()\n"
        "pinb.show_checks([\n"
        '    pinb.check("a valid submission ends the run after one request",\n'
        '               v["out"]["severity"] == "high" and v["callCount"] == 1, "1 request"),\n'
        '    pinb.check("an invalid submission is returned to the model, which repairs it",\n'
        '               r["severity"] == "high" and r["callCount"] == 2, "2 requests"),\n'
        '    pinb.check("repeated invalid submissions stop at maxAttempts",\n'
        '               a["kind"] == "invalid-submissions" and a["callCount"] == 2, "2 requests then StepFailed"),\n'
        '    pinb.check("a model that never submits is stopped by maxTurns",\n'
        '               n["kind"] == "turn-limit" and n["callCount"] == 4, "4 requests then StepFailed"),\n'
        "])",
    ),
    (
        "md",
        """## The mixed-batch rule: the bound holds after a submission""",
    ),
    (
        "code",
        'mb, fv, ib = st["mixedBatchBound"], st["firstValidWins"], st["invalidInMixedBatch"]\n'
        'print("submission + non-terminating tool: severity=" + str(mb["out"]["severity"]) + f", requests={mb["callCount"]}")\n'
        'print("first valid wins:                  severity=" + str(fv["out"]["severity"]))\n'
        'print("invalid in mixed batch:            severity=" + str(ib["severity"]) + f", requests={ib["callCount"]}")\n'
        "print()\n"
        "pinb.show_checks([\n"
        '    pinb.check("a submission in a mixed batch cannot outlive maxTurns",\n'
        '               mb["out"]["severity"] == "high" and mb["callCount"] == 2, "2 requests, bounded"),\n'
        '    pinb.check("the first valid submission wins",\n'
        '               fv["out"]["severity"] == "low", "first wins"),\n'
        '    pinb.check("an invalid submission in a mixed batch costs one attempt, not one per tool",\n'
        '               ib["severity"] == "high" and ib["callCount"] == 3, "3 requests, repaired"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

All fourteen step tests.""",
    ),
    *canonical_tests(
        38,
        "ch38-typed-step/step.test.ts",
        what="The chapter's canonical evidence",
        show="mixed",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** `maxTurns: 2` with a mixed batch stored a valid submission in
turn 1. What stops the loop in turn 2 — the valid value or the bound?

**Then change one input.** `maxAttempts: 3` with two invalid mixed batches that
each contain one invalid submission. How many requests before repair?

**Predict the boundary.** A submission in a batch with a tool that *does*
terminate. When does the turn end — immediately, or after the batch?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. maxTurns=2 with a stored submission: the second turn must still find a terminating run.")\n'
        'print("  2. Two invalid mixed batches: two attempts, then the third repairs - 3 requests.")\n'
        'print("  3. A batch where every tool terminates: the turn ends when the batch agrees.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'vs = str(v["out"]["severity"])\n'
        'rs = str(r["severity"])\n'
        'mbs = str(mb["out"]["severity"])\n'
        'ibs = str(ib["severity"])\n'
        'print(f"  valid: severity={vs}, requests={v["callCount"]}")\n'
        'print(f"  repair: severity={rs}, requests={r["callCount"]}")\n'
        'print(f"  mixed batch bound: severity={mbs}, requests={mb["callCount"]}")\n'
        'print(f"  invalid in mixed: severity={ibs}, requests={ib["callCount"]}")\n'
        "print()\n"
        'assert v["callCount"] == 1 and r["callCount"] == 2\n'
        'assert a["kind"] == "invalid-submissions" and n["kind"] == "turn-limit"\n'
        'assert mb["callCount"] == 2 and fv["out"]["severity"] == "low"\n'
        'assert ib["callCount"] == 3\n'
        'print("held: maxAttempts bounds repairs, maxTurns bounds the run, mixed batches cost one attempt")',
    ),
    (
        "md",
        """## Interpretation

A step is a typed function with three parts, and the chapter shows the bounds:

| Part | What it decides | The boundary |
|---|---|---|
| **Schema** | What counts as a valid submission | Invalid → returned to the model |
| **`maxAttempts`** | How many repairs | Exhausted → `StepFailed` kind `invalid-submissions` |
| **`maxTurns`** | How long the run can go | Exhausted → `StepFailed` kind `turn-limit` |

The mixed-batch rule: a turn ends early only when every completed result in the
batch agrees to terminate. `submit` agrees, `lookup_evidence` does not, so one
response can store a valid answer and still leave the loop running — the bound has
to keep firing after a submission, or the bound is not a bound.

Practical rules:
1. **Validate the submission** — the schema is the contract, and repairs cost requests.
2. **Bound both dimensions** — attempts limit repairs, turns limit the run.
3. **Count requests** — a valid step costs one; a repair costs two; a bounded run stops on the bound.
4. **Remember the batch rule** — a stored submission does not end the run unless the batch agrees.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=38,
            mode="**Run** — the chapter's `step()` against the scripted provider, all the boundary cases.",
            scope="`in_process_runtime`. Schema validation, repair, and the batch rule are the chapter's step.",
            provenance=[
                "**Ran** `drivers/ch38-typed-step.ts`: seven step scenarios (valid, repair, attempt exhaustion, never submits, mixed batch bound, first valid wins, invalid in mixed batch).",
                "**Ran** `ch38-typed-step/step.test.ts` (14 tests).",
                "**Read** `examples/evidence.json`, chapter 38 rows (14 claims).",
            ],
            limits=[
                "**`maxAttempts` and `maxTurns` are proposed bounds, not Pi's contract** (`ch38-lim2`).",
                "**Every case is a case someone anticipated** — a scripted test cannot show an autonomous surprise.",
            ],
        ),
    ),
]