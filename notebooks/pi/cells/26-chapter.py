"""Chapter 26 - Message Types."""

from _common import establishes, heading, setup_cells, sources_and_limits

TITLE = "Message Types"
QUESTION = """Do the types printed in the chapter match the exported declarations — and does
`SystemMessage.replace` exist at this pin?

The chapter's point: the message types are a **contract**, and the contract is the
exported declaration, not the prose. When `message-types.md` describes a
`SystemMessage.replace` that the 1.0.4 declaration does not have, the declaration
wins and the discrepancy is recorded."""

CELLS = [
    ("md", heading(26, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "The chapter's hand-written declarations are **assignable to and from** the exported types, in both directions, checked at compile time.",
                "The **key sets** match too — assignability alone tolerates a missing optional field, so the key sets are compared separately.",
                "At 1.0.4, the exported `SystemMessage` has **no `replace` member**, and no shipped JavaScript reads one.",
                "The four roles the chapter declares (`system`, `user`, `assistant`, `toolResult`) are the four in the exported union.",
            ],
            [
                "**Not a runtime claim.** This notebook checks **declarations and static text**; it runs no session and asserts no behaviour.",
                "**The prose/declaration mismatch on `replace`** is a recorded discrepancy, not a bug report.",
                "**No provider mapping is described** — the chapter does not claim how a message becomes a provider payload.",
                "**The declaration wins** where the two disagree; this notebook's job is to show where they do.",
            ],
        ),
    ),
    *setup_cells(
        26,
        mode="**Inspect** — compile-time check (`tsc` over `assert-equal.ts`) plus a static read of the 1.0.4 declaration and the shipped JavaScript.",
        scope="`declarations`. Nothing here runs a model or a session.",
    ),
    (
        "md",
        """## Baseline: the declaration at the pin

The exported `SystemMessage`, read directly from
`examples/node_modules/@earendil-works/pi-ai/dist/types.d.ts`. This is the
authority the chapter is checked against.""",
    ),
    (
        "code",
        'TYPES = pinb.driver_source("ch26-message-types.ts")\n'
        'types = pinb.driver(TYPES, label="ch26-message-types", timeout=120)\n'
        'print("SystemMessage at 1.0.4:")\n'
        'print("  " + types["systemMessageDeclaration"][:400])\n'
        "print()\n"
        'print("Four roles in the chapter\'s declaration:", ", ".join(types["declaredRoles"]))',
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("the four base roles are declared",\n'
        '               types["declaredRoles"] == ["system", "user", "assistant", "toolResult"],\n'
        '               ", ".join(types["declaredRoles"])),\n'
        '    pinb.check("the declaration still has content, sections, toolsAdded, toolsRemoved at this pin",\n'
        '               all(k in types["systemMessageDeclaration"] for k in ["content", "sections", "toolsAdded", "toolsRemoved"]),\n'
        '               "all four fields present"),\n'
        "])",
    ),
    (
        "md",
        """## The compile-time check

`ch26-message-types/assert-equal.ts` compares the chapter's declarations with the
exported types, in both directions, and separately compares the key sets. If a
field drifts on either side, `tsc` fails. Running the project typecheck is
running the chapter's declaration claim.""",
    ),
    (
        "code",
        'import subprocess\n'
        'r = pinb.run_node(["node_modules/typescript/bin/tsc", "-p", "."], cwd=pinb.EXAMPLES, timeout=180)\n'
        'print("$ tsc -p examples/")\n'
        'print(f"  exit={r.status}")\n'
        'if r.stdout.strip():\n'
        '    print(r.stdout.strip()[:500])\n'
        'if r.stderr.strip():\n'
        '    print(r.stderr.strip()[:500])\n'
        "pinb.show_checks([\n"
        '    pinb.check("the chapter declarations compile against the exported types",\n'
        '               r.status == 0, "tsc exit 0"),\n'
        "])",
    ),
    (
        "md",
        """## Contrasting case: the recorded discrepancy

`message-types.md` describes `SystemMessage.replace`. The 1.0.4 declaration does
not have one, and no shipped JavaScript reads one. The declaration wins: a
notebook or a chapter that used `replace` would fail to compile.

This is the book's drift protocol in miniature — a documented member that the
declaration never had. It is **recorded**, not smoothed over.""",
    ),
    (
        "code",
        'print("Does the 1.0.4 SystemMessage declaration have a `replace` member?")\n'
        'print("  " + ("yes" if types["declarationHasReplace"] else "no"))\n'
        'print()\n'
        'print(f"Shipped JavaScript files scanned: {types[\'jsFilesScanned\']}")\n'
        'print("Files that read a SystemMessage.replace:", types["jsReadsReplace"] or "(none)")\n'
        'print()\n'
        'pinb.show_checks([\n'
        '    pinb.check("the 1.0.4 declaration has NO `replace` member",\n'
        '               not types["declarationHasReplace"], "absent from the declaration"),\n'
        '    pinb.check("no shipped JavaScript reads a SystemMessage.replace",\n'
        '               len(types["jsReadsReplace"]) == 0, "no reader found"),\n'
        "])",
    ),
    (
        "md",
        """## Your turn: inspect, then decide

**Predict first.** The chapter's `assert-equal.ts` compares both assignability and
key sets. Which would catch an **optional** field the declaration gained but the
chapter did not? (Assignability would not; the key-set comparison would.)

**Then check one thing.** Open
`examples/node_modules/@earendil-works/pi-ai/dist/types.d.ts` and find
`AssistantMessage`. Does it declare `stopReason`? What are the allowed values?

**Predict the boundary.** If a future Pi release *adds* `SystemMessage.replace`,
what breaks first — this notebook's static check, the chapter's `assert-equal.ts`,
or the prose that documents it?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. Key-set comparison catches an added optional field; assignability does not.")\n'
        'print("  2. AssistantMessage declares stopReason with the union of stop reasons.")\n'
        'print("  3. A new member breaks the static check first (this notebook), then tsc, then the prose.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  declaration has replace: {types[\'declarationHasReplace\']}")\n'
        'print(f"  shipped JS readers: {len(types[\'jsReadsReplace\'])}")\n'
        'print(f"  roles declared: {types[\'declaredRoles\']}")\n'
        'assert not types["declarationHasReplace"]\n'
        'assert len(types["jsReadsReplace"]) == 0\n'
        'print()\n'
        'print("held: the 1.0.4 declaration has no SystemMessage.replace; the prose describes one; the declaration wins")',
    ),
    (
        "md",
        """## Interpretation

The message types are checked two ways, and each catches something the other
misses:

| Check | What it catches | What it misses |
|---|---|---|
| Assignability (`Same<A, B>`) | A type that is structurally incompatible | An **optional** field missing on one side |
| Key sets (`SameKeys<A, B>`) | Any field the two disagree about | Nothing at the type level |
| Static read of `.d.ts` | A member the prose describes but the declaration lacks | Whether the shipped code reads it |
| Static read of `.js` | Whether the shipped code actually uses a member | Behaviour |

The practical rules:
1. **The declaration wins.** When prose and `.d.ts` disagree, the book follows the declaration.
2. **Check both directions, and the key sets.** Assignability alone tolerates a missing optional field.
3. **A discrepancy is recorded, not smoothed over.** `SystemMessage.replace` is the book's worked example.
4. **Compile-time is evidence for a type claim.** `tsc` passing on `assert-equal.ts` is the chapter's declaration evidence.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=26,
            mode="**Inspect** — compile-time check (`tsc` over `assert-equal.ts`) plus a static read of the 1.0.4 declaration and the shipped JavaScript.",
            scope="`declarations`. Nothing here runs a model or a session.",
            provenance=[
                "**Ran** `tsc -p examples/` — the chapter's `assert-equal.ts` compiled against the pinned declarations.",
                "**Read** `@earendil-works/pi-ai/dist/types.d.ts` for the exported `SystemMessage`.",
                "**Read** `ch26-message-types/declared.ts` and `assert-equal.ts`.",
                "**Read** `examples/evidence.json`, chapter 26 row (1 claim, `declarations`).",
            ],
            limits=[
                "**Not a runtime claim.** This notebook checks declarations and static text only.",
                "**The prose/declaration mismatch on `replace`** is a recorded discrepancy, not a bug report.",
                "**No provider mapping is described** — the chapter does not claim how a message becomes a provider payload.",
            ],
        ),
    ),
]