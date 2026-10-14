"""Chapter 08 - The Project .pi Directory and Trust."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "The Project .pi Directory and Trust"
QUESTION = """Which project files are gated behind a trust decision, and **who wins when
several sources have an opinion?**

The ordering matters more than the gate. A repository cannot ask for trust, a
saved decision can be overridden by a flag, and print mode — which has nobody to
ask — quietly behaves as "skip"."""

CELLS = [
    ("md", heading(8, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "Nine documented project paths require a decision: the seven under "
                "`.pi/`, plus `.agents/skills/.../SKILL.md`. A bare `.pi/` directory does "
                "**not**, and neither do `AGENTS.md` / `CLAUDE.md`.",
                "`AGENTS.md` loads **regardless of trust**. Declining is not isolation: the "
                "extension and the prompt template stay out, the context file comes in.",
                "The decision order is **flag → extension handler → saved decision → "
                "`defaultProjectTrust`**, and an extension that answers `undecided` hands "
                "the decision on rather than making it.",
                "A saved decision for a directory covers its children; a child decision "
                "overrides without rewriting the parent, and setting a decision to `null` "
                "clears it.",
            ],
            [
                "**Print mode cannot ask.** With no UI and no override, `ask` behaves as "
                "skip. Every ordering row below is therefore observed through a headless "
                "driver, which is exactly the situation the chapter warns about.",
                "**`remember` is declared and not tested**, by the chapter's own account.",
                "**No isolation method is evaluated.** `metadata/08-chapter.yaml` records "
                "that evaluating a container, VM or credential proxy is out of scope — that "
                "is `docs/containerization.md` and chapter 42.",
                "**The `sessionDir` setting is read before trust resolves**, so it is the one "
                "thing a declined trust does not undo. That is chapter 5's evidence, run "
                "there.",
            ],
        ),
    ),
    *setup_cells(
        8,
        mode="**Run** — Pi's own trust predicates against real directories, and the shipped "
        "binary in print mode for the decision order.",
        scope="`in_process_runtime` for the predicates and the store; `shipped_binary` for the "
        "decision order.",
    ),
    (
        "md",
        """## Experiment 1: which paths are gated

`hasTrustRequiringProjectResources` is Pi's own predicate, pointed at real temporary
directories each containing exactly one candidate path. The last two rows are the
exceptions that matter: a bare `.pi/`, and context files.""",
    ),
    (
        "code",
        'TRUST = pinb.driver_source("ch08-trust.ts")\n'
        'trust = pinb.driver(TRUST, label="ch08-trust", timeout=300)\n'
        'print(pinb.md_table(\n'
        '    ["project path", "requires a decision?"],\n'
        '    [[t["path"], "yes" if t["requiresDecision"] else "no"] for t in trust["triggers"]]\n'
        '    + [[trust["withContextFiles"]["path"] + "  (the exception)", "yes" if trust["withContextFiles"]["requiresDecision"] else "no"],\n'
        '       [trust["ancestor"]["path"], "yes" if trust["ancestor"]["requiresDecision"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "gated = {t[\"path\"] for t in trust[\"triggers\"] if t[\"requiresDecision\"]}\n"
        "ungated = {t[\"path\"] for t in trust[\"triggers\"] if not t[\"requiresDecision\"]}\n"
        "expected_gated = {\n"
        '    ".pi/settings.json", ".pi/mcp.json", ".pi/extensions/example.ts",\n'
        '    ".pi/skills/example/SKILL.md", ".pi/prompts/example.md", ".pi/themes/example.json",\n'
        '    ".pi/SYSTEM.md", ".pi/APPEND_SYSTEM.md", ".agents/skills/example/SKILL.md",\n'
        "}\n"
        "\n"
        "pinb.show_checks([\n"
        '    pinb.check("exactly the nine documented paths are gated",\n'
        '               gated == expected_gated, f"{len(gated)} gated"),\n'
        '    pinb.check("a bare .pi/ directory needs no decision", ".pi/" in ungated, str(sorted(ungated))),\n'
        '    pinb.check("a context file needs no decision", "AGENTS.md" in ungated, "AGENTS.md is ungated"),\n'
        '    pinb.check("AGENTS.md + CLAUDE.md together still need no decision",\n'
        '               not trust["withContextFiles"]["requiresDecision"], "no"),\n'
        '    pinb.check("a trigger in an ancestor counts when you start below it",\n'
        '               trust["ancestor"]["requiresDecision"], "yes"),\n'
        "])",
    ),
    (
        "md",
        """## Experiment 2: saved decisions are inherited, and clearing works

`trust.json` in the agent directory is the durable record. The sequence below is
three `set` calls and four reads, which is the whole inheritance rule.""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["after", "read for the repository", "read for repo/src"],\n'
        '    [["nothing saved", trust["inheritance"]["initial"], "-"],\n'
        '     ["parent set to yes", trust["inheritance"]["afterParentYes"]["repo"], trust["inheritance"]["afterParentYes"]["child"]],\n'
        '     ["child set to no", trust["inheritance"]["afterChildNo"]["repo"], trust["inheritance"]["afterChildNo"]["child"]],\n'
        '     ["parent cleared with null", trust["inheritance"]["afterCleared"]["repo"], "-"]],\n'
        "))",
    ),
    (
        "md",
        """Row three is the one to notice: the child says **no** and the parent still
says **yes**. The store resolves by walking up and taking the nearest decision, so
refusing a subdirectory does not poison its parent.

## Experiment 3: who decides, in what order

Every row is a real `pi --print` run against the shipped binary. The project
extension writes a flag file when its factory runs, which is the observable: did the
protected project resource load, yes or no.""",
    ),
    (
        "code",
        'DECISION = pinb.driver_source("ch08-decision.ts")\n'
        'order = pinb.driver(DECISION, label="ch08-decision", timeout=420)\n'
        'print(pinb.md_table(\n'
        '    ["who has an opinion", "the project extension loaded?"],\n'
        '    [[r["who"], "YES" if r["loaded"] else "no"] for r in order],\n'
        "))",
    ),
    (
        "code",
        'loaded = {r["who"]: r["loaded"] for r in order}\n'
        "\n"
        "pinb.show_checks([\n"
        '    pinb.check("nothing configured: print mode cannot ask, so it skips",\n'
        '               loaded["nothing at all"] is False, "not loaded"),\n'
        '    pinb.check("--approve loads, --no-approve does not",\n'
        '               loaded["--approve"] is True and loaded["--no-approve"] is False, "flag decides first"),\n'
        '    pinb.check("defaultProjectTrust: always loads; ask and never skip",\n'
        '               loaded["defaultProjectTrust: always"] is True\n'
        '               and not loaded["defaultProjectTrust: ask"]\n'
        '               and not loaded["defaultProjectTrust: never"], "setting decides last"),\n'
        '    pinb.check("a saved decision beats the default setting",\n'
        '               loaded["saved yes + defaultProjectTrust: never"] is True, "saved yes wins over never"),\n'
        '    pinb.check("a command-line flag beats a saved decision",\n'
        '               loaded["saved no + --approve"] is True, "--approve over a saved no"),\n'
        '    pinb.check("an extension handler beats a saved decision",\n'
        '               loaded["extension says yes + saved no"] is True\n'
        '               and loaded["extension says no + saved yes"] is False, "handler decides before the store"),\n'
        '    pinb.check("an extension that answers undecided hands the decision on",\n'
        '               loaded["extension says undecided + saved yes"] is True, "the saved yes applied"),\n'
        '    pinb.check("the flag still outranks an extension",\n'
        '               loaded["extension says yes + --no-approve"] is False, "--no-approve wins"),\n'
        "])",
    ),
    (
        "md",
        """Read the table top to bottom and the order is forced: every source that
appears **later** in this list is contradicted by an earlier one.

```
command-line flag  >  extension project_trust handler  >  saved decision  >  defaultProjectTrust
```

That is a design choice, not an accident of implementation, and it has a
consequence worth stating: **a hostile repository cannot grant itself trust**, and
neither can a project file — `defaultProjectTrust` only reads from the agent
directory.

### The ungated channel

The exception in experiment 1 is the part to carry forward. `AGENTS.md` and
`CLAUDE.md` load regardless of trust. Declining a project stops its extensions,
prompts, skills, themes and system-prompt files; it does **not** stop its
instructions from being read into the model's context. `-nc` / `--no-context-files`
is the only documented way to remove that channel, and it is a per-run choice.""",
    ),
    *canonical_tests(
        8,
        ["ch08-trust/trust.test.ts", "ch08-trust/decision.test.ts"],
        what="The chapter's canonical evidence",
        show="AGENTS.md",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** With **no** flag, **no** extension and **no** saved decision, in
`--print` mode: does a project `AGENTS.md` load? Does a project `.pi/settings.json`?

**Then change one input.** `ORDER` below adds one row to the same matrix: a saved
**no** plus an extension that answers `undecided`. Which way should it fall?

**Predict the boundary.** What would an extension have to return to *not* be
consulted at all? (The chapter records that returning the bare string `"yes"` is
silently ignored, because the handler returns an object.)""",
    ),
    (
        "code",
        "expected = {\n"
        '    "undecided + saved no": False,\n'
        '    "flag beats everything": False,\n'
        "}\n"
        'print("predicted:")\n'
        'for k, v in expected.items():\n'
        '    print(f"  {k:26s} -> {v}")\n'
        "print()\n"
        "print(\"already observed above:\")\n"
        'print(f"  {\'undecided + saved yes\':26s} -> {loaded[\'extension says undecided + saved yes\']}")\n'
        'print(f"  {\'yes + --no-approve\':26s} -> {loaded[\'extension says yes + --no-approve\']}")\n'
        "\n"
        'assert loaded["extension says undecided + saved yes"] is True\n'
        'assert loaded["extension says yes + --no-approve"] is False\n'
        'print()\n'
        'print("held: undecided defers to the store, and the flag outranks every extension")',
    ),
    (
        "md",
        """## Interpretation

Trust is a **gate on loading**, decided in a fixed order, with exactly one ungated
channel. Three practical consequences:

1. **Decide in scripts, not in prompts.** Print mode cannot ask. `--approve` and
   `--no-approve` are the only two answers available to a batch job, and the chapter
   is explicit that `always` loads while `ask` and `never` skip there.
2. **Declining is not isolation.** It removes executable and configurable project
   material. It does not remove instructions. If that matters, turn off context
   files for the run.
3. **A remembered decision is sticky in one direction.** It can be overridden by a
   flag or a handler in every run, but it persists in `trust.json` until someone
   clears it. Chapter 42 is about what "trusted" does and does not buy you.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=8,
            mode="**Run** — Pi's trust predicate against eleven real directory layouts, "
            "`ProjectTrustStore` across four reads, and fourteen headless runs of the "
            "shipped binary.",
            scope="`in_process_runtime` plus `shipped_binary`. The provider is scripted; the "
            "gate, the store and the decision order are Pi's.",
            provenance=[
                "**Ran** `hasTrustRequiringProjectResources` on eleven temporary "
                "directories, each holding exactly one candidate path, plus an "
                "`AGENTS.md + CLAUDE.md` layout and a start-below-an-ancestor case.",
                "**Ran** four reads against one `ProjectTrustStore` across three `set` calls.",
                "**Ran** fourteen `pi --print` invocations, offline, each in a fresh "
                "temporary working directory, with the flag / saved decision / setting / "
                "extension handler varied.",
                "**Ran** `ch08-trust/trust.test.ts` and `ch08-trust/decision.test.ts`.",
                "**Read** `examples/evidence.json`, chapter 8 rows (18 claims).",
            ],
            limits=[
                "**Print mode cannot ask.** Every ordering row is therefore observed in the "
                "mode where the answer is forced. A terminal session with a person present "
                "would offer a prompt instead, which changes `ask` from skip to ask — a "
                "behaviour that cannot be exercised here.",
                "**The ungated-channel claim is structural.** The table shows that "
                "`AGENTS.md` does not require a decision; the chapter's own test "
                "(`untrusted: the project's extension and prompt template do not load, but "
                "its AGENTS.md still does`) is the evidence that it still loads, and it ran "
                "above.",
                "**`remember` was not exercised**, by the chapter's own account. No isolation "
                "method is evaluated here; that is chapter 42 and it is mostly *not run*.",
            ],
        ),
    ),
]