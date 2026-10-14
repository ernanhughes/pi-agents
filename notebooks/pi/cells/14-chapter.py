"""Chapter 14 - Skills That Carry Files."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Skills That Carry Files"
QUESTION = """A skill that ships a script: **which repository does that script resolve**, and
does `set -euo pipefail` change what a failing script reports?

The chapter's point is that a skill is not a file — it is a *location* plus a
convention. The script has to find the repository itself, and the two lines at the
top decide whether a failure is visible or silently swallowed."""

CELLS = [
    ("md", heading(14, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "The provider's system prompt carries the skill's **path** — so a relative "
                "path in `SKILL.md` can be resolved — but **not** the body of a bundled "
                "file. A bundled file reaches the context only when the model reads it with "
                "its own `read` tool.",
                "A bundled script resolves the **repository it was launched in**, not a "
                "directory it counted up to, and not a decoy repository named in the "
                "frontmatter.",
                "`PI_REVIEW_GUARD_ROOT` overrides discovery, so one installed skill can serve "
                "several repositories.",
                "`set -euo pipefail` makes a failing script exit non-zero; without it the "
                "same failure exits **zero** and prints `reached the end`.",
            ],
            [
                "**Six of the chapter's eight tests skip** when no usable POSIX shell exists. "
                "The driver reports `shell.available` and `gitAvailable` so the result can be "
                "read with its platform caveat attached.",
                "**No token budget for `SKILL.md`** is documented, and the size rule of thumb "
                "is the author's recommendation, not a Pi limit (`ch14-lim1`).",
                "**Skill frontmatter does not become an environment variable.** The three "
                "genuine ways to pass a value — an exported variable, a bundled config, a "
                "wrapper script — are the author's pattern, not a documented Pi feature "
                "(`ch14-lim2`).",
                "**Repository discovery is a convention, not containment.** Chapter 42 owns "
                "containment.",
            ],
        ),
    ),
    *setup_cells(
        14,
        mode="**Run** — a real git repository with a real `run-checks.sh`, a stand-in `pnpm` "
        "on `PATH`, and a real session whose provider prompt is read back.",
        scope="`in_process_runtime`. The shell and `git` are the reader's; the discovery rule, "
        "the path-in-prompt rule and the exit-code rule are Pi's.",
    ),
    (
        "md",
        """## Baseline: what the model is told, and what it has to go and read

Two separate questions, one driver.

**Context.** The skill's `SKILL.md` tells the model where the skill lives. A bundled
`CHECKLIST.md` sits beside it. The driver checks whether the provider's system
prompt contains the skill's path, and whether it contains the checklist's marker —
then has the model call `read` on the checklist and checks whether the marker
arrives in the tool result.

**Shell.** A real `run-checks.sh` in a real git repository, run from an unrelated
directory with a stand-in `pnpm` on `PATH`, twice: once with `set -euo pipefail` and
once without.""",
    ),
    (
        "code",
        'SKILL_FILES = pinb.driver_source("ch14-skill-files.ts")\n'
        'skill = pinb.driver(SKILL_FILES, label="ch14-skill-files", timeout=420)\n'
        'ctx, shell = skill["context"], skill["shell"]\n'
        'print("shell available:", shell["available"], "| git available:", shell["gitAvailable"])\n'
        "print()\n"
        'print("What the provider was told, and what the model had to read:")\n'
        'print(pinb.md_table(\n'
        '    ["planted in", "where it appears"],\n'
        '    [["the skill\'s path", "the provider\'s system prompt" if ctx["pathInPrompt"] else "nowhere"],\n'
        '     ["the bundled file\'s marker", "the provider\'s system prompt" if ctx["bodyMarkerInPrompt"] else "nowhere"],\n'
        '     ["the bundled file\'s marker", "the tool result after the model called read" if ctx["markerAfterRead"] else "nowhere"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("the skill\'s path reaches the provider, so relative paths can be resolved",\n'
        '               ctx["pathInPrompt"], "path present"),\n'
        '    pinb.check("the bundled file\'s body does NOT reach the provider",\n'
        '               not ctx["bodyMarkerInPrompt"], "absent from the system prompt"),\n'
        '    pinb.check("the bundled file\'s body does NOT reach the provider by name either",\n'
        '               not ctx["namesScriptInBody"], "the script is not named in the prompt"),\n'
        '    pinb.check("it arrives only when the model reads it with its own tool",\n'
        '               ctx["markerAfterRead"] and ctx["toolResultsAfterRead"] == 1,\n'
        '               "one read, one tool result"),\n'
        "])",
    ),
    (
        "md",
        """The asymmetry is the whole design. The model is told **where** the skill lives
and **what it is for**. It is not told what is in the bundled files. Those cost
tokens only when the model decides to read them — which is the difference between
a skill that is *available* and a skill that is *loaded*.

## Experiment: which repository does the script resolve

Three runs of the same script from three different working directories. The script
prints the repository it resolved and then runs the stand-in `pnpm`.

The third run is the one that matters: `PI_REVIEW_GUARD_ROOT` points somewhere
else, and the script still resolves the **launch** repository.""",
    ),
    (
        "code",
        'p, o, ov = shell["project"], shell["outside"], shell["override"]\n'
        'print(pinb.md_table(\n'
        '    ["run", "resolved the launch repository?", "exit", "ran both steps?"],\n'
        '    [["from the repository root", p["resolvedLaunchRepo"], p["status"], p["ranBothSteps"]],\n'
        '     ["from an unrelated directory", o["resolvedLaunchRepo"], o["status"], o.get("mentionsSkillDir", False)],\n'
        '     ["with PI_REVIEW_GUARD_ROOT set elsewhere", ov["resolvedOtherRepo"], "-", "-"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("from the repository root, the script resolves that repository",\n'
        '               p["resolvedLaunchRepo"] and p["status"] == 0, "resolved, exit 0"),\n'
        '    pinb.check("from an unrelated directory, it still resolves the launch repository",\n'
        '               o["resolvedLaunchRepo"] and o["status"] == 0, "resolved, exit 0"),\n'
        '    pinb.check("PI_REVIEW_GUARD_ROOT overrides discovery to a different repository",\n'
        '               ov["resolvedOtherRepo"], "resolved elsewhere"),\n'
        "])",
    ),
    (
        "md",
        """## Contrasting case: two lines decide whether a failure is visible

The same script, run twice. The only difference is `set -euo pipefail` at the top.
The stand-in `pnpm` fails on its first step.

The strict run exits non-zero and stops. The lax run exits **zero** and prints
`reached the end` — which is the difference between a failing check that is
visible and a failing check that looks like a pass.""",
    ),
    (
        "code",
        'strict, lax = shell["strictExit"], shell["laxExit"]\n'
        'print(pinb.md_table(\n'
        '    ["script", "exit code", "reached the end?"],\n'
        '    [["with set -euo pipefail", strict, "no" if not shell["strictReachedEnd"] else "yes"],\n'
        '     ["without it", lax, "yes" if shell["laxReachedEnd"] else "no"]],\n'
        "))\n"
        "\n"
        "if not shell[\"available\"]:\n"
        '    pinb.unrun("the exit-code case", "no usable POSIX shell (Git Bash or bash on PATH)")\n'
        "else:\n"
        "    pinb.show_checks([\n"
        '        pinb.check("with set -euo pipefail the failing script exits non-zero",\n'
        '                   strict != 0, str(strict)),\n'
        '        pinb.check("without it the same failure exits zero",\n'
        '                   lax == 0, str(lax)),\n'
        '        pinb.check("and the lax run reports success it did not earn",\n'
        '                   shell["laxReachedEnd"], "reached the end"),\n'
        "    ])\n"
        '    assert strict != 0 and lax == 0',
    ),
    (
        "md",
        """## The chapter's own tests

The driver above is built from the chapter's fixtures. The chapter's eight tests
add the frontmatter-is-not-an-environment-variable row, the bundled-config row and
the model-is-told-where-the-skill-lives row, and they **skip with a reason** when no
usable shell exists — which is the honest way to handle a platform dependency.""",
    ),
    *canonical_tests(
        14,
        "ch14-skill-files/skill-files.test.ts",
        what="The chapter's canonical evidence",
        show="repository",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** Remove `set -euo pipefail` from the script and make the
stand-in `pnpm` fail on its **second** step instead of its first. Does the exit code
change? Does `reached the end` still print?

**Then change one input.** `STEPS` below is how many steps the stand-in `pnpm`
runs before failing. Try `1` and `3`.

**Predict the boundary.** The script resolves the repository with
`git rev-parse --show-toplevel`. What happens in a subdirectory of the repository?
What happens in a directory that is not in a repository at all — and is that failure
loud or quiet?""",
    ),
    (
        "code",
        'STEPS = 2\n'
        'print("predicted: with set -euo pipefail, the script exits non-zero at step", STEPS)\n'
        'print("            and does not reach the end.")\n'
        "print()\n"
        'print("The script resolves the repository with git rev-parse --show-toplevel.")\n'
        'print("  in a subdirectory  -> the repository root, not the subdirectory")\n'
        'print("  outside a repository -> git fails, and with set -e the script stops there")\n'
        "print()\n"
        'print("The chapter\'s own test asserts the subdirectory case explicitly:")\n'
        'print("  \\"a project skill checks the repository it was launched in, not a directory")\n'
        'print("   it counted to\\"")\n'
        "\n"
        'assert shell["strictExit"] != 0, "the strict script fails loudly"\n'
        'assert shell["laxExit"] == 0, "the lax script fails silently"\n'
        'print()\n'
        'print("held: two lines at the top decide whether a failure is visible")',
    ),
    (
        "md",
        """## Interpretation

A skill that carries files is three mechanisms, and each one has a failure mode that
is quiet:

| Mechanism | What it does | The quiet failure |
|---|---|---|
| the path in the system prompt | lets the model resolve relative paths | a wrong path is a 404, not an error |
| `git rev-parse` in the script | finds the repository | outside a repository it fails — loudly only with `set -e` |
| the bundled file | reaches the context only when read | the model never reads it, and nothing says so |

The practical rules:

1. **Put `set -euo pipefail` in every bundled script.** Without it, a failing check
   reports success. That is the difference between a check and a decoration.
2. **Resolve the repository from the launch directory, not from `$0`.** A skill
   installed once and used from many repositories must follow the launch directory.
3. **Do not put values in frontmatter and expect them as environment variables.**
   They are not. Use an exported variable, a bundled config, or a wrapper script.

### What this chapter does not settle

`metadata/14-chapter.yaml` records two limits that survive here: Pi documents **no
token budget** for `SKILL.md`, and the three ways to pass a value to a bundled
script are the author's pattern rather than a documented feature. The size rule of
thumb in the chapter is a recommendation, not a limit.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=14,
            mode="**Run** — a real git repository with a real `run-checks.sh` and a stand-in "
            "`pnpm`, plus a real session whose provider prompt is read back.",
            scope="`in_process_runtime`. The shell and `git` are the reader's.",
            provenance=[
                "**Ran** `drivers/ch14-skill-files.ts`: three runs of a real `run-checks.sh` "
                "in a real temporary git repository, from three different working directories, "
                "plus a real session with a bundled `CHECKLIST.md`.",
                "**Read the provider's system prompt** via the book's "
                "`systemPromptSeenByProvider`.",
                "**Ran** `ch14-skill-files/skill-files.test.ts`.",
                "**Read** `examples/evidence.json`, chapter 14 rows (8 claims).",
            ],
            limits=[
                "**Platform-dependent.** The driver reports `shell.available` and "
                "`gitAvailable`; six of the chapter's eight tests skip with a reason when no "
                "usable POSIX shell exists. The exit-code case above is guarded the same way.",
                "**The stand-in `pnpm` is a script**, not the real tool. It fails on a chosen "
                "step so the exit-code behaviour is observable without a real build.",
                "**Repository discovery is a convention, not containment.** A script that "
                "resolves the repository can also be told to resolve a different one; "
                "`PI_REVIEW_GUARD_ROOT` is the documented override.",
            ],
        ),
    ),
]