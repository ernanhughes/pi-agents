"""Chapter 42 - Authority, Isolation, and What Makes an Agent Worth Building."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Authority, Isolation, and What Makes an Agent Worth Building"
QUESTION = """Can a value chosen by the inspected party gate the inspection?

The chapter's point: `AgentTool.replay` is a field a tool fills in **about
itself**. A tool can declare `replay: "safe"`, and **nothing in the declaration
verifies it**. The static scan shows that no shipped JavaScript in the Pi packages
reads the field — the declaration and the scan are the evidence, and the 
anti-vacuity self-test guarantees the scan would notice a reader."""

CELLS = [
    ("md", heading(42, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "A tool can declare `replay` **about itself**, and nothing in the declaration verifies the claim.",
                "The **static scan for a reader of `AgentTool.replay`** would notice one — the anti-vacuity self-test makes an empty result meaningful.",
                "At **1.0.4, no shipped JavaScript** in the Pi packages reads a tool's `replay` field.",
                "The chapter's own gate evidence is reused: block-before-effect, the no-UI guard, the lying `readOnlyHint`.",
            ],
            [
                "**Containers, micro-VMs and credential proxies are documented, not run** — this book executed none.",
                "**A schematic sandbox is not containment evidence** — a diagram of a sandbox is not a proof it confines.",
                "**No `real_model` evidence exists** in this book (see `examples/evidence.json`).",
                "**The four-rung ladder and the permission model are the book's proposals**.",
            ],
        ),
    ),
    *setup_cells(
        42,
        mode="**Run** + Inspect — the chapter's static scan and its anti-vacuity self-test, plus the reused gate evidence from chapters 16, 17 and 21.",
        scope="`in_process_runtime` + `shipped_binary`. No container or VM is run.",
    ),
    (
        "md",
        """## Baseline: the value chosen by the inspected party""",
    ),
    (
        "code",
        'AUTH = pinb.driver_source("ch42-authority.ts")\n'
        'auth = pinb.driver(AUTH, label="ch42-authority", timeout=120)\n'
        'print(pinb.md_table(\n'
        '    ["check", "value"],\n'
        '    [["a tool can declare replay about itself", auth["toolCanDeclare"]],\n'
        '     ["scan would notice a direct comparison", auth["antiVacuity"]["seesDirectComparison"]],\n'
        '     ["scan would notice an object literal", auth["antiVacuity"]["seesObjectLiteral"]],\n'
        '     ["JavaScript files scanned", auth["scanned"]],\n'
        '     ["readers found", len(auth["readers"])]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("the declaration is self-authored and unverified",\n'
        '               auth["toolCanDeclare"], "replay: safe declared"),\n'
        '    pinb.check("the scan is not vacuous: it would notice a reader",\n'
        '               auth["antiVacuity"]["seesDirectComparison"] and auth["antiVacuity"]["seesObjectLiteral"],\n'
        '               "anti-vacuity holds"),\n'
        '    pinb.check("no shipped JavaScript reads a tool replay field at 1.0.4",\n'
        '               auth["noReaders"] and len(auth["readers"]) == 0, f"{auth[\'scanned\']} files, 0 readers"),\n'
        "])",
    ),
    (
        "md",
        """## The gate evidence, reused

The book's authority mechanism is not one scan — it is the gates, exercised in
chapters 16, 17 and 21. Those are **observed** evidence, and this notebook points
at them rather than re-running what they already show:

| Evidence | Chapter | What it shows |
|---|---|---|
| Block-before-effect | 16 | A `tool_call` guard leaves the filesystem untouched |
| No-UI refusal | 16 | Print mode refuses rather than allowing silently |
| Lying `readOnlyHint` | 17, 21 | An annotation passes the gate — hints are unverified |
| `replay: "safe"` | 42 | A self-declared recovery policy with no reader |""",
    ),
    (
        "md",
        """## The chapter's own tests

All three authority tests.""",
    ),
    *canonical_tests(
        42,
        "ch42-authority/replay.test.ts",
        what="The chapter's canonical evidence",
        show="replay",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** A future Pi release *does* start reading `replay`. What breaks
in this notebook first — and what must chapter 42 then do?

**Then change one input.** Add a line to the scan's pattern that reads
`tool.replay` in a loop. Does the anti-vacuity self-test now fail the 
no-readers assertion?

**Predict the boundary.** The chapter's containers and micro-VMs are documented,
not run. What would a containment *claim* require that this notebook does not
have?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. A reader in a future release fails the no-readers assertion, and chapter 42 must be re-read.")\n'
        'print("  2. A real reader in the scanned code would surface in the readers list.")\n'
        'print("  3. A containment claim needs an executed sandbox, not a diagram - unrun here.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  tool can declare: {auth[\'toolCanDeclare\']}")\n'
        'print(f"  anti-vacuity: direct={auth[\'antiVacuity\'][\'seesDirectComparison\']}, literal={auth[\'antiVacuity\'][\'seesObjectLiteral\']}")\n'
        'print(f"  scanned files: {auth[\'scanned\']}, readers: {len(auth[\'readers\'])}")\n'
        "print()\n"
        'assert auth["toolCanDeclare"]\n'
        'assert auth["antiVacuity"]["seesDirectComparison"] and auth["antiVacuity"]["seesObjectLiteral"]\n'
        'assert auth["noReaders"]\n'
        'print("held: a self-authored replay claim is unverified; the scan is non-vacuous; 1.0.4 has no reader")',
    ),
    (
        "md",
        """## Interpretation

Authority in this book comes from **who inspects whom**, and the chapter shows
the sharpest case: `AgentTool.replay` is **self-reported**. The evidence is:
the field can be set, the scan is non-vacuous, and no shipped code reads it at
1.0.4.

What this notebook does **not** establish:
* Containers, micro-VMs and credential proxies — **documented, not run**.
* A schematic sandbox — **not containment evidence**.
* Any `real_model` result — the book has none.

The practical rules:
1. **Self-reported fields are claims, not facts** — `replay: "safe"` is the tool's word.
2. **A non-vacuous scan is the tool of real evidence** — the anti-vacuity self-test makes "no reader" meaningful.
3. **Gates are exercised, not imagined** — the block-before-effect and no-UI refusal are observed evidence.
4. **Containment requires execution** — a diagram is not a sandbox, and unrun recipes stay unrun.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=42,
            mode="**Run** + Inspect — the chapter's static scan and its anti-vacuity self-test, plus the reused gate evidence from chapters 16, 17 and 21.",
            scope="`in_process_runtime` + `shipped_binary`. No container or VM is run.",
            provenance=[
                "**Ran** `drivers/ch42-authority.ts`: the static scan of the Pi packages' `dist` for a reader of `AgentTool.replay`, with its anti-vacuity self-test.",
                "**Ran** `ch42-authority/replay.test.ts` (3 tests).",
                "**Reused** the observed gate evidence from chapters 16, 17 and 21 (quoted, not re-run).",
                "**Read** `examples/evidence.json`, chapter 42 rows (3 claims).",
            ],
            limits=[
                "**Containers, micro-VMs and credential proxies are documented, not run** — this book executed none.",
                "**A schematic sandbox is not containment evidence**.",
                "**No `real_model` evidence exists** — the one retained attempt was refused before the model saw a prompt.",
                "**The four-rung ladder and the permission model are the book's proposals**.",
            ],
            unrun=[
                "Container and VM recipes (documented, not run).",
                "Credential proxies (documented, not run).",
                "Any real-model call (none exists in this book).",
            ],
        ),
    ),
]