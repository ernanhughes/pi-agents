"""Chapter 11 - Four Ways to Change Pi."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Four Ways to Change Pi"
QUESTION = """Two requirements of *different kinds* — \"never force push\" and \"confirm
before anything under `migrations/`\". **Which of them can a person wave through,
and what does the blocked call actually do?**

The chapter's answer is that a guard is a *procedure*, and the two halves are
different code. This notebook separates them and checks the blocked half against
the filesystem, not against the transcript."""

CELLS = [
    (
        "md",
        establishes(
            [
                "A force push is **refused outright**: no confirmation is offered, the tool "
                "result is an error, and no file appears.",
                "An ordinary `git push`, or anything mentioning `migrations/`, is a "
                "**question**: one confirmation is shown, and the answer decides whether the "
                "command runs.",
                "With **no UI to ask**, the confirming half takes the safe branch and blocks. "
                "A headless run cannot approve anything.",
                "The retained pre-fix guard shows the contrast on the same scenario: it "
                "*asks* about a force push, and a person who says yes lets it through.",
            ],
            [
                "**A guard is a procedure, not containment.** `metadata/11-chapter.yaml` "
                "records that the four rules, the four questions and the placement table are "
                "**proposed** by this book. Chapter 42 is about the half that must *hold*.",
                "**The procedure assumes the need is classifiable.** A command that means "
                "`git push` without containing it will not match, and the chapter says so.",
                "**The commands really run.** `git push` fails here because the temporary "
                "directory is not a repository; that is the *tool's* honest failure and it is "
                "what makes the effect check meaningful — the flag file is created before the "
                "push in every allowed case.",
            ],
        ),
    ),
    *setup_cells(
        11,
        mode="**Run** — the chapter's own guard extension loaded unmodified into real sessions, "
        "plus the retained pre-fix version as a control.",
        scope="`in_process_runtime`. The gate is the extension's; the tool is Pi's `bash`; the "
        "model is scripted.",
    ),
    (
        "md",
        """## Baseline: one extension, two kinds of rule

`ch11-guard/guard.ts` is 16 lines and contains both halves:

* a **prohibition** — a force push matches a list and returns `{ block: true }` with a
  reason, with no question asked;
* a **confirmation** — anything else matching `git push` or `migrations/` calls
  `ctx.ui.confirm`, and the answer decides.

The driver runs each case in its own session and reports three things: how many
confirmations were shown, whether the tool result was an error, and whether a file
the command would create actually exists.""",
    ),
    (
        "code",
        'GUARD = pinb.driver_source("ch11-guard.ts")\n'
        'guard = pinb.driver(GUARD, label="ch11-guard", timeout=420)\n'
        'print(pinb.md_table(\n'
        '    ["case", "confirmations shown", "tool result", "ran.flag created?"],\n'
        '    [[guard[k]["label"], guard[k]["confirmsShown"],\n'
        '      "error" if guard[k]["results"][0]["isError"] else "ok",\n'
        '      "YES" if guard[k]["ran"][0] else "no"] for k in guard],\n'
        "))\n"
        'print()\n'
        'print("The reason the model received, in the two blocked cases:")\n'
        'print("  no UI      :", guard["noUI"]["results"][0]["text"])\n'
        'print("  person says no:", guard["ordinaryRefused"]["results"][0]["text"])\n'
        'print("  force push :", guard["forcePush"]["results"][0]["text"])',
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("a force push is refused with no question asked",\n'
        '               guard["forcePush"]["confirmsShown"] == 0 and guard["forcePush"]["results"][0]["isError"],\n'
        '               "0 confirmations, isError"),\n'
        '    pinb.check("and nothing ran", not guard["forcePush"]["ran"][0], "ran.flag absent"),\n'
        '    pinb.check("an ordinary push asks exactly once", guard["ordinary"]["confirmsShown"] == 1, "1 confirmation"),\n'
        '    pinb.check("saying yes lets it run", guard["ordinary"]["ran"][0] is True, "ran.flag present"),\n'
        '    pinb.check("saying no blocks it and nothing runs",\n'
        '               guard["ordinaryRefused"]["results"][0]["isError"] and not guard["ordinaryRefused"]["ran"][0],\n'
        '               guard["ordinaryRefused"]["results"][0]["text"]),\n'
        '    pinb.check("a migrations/ path is treated the same way",\n'
        '               guard["migrations"]["confirmsShown"] == 1 and guard["migrations"]["ran"][0] is True,\n'
        '               "asked once, then ran"),\n'
        '    pinb.check("an unrelated command is left alone",\n'
        '               guard["quiet"]["confirmsShown"] == 0 and not guard["quiet"]["results"][0]["isError"],\n'
        '               "no question, ran cleanly"),\n'
        '    pinb.check("with no UI the confirming half blocks rather than allowing",\n'
        '               guard["noUI"]["confirmsShown"] == 0 and not guard["noUI"]["ran"][0],\n'
        '               "0 confirmations, nothing ran"),\n'
        "])",
    ),
    (
        "md",
        """## Contrasting case: the guard before it was fixed

The repository keeps `ch11-guard/guard-original.ts` for exactly this reason — the
first version treated a force push as a question. The two rows below are the same
scenario under the two guards.

The difference is not the pattern; it is the **kind of rule**. A prohibition with a
question attached is not a prohibition, because a person can say yes.""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["guard", "scenario", "confirmations", "ran.flag created?"],\n'
        '    [["current", "a force push", guard["forcePush"]["confirmsShown"], "YES" if guard["forcePush"]["ran"][0] else "no"],\n'
        '     ["pre-fix", "a force push", guard["originalForcePush"]["confirmsShown"], "YES" if guard["originalForcePush"]["ran"][0] else "no"],\n'
        '     ["current", "an ordinary push", guard["ordinary"]["confirmsShown"], "YES" if guard["ordinary"]["ran"][0] else "no"],\n'
        '     ["pre-fix", "an ordinary push", guard["originalOrdinary"]["confirmsShown"], "YES" if guard["originalOrdinary"]["ran"][0] else "no"]],\n'
        "))\n"
        "\n"
        "pinb.show_checks([\n"
        '    pinb.check("the current guard refuses a force push", not guard["forcePush"]["ran"][0], "refused"),\n'
        '    pinb.check("the pre-fix guard lets a person approve one", guard["originalForcePush"]["ran"][0] is True,\n'
        '               "approved, and the command ran"),\n'
        '    pinb.check("both guards still ask about an ordinary push",\n'
        '               guard["ordinary"]["confirmsShown"] == 1 and guard["originalOrdinary"]["confirmsShown"] == 1,\n'
        '               "1 confirmation each"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

The driver above is built from the chapter's guard; the assertion set that belongs
to the chapter is its test file, which also covers the "no UI to ask" branch and the
migrations half directly.""",
    ),
    *canonical_tests(
        11,
        "ch11-guard/guard.test.ts",
        what="The chapter's canonical evidence",
        show="guard",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** Add a third kind of rule to the guard: anything touching
`production` is refused outright, like a force push. Which existing case would that
have to be distinguished from — and what happens to the `git push` confirmation if
you get the order wrong?

**Then change one input.** `COMMAND` below is what the model asks for. Run it with
a force push, then with `git push`, then with an unrelated command.

**Predict the boundary.** The force-push pattern is matched against
`JSON.stringify(event.input)`, not against the raw argument. What would a command
that *contains the words* `git push --force` inside a quoted string do — block, or
let through?""",
    ),
    (
        "code",
        'COMMAND = "git push origin main"\n'
        "\n"
        'print("Current pattern:", r"/\\bgit\\s+push\\b.*(?:\\s--force\\b|\\s-f\\b|--force-with-lease\\b)/")\n'
        'print("Matched against JSON.stringify(event.input), not the raw argument.")\n'
        "print()\n"
        "\n"
        "cases = {\n"
        '    "git push --force origin main": True,\n'
        '    "git push -f origin main": True,\n'
        '    "git push --force-with-lease origin main": True,\n'
        '    "git push origin main": False,\n'
        '    \'echo "remember to git push --force later"\': True,\n'
        '    "git  push   --force": True,\n'
        "}\n"
        "pattern = __import__(\"re\").compile(r\"\\bgit\\s+push\\b.*(?:\\s--force\\b|\\s-f\\b|--force-with-lease\\b)\")\n"
        "print(\"Predict, then check, for each command:\")\n"
        "for command, expected in cases.items():\n"
        '    matched = bool(pattern.search(__import__("json\").dumps({"command": command})))\n'
        '    print(f"  {command!r:52s} blocked={matched}")\n'
        "print()\n"
        'print("The last row is the answer to the boundary question: the pattern matches the")\n'
        'print("serialised input, so a *mention* of a force push inside a quoted string")\n'
        'print("blocks a command that was never going to force push. Refusing is the safe")\n'
        'print("direction; allowing would not be.")',
    ),
    (
        "md",
        """## Interpretation

The chapter's four ways to change Pi are a spectrum, and this notebook puts a number
on the difference between the two ends:

| Kind of rule | Where it lives | Can a person override it? | Does it hold without a person? |
|---|---|---|---|
| **prohibition** | the extension's own code | no — there is nothing to approve | **yes**, including headless |
| **confirmation** | `ctx.ui.confirm` | yes, by answering | no — with no UI it must pick, and the safe pick is to block |
| instruction (chapters 12–14) | files the model reads | yes, by editing the file | no — it is prose |
| the model's own judgement | nowhere | n/a | no |

A guard that is only the second row is a speed bump. The value of the first row is
that it does not depend on anybody being present — which is exactly the case the
`noUI` row above measures.

### What this chapter does not settle

`metadata/11-chapter.yaml` records that the guard is a **procedure over a serialised
command string**, and that the procedure assumes the need can be classified into one
of four kinds. A command that means `git push` without saying so defeats it. That is
not a bug in the guard; it is the boundary between a procedure and containment, and
chapter 42 is the chapter about containment.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=11,
            mode="**Run** — eight real sessions loading the chapter's guard and its retained "
            "pre-fix version, plus the chapter's own test file.",
            scope="`in_process_runtime`. The gate is extension code under test; the tool is "
            "Pi's `bash`; the model is scripted.",
            provenance=[
                "**Ran** `drivers/ch11-guard.ts`: eight sessions, each with its own temporary "
                "agent directory and working directory, loading `ch11-guard/guard.ts` and "
                "`ch11-guard/guard-original.ts` unmodified.",
                "**Checked the filesystem in every case** (`ran.flag`), so \"blocked\" means "
                "no effect rather than an error-shaped message.",
                "**Ran** `ch11-guard/guard.test.ts`.",
                "**Read** `examples/evidence.json`, chapter 11 rows (6 claims).",
            ],
            limits=[
                "**Commands really execute.** `git push` fails here because the temporary "
                "directory is not a repository. That is why the allowed cases are read from "
                "the flag file rather than from the push's own output.",
                "**A `UiRecorder` stands in for a person.** Its answers are queued by the "
                "driver. That is enough to observe *whether* a question was asked and what "
                "the answer decided; it is not a study of how a person answers.",
                "**No real model.** The scripted model asked for the commands; nothing here "
                "is evidence about whether a model would try to force push.",
                "**The pattern-matching exercise is Python**, restating the extension's own "
                "regex so the boundary can be inspected. The authoritative check that the "
                "guard blocks is the session run above and the chapter's tests.",
            ],
        ),
    ),
]