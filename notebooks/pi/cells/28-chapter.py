"""Chapter 28 - Context Admission Is Application Policy."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Context Admission Is Application Policy"
QUESTION = """Starting in `repo/src/billing`, which `AGENTS.md` files are discovered and
admitted — and does an override reach outside its directory?

The chapter's point: discovery walks the **working directory and its parents**,
plus the agent directory. Siblings are never discovered. An `AGENTS.override.md`
replaces the `AGENTS.md` beside it and **only that one**. And a host can drop or
add files before they reach the model — admission is application policy."""

CELLS = [
    ("md", heading(28, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "Discovery walks the **agent directory**, the **working directory** and its **parents** — a sibling directory is never discovered.",
                "An `AGENTS.override.md` **replaces the `AGENTS.md` beside it**, and only that one — it does not suppress other directories.",
                "The host **owns admission**: an `agentsFilesOverride` can drop a file before it reaches the model, or add a virtual one.",
                "The merge order of several context files at once is **not specified** by Pi (`ch28-lim1`).",
                "Whether the **model received** the files was not run (`ch28-lim3`) — this is the loader's admitted list, not a provider request.",
            ],
            [
                "**The merge order of several context files at once is not specified** (`ch28-lim1`).",
                "**Whether the model received the files** was not run (`ch28-lim3`) — this reads the loader, not the provider.",
                "**Admission is application policy**, not a Pi guarantee — the `agentsFilesOverride` is a hook the host uses.",
            ],
        ),
    ),
    *setup_cells(
        28,
        mode="**Run** — `DefaultResourceLoader` built directly over a real fixture tree on disk.",
        scope="`in_process_runtime`. The discovery rules and the override hook are Pi's.",
    ),
    (
        "md",
        """## Baseline: what is discovered from `repo/src/billing`""",
    ),
    (
        "code",
        'ADM = pinb.driver_source("ch28-admission.ts")\n'
        'adm = pinb.driver(ADM, label="ch28-admission", timeout=180)\n'
        'print("Admitted files:")\n'
        'for f in adm["discovered"]["list"]:\n'
        '    print("  -", f)\n'
        'print()\n'
        'pinb.show_checks([\n'
        '    pinb.check("the agent directory applies everywhere",\n'
        '               adm["discovered"]["includesUser"], "user rules present"),\n'
        '    pinb.check("a parent directory is inherited downward",\n'
        '               adm["discovered"]["includesRepo"], "repo rules present"),\n'
        '    pinb.check("a sibling directory is never discovered",\n'
        '               not adm["discovered"]["includesDocsSibling"], "docs rules absent"),\n'
        "])",
    ),
    (
        "md",
        """## An override replaces the file beside it, and only that one""",
    ),
    (
        "code",
        'print("Admitted files with the override:")\n'
        'for f in adm["override"]["list"]:\n'
        '    print("  -", f)\n'
        'print()\n'
        'pinb.show_checks([\n'
        '    pinb.check("the override is admitted",\n'
        '               adm["override"]["hasOverride"], "billing override present"),\n'
        '    pinb.check("the AGENTS.md beside it is replaced",\n'
        '               not adm["override"]["hasReplaced"], "billing rules (replaced) absent"),\n'
        '    pinb.check("an override does not suppress other directories",\n'
        '               adm["override"]["hasRepoStill"], "repo rules still present"),\n'
        "])",
    ),
    (
        "md",
        """## The host owns admission: drop and add""",
    ),
    (
        "code",
        'print("Admitted files after the host override:")\n'
        'for f in adm["host"]["list"]:\n'
        '    print("  -", f)\n'
        'print()\n'
        'pinb.show_checks([\n'
        '    pinb.check("the host can drop a file before it reaches the model",\n'
        '               not adm["host"]["hasUserRules"], "user rules dropped"),\n'
        '    pinb.check("the host can add a virtual file",\n'
        '               adm["host"]["hasVirtual"], "host policy added"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

All three admission tests.""",
    ),
    *canonical_tests(
        28,
        "ch28-admission/admission.test.ts",
        what="The chapter's canonical evidence",
        show="admitted",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** Starting in `repo/docs` instead of `repo/src/billing`, which
files would be discovered? Does `billing`'s override come along?

**Then change one input.** Move the override to `repo/AGENTS.override.md` (the
repository root). What replaces what?

**Predict the boundary.** The chapter says "the merge order of several context
files at once is not specified." If the repo root and the project both define a
rule with the same name, which wins?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. From repo/docs: repo rules + user rules; billing is a sibling, not discovered.")\n'
        'print("  2. Override at repo root: replaces repo/AGENTS.md, not billing/.")\n'
        'print("  3. Same-name rule: the merge order is unspecified - do not rely on it.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'user = adm["discovered"]["includesUser"]\n'
        'repo = adm["discovered"]["includesRepo"]\n'
        'docs = adm["discovered"]["includesDocsSibling"]\n'
        'print(f"  discovered: user={user}, repo={repo}, docs sibling={docs}")\n'
        'print(f"  override: present={adm[\'override\'][\'hasOverride\']}, replaced={adm[\'override\'][\'hasReplaced\']}, repo still={adm[\'override\'][\'hasRepoStill\']}")\n'
        'print(f"  host: user dropped={not adm[\'host\'][\'hasUserRules\']}, virtual added={adm[\'host\'][\'hasVirtual\']}")\n'
        "print()\n"
        'assert adm["discovered"]["includesUser"] and adm["discovered"]["includesRepo"]\n'
        'assert not adm["discovered"]["includesDocsSibling"]\n'
        'assert adm["override"]["hasOverride"] and not adm["override"]["hasReplaced"] and adm["override"]["hasRepoStill"]\n'
        'assert not adm["host"]["hasUserRules"] and adm["host"]["hasVirtual"]\n'
        'print("held: discovery walks up, not sideways; an override replaces its neighbour only; the host can drop and add")',
    ),
    (
        "md",
        """## Interpretation

Context admission has three layers, and the chapter shows the boundaries:

| Layer | What it decides | The boundary |
|---|---|---|
| **Discovery** | Which files are candidates | Working dir + parents + agent dir; **not siblings** |
| **Admission** | Which candidates load | An `AGENTS.override.md` replaces its neighbour **only** |
| **Host override** | What the model finally sees | `agentsFilesOverride` can **drop or add** files |

Practical rules:
1. **Context comes from the path, not the project** — a file is loaded because it is on the path from the working directory to the root.
2. **An override is local** — it replaces one file, not a directory's worth.
3. **The host can filter** — `agentsFilesOverride` is where an application enforces its own policy.
4. **Merge order is unspecified** — do not depend on which of two same-name rules wins.
5. **This is admission, not delivery** — whether the model received the files is a separate question (chapter 5's stored-vs-sent).""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=28,
            mode="**Run** — `DefaultResourceLoader` built directly over a real fixture tree on disk.",
            scope="`in_process_runtime`. The discovery rules and the override hook are Pi's.",
            provenance=[
                "**Ran** `drivers/ch28-admission.ts`: three real `DefaultResourceLoader` builds over a fixture tree (discovery, override locality, host admission).",
                "**Ran** `ch28-admission/admission.test.ts` (3 tests).",
                "**Read** `examples/evidence.json`, chapter 28 rows (3 claims).",
            ],
            limits=[
                "**The merge order of several context files at once is not specified** (`ch28-lim1`).",
                "**Whether the model received the files** was not run (`ch28-lim3`) — this reads the loader, not the provider.",
            ],
        ),
    ),
]