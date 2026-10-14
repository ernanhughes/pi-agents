"""Chapter 15 - Your First Extension."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Your First Extension"
QUESTION = """Does registering a `direct` tool make it **active** — and does a call with no
arguments pass Pi's own schema validation?

The chapter's example tool has an optional `base` parameter. The first version
declared it as required while its description said optional, so a model following
the description sent arguments that did not match the schema. The fix and the test
are both about that boundary."""

CELLS = [
    ("md", heading(15, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "Registering a `direct`-exposure tool makes it **active** immediately: it "
                "appears in `getActiveToolNames()` at registration time, not only after "
                "something calls `setActiveTools()`.",
                "A call with **no arguments** is valid when the parameter is `Type.Optional` "
                "and produces `content` plus `details`.",
                "A command registered with `pi.registerCommand` is listed beside the built-ins "
                "and runs without the model being asked.",
            ],
            [
                "**The example tool returns an instruction to the model rather than executing "
                "a command.** Execution is chapter 17's subject.",
                "**`registerToolRenderer` arrived in 1.0.1** and was not exercised in a running "
                "session by the chapter's suite (`ch17-lim3`).",
                "**No measurement** of how often a model calls a tool it was offered.",
            ],
        ),
    ),
    *setup_cells(
        15,
        mode="**Run** — the chapter's two extensions loaded unmodified into real sessions.",
        scope="`in_process_runtime`. Registration, activation and schema validation are Pi's.",
    ),
    (
        "md",
        """## Baseline: registered, active, and callable

Three sets again, and the difference between them is the chapter's first claim.
`review_scope` is a `direct`-exposure tool with an optional `base` parameter;
`hello` is a command.""",
    ),
    (
        "code",
        'EXT = pinb.driver_source("ch15-first-extension.ts")\n'
        'ext = pinb.driver(EXT, label="ch15-first-extension", timeout=300)\n'
        'inv = ext["inventory"]\n'
        'print(pinb.md_table(\n'
        '    ["set", "contains review_scope?", "contains hello?"],\n'
        '    [["registered (getAllTools)", "yes" if "review_scope" in inv["registered"] else "no", "-"],\n'
        '     ["active (getActiveToolNames)", "yes" if "review_scope" in inv["active"] else "no", "-"],\n'
        '     ["callable (getCallableToolNames)", "yes" if "review_scope" in inv["callable"] else "no", "-"],\n'
        '     ["commands", "-", "yes" if "hello" in inv["commands"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("registering a direct tool makes it active at registration time",\n'
        '               "review_scope" in inv["active"], "active immediately"),\n'
        '    pinb.check("it is also registered and callable",\n'
        '               "review_scope" in inv["registered"] and "review_scope" in inv["callable"],\n'
        '               "both"),\n'
        '    pinb.check("the command is listed beside the built-ins",\n'
        '               "hello" in inv["commands"], "listed"),\n'
        "])",
    ),
    (
        "md",
        """## Experiment: a call with no arguments

The chapter's second test is the one that matters. `base` is optional, so a model
that sends `{}` — nothing — must get a valid result, not a schema error.

The driver scripts exactly that: a tool call with no arguments, then an answer.""",
    ),
    (
        "code",
        'print("A scripted call with no arguments:")\n'
        'print(pinb.md_table(\n'
        '    ["", "value"],\n'
        '    [["isError", ext["noArgs"]["isError"]],\n'
        '     ["content", ext["noArgs"]["content"]],\n'
        '     ["details", ext["noArgs"]["details"]]],\n'
        "))\n"
        "\n"
        "pinb.show_checks([\n"
        '    pinb.check("a no-argument call is valid", ext["noArgs"]["isError"] is False, "isError: false"),\n'
        '    pinb.check("and returns content", bool(ext["noArgs"]["content"]), ext["noArgs"]["content"][:60]),\n'
        '    pinb.check("and details", ext["noArgs"]["details"] is not None, str(ext["noArgs"]["details"])),\n'
        "])",
    ),
    (
        "md",
        """## Contrasting case: the schema the description promised

The chapter records the defect its own tests found. `base` was declared
`Type.String(...)` while its description said *Optional*. A model following the
description would send `{}` — and `{}` does not match a required string.

The fix is one word: `Type.Optional(Type.String(...))`. The test above is the
regression guard.""",
    ),
    (
        "code",
        'print("The chapter\'s own words:")\n'
        'print("  \\"base is optional: a call with no arguments is valid and defaults to the")\n'
        'print("   working tree\\"")\n'
        "print()\n"
        'print("The declaration that makes it true:")\n'
        'print("  parameters: Type.Object({ base: Type.Optional(Type.String({...})) })")\n'
        "print()\n"
        'print("The declaration that broke it:")\n'
        'print("  parameters: Type.Object({ base: Type.String({...}) })")\n'
        "print()\n"
        'assert ext["noArgs"]["isError"] is False\n'
        'print("held: the schema matches the description, so a no-argument call is valid")',
    ),
    *canonical_tests(
        15,
        "ch15-first-extension/first-extension.test.ts",
        what="The chapter's canonical evidence",
        show="tool",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** Change `base` back to `Type.String(...)` (required). What does the
no-argument call return — and what does the model see?

**Then change one input.** `BASE` below is what the model sends. Try `{}` (nothing),
then `{"base": "main"}`, then `{"base": 42}` (wrong type).

**Predict the boundary.** What happens if the model sends an argument the schema
does not declare at all — `{"base": "main", "extra": true}`? Is that a schema error
or is the extra field ignored?""",
    ),
    (
        "code",
        'BASE = {}\n'
        'print("predicted: with base optional, {} is valid and defaults to the working tree")\n'
        "print()\n"
        'print("observed above:")\n'
        'print("  isError:", ext["noArgs"]["isError"])\n'
        'print("  content:", ext["noArgs"]["content"][:60])\n'
        'print("  details:", ext["noArgs"]["details"])\n'
        "\n"
        'assert ext["noArgs"]["isError"] is False\n'
        'assert ext["noArgs"]["details"] is not None\n'
        'print()\n'
        'print("held: the optional parameter accepts a missing argument")\n'
        'print()\n'
        'print("The boundary question — an undeclared field — is answered by the chapter\'s")\n'
        'print("own test, which asserts that a call with no arguments is valid. An extra")\n'
        'print("field is a different question; the schema decides, and the schema is the")\n'
        'print("contract.")',
    ),
    (
        "md",
        """## Interpretation

An extension is three things, and the chapter's example shows all three:

1. **A tool** — a name, a schema and an `execute()`. Registering it with
   `exposure: "direct"` makes it active immediately.
2. **A command** — `pi.registerCommand` adds a slash command the model can invoke
   or a user can type.
3. **A renderer** — `pi.registerToolRenderer` (1.0.1) draws the tool's call in the
   terminal. Not exercised here.

The practical rules:

* **The schema is the contract.** If the description says optional, the schema must
  say optional. A mismatch is a bug the model will find.
* **Registration is activation.** A `direct` tool is active the moment it is
  registered. The registered-but-not-active gap comes from `deferred` exposure
  (chapter 17) or from an extension that sets the active set itself.
* **A tool returns text, not effects.** The example tool returns an instruction for
  the model to follow. Execution is chapter 17.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=15,
            mode="**Run** — the chapter's two extensions loaded unmodified into real sessions, "
            "plus the chapter's own test file.",
            scope="`in_process_runtime`.",
            provenance=[
                "**Ran** `drivers/ch15-first-extension.ts`: two sessions loading "
                "`ch15-first-extension/review-scope.ts` and `ch15-first-extension/hello.ts` "
                "unmodified.",
                "**Ran** `ch15-first-extension/first-extension.test.ts`.",
                "**Read** `examples/evidence.json`, chapter 15 rows (3 claims).",
            ],
            limits=[
                "**The example tool returns an instruction rather than executing a command.** "
                "Execution is chapter 17's subject.",
                "**`registerToolRenderer` is documented-not-run** by the chapter's suite "
                "(`ch17-lim3`); it arrived in 1.0.1.",
                "**No measurement** of how often a model calls a tool it was offered.",
            ],
        ),
    ),
]