"""Chapter 13 - Skills."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Skills"
QUESTION = """Does the model's context carry a skill's **body**, or only enough to decide
whether it is relevant?**

This is the whole design of the feature, and it is checkable in one string: read
what the provider received and look for a marker planted in the body."""

CELLS = [
    ("md", heading(13, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "The provider's system prompt carries a skill's **name**, **description** "
                "and **path**, and **not** its body. A marker string planted in the body "
                "never appears.",
                "A skill with **no description is not loaded at all** — a silent "
                "disappearance, not an error.",
                "`disable-model-invocation: true` hides a skill from the model while "
                "`/skill:name` still loads its body as the request.",
                "Skills are discovered **recursively**; two skills with the same name keep "
                "the first discovered, and only its description reaches the model.",
            ],
            [
                "**No routing quality is measured.** Pi exposes no way to score whether a "
                "description routed correctly, and `metadata/13-chapter.yaml` records that "
                "namespacing similar descriptions stays open (`ch13-q2`). Nothing here "
                "measures it.",
                "**Skills installed on the machine running the notebook are also "
                "discovered.** The chapter says so, and the driver therefore filters its "
                "report to the skills it created — otherwise a test asserting \"exactly "
                "one skill\" would fail on a developer machine and pass on CI.",
                "**A description is not a permission.** Nothing here establishes that the "
                "model will read a body it was offered.",
            ],
        ),
    ),
    *setup_cells(
        13,
        mode="**Run** — real skills on disk, loaded by Pi's own resource loader, with the "
        "provider's system prompt read back.",
        scope="`in_process_runtime`. Discovery and the description-in-context rule are Pi's.",
    ),
    (
        "md",
        """## Baseline: one skill, three markers

The skill body contains `SECRET-BODY-TEXT`. The name, the description and the path
are planted separately so they can be looked for individually.

`systemPromptSeenByProvider` is the book's own helper: it runs one scripted turn and
returns the system message text exactly as the provider received it.""",
    ),
    (
        "code",
        'SKILLS = pinb.driver_source("ch13-skills.ts")\n'
        'skills = pinb.driver(SKILLS, label="ch13-skills", timeout=420)\n'
        'loaded = skills["loaded"]\n'
        'print("skill:")\n'
        'print("    name:        review-guard")\n'
        'print("    description: Reviews changed code. Use when reviewing a diff.")\n'
        'print("    body:        SECRET-BODY-TEXT")\n'
        "print()\n"
        'print(pinb.md_table(\n'
        '    ["planted in the", "does the provider\'s system prompt contain it?"],\n'
        '    [["name", "YES" if loaded["carriesName"] else "no"],\n'
        '     ["description", "YES" if loaded["carriesDescription"] else "no"],\n'
        '     ["path (SKILL.md)", "YES" if loaded["carriesPath"] else "no"],\n'
        '     ["body", "YES" if loaded["carriesBody"] else "no"]],\n'
        "))\n"
        'print("discovered skills (this run\'s fixtures only):", ", ".join(loaded["discovered"]))',
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("the name reaches the model", loaded["carriesName"], "yes"),\n'
        '    pinb.check("the description reaches the model", loaded["carriesDescription"], "yes"),\n'
        '    pinb.check("the path reaches the model, so relative paths can be resolved",\n'
        '               loaded["carriesPath"], "yes"),\n'
        '    pinb.check("the body does not", not loaded["carriesBody"], "no: the marker is absent"),\n'
        '    pinb.check("the skill was discovered", loaded["discovered"] == ["review-guard"],\n'
        '               ", ".join(loaded["discovered"])),\n'
        "])",
    ),
    (
        "md",
        """That is the entire mechanism in one table. The model is told enough to decide
whether the skill is relevant, and nothing more. The body costs tokens only if
somebody reads it.

## Contrasting cases: three ways a skill stays out

Each row below is a separate session with a different fixture.

* **no description** — the skill is not loaded at all. There is no error and no
  warning; it is simply absent.
* **`disable-model-invocation: true`** — loaded, discoverable, and reachable by
  `/skill:name`, but absent from the model's context.
* **two skills with the same name** — one survives, and it is the first discovered.""",
    ),
    (
        "code",
        'noDesc = skills["noDescription"]\n'
        'manual = skills["manualOnly"]\n'
        'nested = skills["nested"]\n'
        'collision = skills["collision"]\n'
        "\n"
        'print(pinb.md_table(\n'
        '    ["fixture", "discovered", "named in the model\'s context?"],\n'
        '    [["no description", ", ".join(noDesc["discovered"]) or "(nothing)", "no" if not noDesc["mentionsName"] else "yes"],\n'
        '     ["disable-model-invocation", ", ".join(manual["discovered"]) or "(nothing)", "no" if not manual["mentionsName"] else "yes"],\n'
        '     ["nested two levels down", ", ".join(nested["discovered"]) or "(nothing)", "yes" if nested["mentionsName"] else "no"],\n'
        '     ["two skills named review", ", ".join(collision["discovered"]) or "(nothing)",\n'
        '      ("first" if collision["first"] else "second") if collision["first"] != collision["second"] else "both"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("a skill with no description is not loaded at all",\n'
        '               noDesc["discovered"] == [] and not noDesc["mentionsName"], "absent from both lists"),\n'
        '    pinb.check("disable-model-invocation keeps it discoverable but invisible to the model",\n'
        '               manual["discovered"] == ["manual-only"] and not manual["mentionsName"],\n'
        '               "discovered, not described"),\n'
        '    pinb.check("skills are discovered recursively",\n'
        '               nested["discovered"] == ["nested-skill"] and nested["mentionsName"], "two levels down, found"),\n'
        '    pinb.check("a name collision keeps exactly one skill, the first discovered",\n'
        '               collision["discovered"] == ["review"] and collision["first"] != collision["second"],\n'
        '               "first description present, second absent"),\n'
        "])",
    ),
    (
        "md",
        """## The other half: `/skill:name` loads the body on purpose

The body is not *forbidden* from the context — it is *not volunteered*. The
`<skill>` block below carries the body, the location, and the arguments the operator
typed after it.""",
    ),
    (
        "code",
        'sent = skills["explicitLoad"]\n'
        'print("typed: /skill:manual-only src/auth only")\n'
        "print()\n"
        'print("the provider received:")\n'
        'for line in sent.splitlines():\n'
        '    print("   ", line)\n'
        "print()\n"
        "\n"
        "pinb.show_checks([\n"
        '    pinb.check("the body is in the request", "MANUAL-BODY-TEXT" in sent, "present"),\n'
        '    pinb.check("it arrives as a named block with a location",\n'
        '               "<skill" in sent and "location=" in sent, "<skill name=... location=...>"),\n'
        '    pinb.check("the operator\'s arguments are appended after the body",\n'
        '               sent.rstrip().endswith("src/auth only"), "arguments last"),\n'
        '    pinb.check("the block tells the model where it is", "References are relative to" in sent, "location stated"),\n'
        "])",
    ),
    *canonical_tests(
        13,
        "ch13-skills/skills.test.ts",
        what="The chapter's canonical evidence",
        show="skill",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** Move the body text into the **description**. Does the marker
reach the model now? What is the cost of doing that deliberately for a long skill?

**Then change one input.** `DESCRIPTION` below is what the skill advertises. Try
one that would plausibly route for a *different* task, and read the consequence.

**Predict the boundary.** A skill with no description is not loaded — silently. What
is the smallest change to the *loader* (not the skill) that would turn that
silence into a warning, and why did nobody add it?""",
    ),
    (
        "code",
'DESCRIPTION = "Reviews changed code. Use when reviewing a diff."\n'
        'BODY = "SECRET-BODY-TEXT"\n'
        "\n"
        'print("advertised (always in context):", DESCRIPTION)\n'
        'print("body (only when read):         ", BODY)\n'
        "print()\n"
        'print("rough size comparison, in characters rather than tokens:")\n'
        'print(pinb.table(\n'
        '    ["part", "chars", "share of the whole skill"],\n'
        '    [["description", len(DESCRIPTION), f"{len(DESCRIPTION) / (len(DESCRIPTION) + len(BODY)) * 100:.0f}%"],\n'
        '     ["body", len(BODY), f"{len(BODY) / (len(DESCRIPTION) + len(BODY)) * 100:.0f}%"]],\n'
        '    indent="",\n'
        "))"
    ),
    (
        "md",
        """## Interpretation

A skill is a **two-stage disclosure**:

```
always:    name + description + path          (cheap: a few dozen characters each)
on demand: the body, as a <skill> block      (expensive: whatever the author wrote)
```

The practical consequences:

1. **The description is the entire interface.** It is the only thing the model sees
   when deciding, so it is a routing decision written as prose. `ch13-q2` — how to
   keep two similar descriptions apart — is open, and nothing here measures routing
   quality.
2. **A missing description is not an error.** It is a skill that does not exist.
   When a skill "does not work", check the frontmatter first.
3. **Discovery depth differs from the previous mechanism.** Prompt templates are
   direct `.md` children; skills are recursive. If a skill "is not found", check the
   directory level before you check the name.

### What this chapter does not settle

Nothing here establishes that the model *reads* a body it was offered, or that it
reads the right one. That is a real-model question and this book has no
`real_model` evidence — the ledger's evidence scopes are `declarations`,
`in_process_runtime` and `shipped_binary`, and nothing else.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=13,
            mode="**Run** — six real skill fixtures discovered by Pi's own loader, with the "
            "provider's system prompt read back, plus the chapter's own test file.",
            scope="`in_process_runtime`.",
            provenance=[
                "**Ran** `drivers/ch13-skills.ts`: six sessions, each with its own temporary "
                "agent directory containing real `SKILL.md` files.",
                "**Read the provider's system prompt** via the book's "
                "`systemPromptSeenByProvider`, which captures it in a faux response factory.",
                "**Ran** `ch13-skills/skills.test.ts`.",
                "**Read** `examples/evidence.json`, chapter 13 rows (6 claims).",
            ],
            limits=[
                "**Skills installed on this machine are also discovered**, and the driver "
                "filters them out so the assertions are about the fixtures alone. This is "
                "the same trap the chapter's own tests guard against, and it is why a test "
                "of the form \"exactly one skill was discovered\" is unsafe on a developer "
                "machine.",
                "**No routing quality is measured.** Every result here is about *whether* a "
                "body is in context, never about whether the model would have chosen it.",
                "**The cost comparison in the exercise is in characters, not tokens**, and is "
                "reasoning material rather than a measurement.",
            ],
        ),
    ),
]
