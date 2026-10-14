"""Chapter 09 - Shells, Processes, and Environment Variables."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Shells, Processes, and Environment Variables"
QUESTION = """When the model runs `bash` and when **you** type `!`, are those the same
shell with the same variables? **Compare the two environments directly.**

The chapter's title case is an alias: something that works when you type it, failing
when the model runs it, with no error message that explains why."""

CELLS = [
    ("md", heading(9, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "The model's `bash` tool receives the **session variables** — `PI_SESSION_ID`, "
                "`PI_PROVIDER`, `PI_MODEL`, `PI_REASONING_LEVEL`, `PI_SESSION_FILE`. The "
                "operator's `!` command does **not**: `PI_SESSION_ID` is empty there.",
                "`PI_SESSION_FILE` is populated for a persisted session and empty for an "
                "ephemeral one, which is the documented way for a script to tell.",
                "`shellCommandPrefix` runs before **both** entry points.",
                "A non-zero exit is reported as a result the model can read: the output is in "
                "the result text and `isError` is true.",
            ],
            [
                "**The shell is whatever Pi resolved on this machine.** The run below "
                "records the resolved `bash` path. The chapter states the same caveat: these "
                "ran under Git Bash on Windows, and on another platform the shell — and "
                "therefore the alias result — may differ.",
                "**No container, no isolation.** `metadata/09-chapter.yaml` records "
                "containerization as out of scope; it is chapter 42's subject.",
                "**Nothing about `powershell` / `pwsh`.** Those are available only to a "
                "native Windows Pi process, while your own `!` commands keep using Bash.",
                "**`AI_AGENT=pi` and `PI_CODING_AGENT=true`** are set by the CLI and RPC "
                "entry points only, not automatically through the SDK, and are not read here.",
            ],
        ),
    ),
    *setup_cells(
        9,
        mode="**Run** — the same command string through the model's `bash` tool and through "
        "`session.executeBash`, in one real session.",
        scope="`in_process_runtime`. The shell is the reader's; the session variables and the "
        "prefix handling are Pi's.",
    ),
    (
        "md",
        """## Experiment 1: two callers, two environments

One session. One command string that prints the session variables. Run once as the
model's tool call and once as the operator's `!` command.

The interesting cells are the two that are *empty*: they are the boundary.""",
    ),
    (
        "code",
        'SHELL = pinb.driver_source("ch09-shell.ts")\n'
        'shell = pinb.driver(SHELL, label="ch09-shell", timeout=300)\n'
        'vars_row = shell[0]\n'
        'plain = next(r for r in shell if r["label"] == "a plain echo")\n'
        'failing = next(r for r in shell if r["label"] == "a command that exits 3")\n'
        'prefixed = next(r for r in shell if r["label"] == "with shellCommandPrefix set")\n'
        "\n"
        'print("The same command, two callers:")\n'
        'print(pinb.md_table(\n'
        '    ["variable", "the model\'s bash tool", "your ! command"],\n'
        '    [["PI_SESSION_ID", vars_row["id"], vars_row["bangId"]],\n'
        '     ["PI_SESSION_FILE", vars_row["file"], vars_row["bangFile"]]],\n'
        "))\n"
        'print()\n'
        'print(pinb.md_table(\n'
        '    ["case", "via the model", "via !", "identical?"],\n'
        '    [[plain["label"], plain["viaModel"]["text"], plain["viaBang"]["output"], plain["sameOutput"]],\n'
        '     [prefixed["label"], prefixed["viaModel"]["text"], prefixed["viaBang"]["output"], prefixed["sameOutput"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("the model\'s tool sees PI_SESSION_ID", vars_row["modelSawSessionId"], vars_row["id"]),\n'
        '    pinb.check("your ! command does not", not vars_row["bangSawSessionId"], vars_row["bangId"]),\n'
        '    pinb.check("PI_SESSION_FILE is populated for a persisted session, in the model\'s tool only",\n'
        '               vars_row["modelSawSessionFile"] and not vars_row["bangSawSessionFile"], vars_row["file"]),\n'
        '    pinb.check("an ordinary command produces identical output either way", plain["sameOutput"], plain["viaModel"]["text"]),\n'
        '    pinb.check("a non-zero exit is a readable result, and isError is true",\n'
        '               failing["isError"] is True and "about-to-fail" in failing["text"] and "3" in failing["text"],\n'
        '               failing["text"].replace(chr(10), " | ")),\n'
        '    pinb.check("shellCommandPrefix reaches both entry points",\n'
        '               prefixed["sameOutput"] and prefixed["viaModel"]["text"] == "yes",\n'
        '               "FROM_PREFIX was visible to the model and to !"),\n'
        "])",
    ),
    (
        "md",
        """The asymmetry is not a bug and it is not subtle once you see it: the session
variables are injected for **the model's** subprocess, not for yours.

## Contrasting case: the alias

The chapter's title case, and the most useful thing on this page. An alias defined
in an operator's interactive profile does not exist in Pi's fresh non-interactive
shell — and once `shellCommandPrefix` enables alias expansion and defines it, it
does.

The driver records which shell was used, so the result can be read with its
platform caveat attached.""",
    ),
    (
        "code",
        'ALIAS = pinb.driver_source("ch09-alias.ts")\n'
        'alias = pinb.driver(ALIAS, label="ch09-alias", timeout=300)\n'
        'print("shell Pi resolved:", alias["shell"]["bashPath"], "| usable:", alias["shell"]["bashWorks"])\n'
        "print()\n"
        'print(pinb.md_table(\n'
        '    ["configuration", "the model runs `myalias`", "isError"],\n'
        '    [["default", alias["withoutPrefix"]["text"].splitlines()[0], alias["withoutPrefix"]["isError"]],\n'
        '     ["shellCommandPrefix enables + defines", alias["withPrefix"]["text"].splitlines()[0], alias["withPrefix"]["isError"]]],\n'
        "))\n"
        "\n"
        "if not alias[\"shell\"][\"bashWorks\"]:\n"
        '    pinb.unrun("the alias case", "no usable POSIX shell (Git Bash or bash on PATH)")\n'
        "else:\n"
        "    pinb.show_checks([\n"
        '        pinb.check("without a prefix the alias does not exist",\n'
        '                   alias["withoutPrefix"]["isError"] is True, alias["withoutPrefix"]["text"].splitlines()[0]),\n'
        '        pinb.check("with the prefix it resolves",\n'
        '                   alias["withPrefix"]["isError"] is False and "aliased-ok" in alias["withPrefix"]["text"],\n'
        '                   alias["withPrefix"]["text"].splitlines()[0]),\n'
        "    ], strict=False)\n"
        '    assert alias["withPrefix"]["isError"] is False',
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** `shellCommandPrefix: "export FROM_PREFIX=yes"` was visible to
both callers above. What about `cd /somewhere` — would *your* next `!` command also
start in `/somewhere`, or is the prefix per-process?

**Then change one input.** `PREFIX` below is what Pi runs before each command. Try
one that **fails**: `exit 1`.

**Predict the boundary.** If the prefix exits non-zero, does the command still
run? What does the model see?""",
    ),
    (
        "code",
        'PREFIX = "exit 1"\n'
        'COMMAND = "echo after-the-prefix"\n'
        'print(f"predicted: with prefix {PREFIX!r}, {COMMAND!r} does not run and the model sees the failure")\n'
        "print()\n"
        "broken = pinb.driver(\n"
        "    ALIAS,\n"
        '    label="ch09-broken-prefix",\n'
        "    timeout=300,\n"
        '    env={"NB_COMMAND": COMMAND, "NB_PREFIX": PREFIX},\n'
        ")\n"
        'print("prefix:", repr(PREFIX), " command:", repr(COMMAND))\n'
        'print("without a prefix: isError =", broken["withoutPrefix"]["isError"], "text =", repr(broken["withoutPrefix"]["text"][:120]))\n'
        'print("with that prefix: isError =", broken["withPrefix"]["isError"], "text =", repr(broken["withPrefix"]["text"][:120]))\n'
        "\n"
        'assert broken["withPrefix"]["isError"] is True, "a failing prefix fails the command"\n'
        'assert broken["withoutPrefix"]["isError"] is False and "after-the-prefix" in broken["withoutPrefix"]["text"]\n'
        'print()\n'
        'print("held: the prefix is part of the command, so its failure is the command\'s failure")',
    ),
    (
        "md",
        """## Interpretation

Three rules, all visible above:

1. **Session variables are for the model's subprocess.** If you want to know the
   session id from your own `!` command, read `session.sessionId` in an extension —
   or use a custom command, which is what chapters 12 and 20 are for.
2. **The shell is fresh and non-interactive.** Nothing from your interactive profile
   is there: no aliases, no `~/.bashrc`, no exported functions. `shellCommandPrefix`
   is the documented seam for putting something back.
3. **A non-zero exit is readable data, not an opaque failure.** The command's output
   is in the result and the model can act on it. Chapter 17 makes the same point
   about tools in general.

### What this chapter does not settle

The platform caveat is real and the chapter states it: these results are from Git
Bash on Windows, and the shell Pi resolves — and therefore the alias row — may
differ on your machine. The driver prints the resolved path so you can tell which
shell produced the result you are looking at.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=9,
            mode="**Run** — real subprocesses launched by Pi's own `bash` tool and by "
            "`session.executeBash`, plus the chapter's own test file.",
            scope="`in_process_runtime`. The shell is the reader's; the variables, the prefix "
            "and the result shape are Pi's.",
            provenance=[
                "**Ran** `drivers/ch09-shell.ts` and `drivers/ch09-alias.ts`, each creating "
                "its own sessions with their own temporary agent directories.",
                "**Ran** `ch09-shell/shell.test.ts`, which covers the thinking-level change "
                "and the ephemeral `PI_SESSION_FILE` rows that this driver does not repeat.",
                "**Read** `examples/evidence.json`, chapter 9 rows (7 claims).",
            ],
            limits=[
                "**Platform-dependent by nature.** `bashPath()` and `bashWorks()` are read "
                "from the book's own helper and printed above; the alias result depends on "
                "which shell that is.",
                "**`powershell` and `pwsh` were not run.** They are available only to a "
                "native Windows Pi process, and the operator's own `!` commands keep using "
                "Bash, so the two-caller comparison here is Bash-only.",
                "**The thinking-level row is not repeated here** — a session variable "
                "resolved at command start is asserted by the chapter's own test, which ran "
                "above.",
                "**No isolation.** Commands run with the notebook's own permissions in a "
                "temporary directory.",
            ],
        ),
    ),
]
