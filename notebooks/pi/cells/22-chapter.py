"""Chapter 22 - Packages: Shipping an Agent."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Packages: Shipping an Agent"
QUESTION = """Does `pi install ./pkg` record a relative path and copy nothing — and when
is the host-dependency warning emitted?

The chapter's point: a package is the distribution unit for extensions, skills,
prompts and themes. `pi install` records a relative path in settings.json and
copies nothing. Filters narrow what loads; they cannot expose what the package
did not declare. Host packages belong in `peerDependencies` with a `*` range,
not `dependencies`."""

CELLS = [
    ("md", heading(22, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "`pi install ./pkg` records a **relative path** from the agent directory in `settings.json` — nothing is copied into the agent directory.",
                "`pi list` shows the installed package under 'User packages:'.",
                "A package's prompt template and extension load from conventional directories with no manifest needed.",
                "`pi -e` loads a package for one invocation and **writes nothing to settings**.",
                "`pi remove` removes the package from settings and it no longer loads.",
                "The **object form** in settings filters a package: `prompts: []` excludes prompts but leaves extensions and skills.",
                "A filter **narrows** what the package declares; it **cannot expose** something the package did not declare in its manifest.",
                "The **same package listed twice** (as string and object) loads once — identity is the resolved path.",
                "An explicit `pi` manifest in `package.json` **replaces** conventional discovery — only declared resources load.",
                "`--local` writes to the project's `.pi/settings.json`, which loads **only after the project is trusted**.",
                "A host-provided package in `dependencies` draws a **warning**; in `peerDependencies` with a `*` range it does not.",
            ],
            [
                "**No npm or git source** — every source is a local path and every run is offline; no published package is exercised end to end (`ch22-lim1`).",
                "**No skill theme loading** is demonstrated — the tests focus on prompts and extensions.",
                "**The `pi` manifest's `mcpServers` field** is not exercised here.",
                "**The package gallery** (`pi.image`, `pi.video`) is documented, not run.",
            ],
        ),
    ),
    *setup_cells(
        22,
        mode="**Run** — the shipped binary (`pi`) offline: `install`, `list`, `remove`, `-e`, `--local` under `--approve`/`--no-approve`.",
        scope="`shipped_binary`. The package mechanics are the real Pi CLI.",
    ),
    (
        "md",
        """## Baseline: what `pi install` writes, and what it does not do""",
    ),
    (
        "code",
        'PKG = pinb.driver_source("ch22-install.ts")\n'
        'pkg = pinb.driver(PKG, label="ch22-install", timeout=300)\n'
        'print(pinb.md_table(\n'
        '    ["check", "result"],\n'
        '    [["exit code", "0" if pkg["install"]["exit"] == 0 else "non-zero"],\n'
        '     ["entry is string", "yes" if pkg["install"]["entryIsString"] else "no"],\n'
        '     ["source recorded", pkg["install"]["source"]],\n'
        '     ["is absolute path", "yes" if pkg["install"]["isAbsolute"] else "no"],\n'
        '     ["relative to settings", pkg["install"]["relativeToSettings"]],\n'
        '     ["resolves to package dir", "yes" if pkg["install"]["resolvesToPackage"] else "no"],\n'
        '     ["package still on disk", "yes" if pkg["install"]["packageStillOnDisk"] else "no"],\n'
        '     ["copied into agent dir", "yes" if pkg["install"]["copiedIntoAgentDir"] else "no"],\n'
        '     ["agent dir entries", ", ".join(pkg["install"]["agentDirEntries"])]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("install exits 0", pkg["install"]["exit"] == 0, "exit 0"),\n'
        '    pinb.check("entry is a relative path from agent dir", pkg["install"]["relativeToSettings"] == "../my-pkg", "correct relative path"),\n'
        '    pinb.check("resolves back to the package directory", pkg["install"]["resolvesToPackage"], "resolves correctly"),\n'
        '    pinb.check("package NOT copied into agent dir", not pkg["install"]["copiedIntoAgentDir"], "no copy"),\n'
        '    pinb.check("package still on disk at original location", pkg["install"]["packageStillOnDisk"], "original intact"),\n'
        "])",
    ),
    (
        "md",
        """## Listing and one-shot invocation""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["check", "result"],\n'
        '    [["list shows package", "yes" if pkg["list"]["showsPackage"] else "no"],\n'
        '     ["list has User packages section", "yes" if pkg["list"]["section"] else "no"],\n'
        '     ["one-shot expands template", "yes" if pkg["oneShot"]["expanded"] else "no"],\n'
        '     ["one-shot writes to settings", "yes" if pkg["oneShot"]["settingsWritten"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("pi list shows the package", pkg["list"]["showsPackage"], "listed"),\n'
        '    pinb.check("pi -e expands the template", pkg["oneShot"]["expanded"], "expanded"),\n'
        '    pinb.check("pi -e does NOT write to settings", not pkg["oneShot"]["settingsWritten"], "no settings write"),\n'
        "])",
    ),
    (
        "md",
        """## Removal""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["check", "result"],\n'
        '    [["remove exits 0", "yes" if pkg["remove"]["exit"] == 0 else "no"],\n'
        '     ["package no longer listed", "no" if pkg["remove"]["stillListed"] else "yes"],\n'
        '     ["template no longer expands", "no" if pkg["remove"]["stillExpands"] else "yes"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("remove exits 0", pkg["remove"]["exit"] == 0, "exit 0"),\n'
        '    pinb.check("package removed from list", not pkg["remove"]["stillListed"], "unlisted"),\n'
        '    pinb.check("template no longer expands after remove", not pkg["remove"]["stillExpands"], "unloaded"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

All 11 tests from the chapter's test file.""",
    ),
    *canonical_tests(
        22,
        "ch22-packages/packages.test.ts",
        what="The chapter's canonical evidence",
        show="package",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** What happens if you `pi install` the same package twice? Does
it appear twice in `pi list`?

**Then change one input.** The object form `{ source: "...", prompts: [] }`
filters out prompts. What does `{ source: "...", extensions: [] }` do?

**Predict the boundary.** The chapter says "filters narrow what the package
declares; they cannot expose what the package did not declare." What if the
package declares `prompts: ["./elsewhere/*.md"]` and you filter
`prompts: ["prompts/greet.md"]` — does the filter expose the undeclared
`prompts/greet.md`?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. Install twice: appears once in list (settings.json deduplicates).")\n'
        'print("  2. extensions: [] filters out extensions but leaves prompts/skills.")\n'
        'print("  3. Filter cannot expose undeclared: prompts/greet.md stays hidden.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  install: relative={pkg[\"install\"][\"relativeToSettings\"]}, copied={pkg[\"install\"][\"copiedIntoAgentDir\"]}")\n'
        'print(f"  list: shows={pkg[\"list\"][\"showsPackage\"]}")\n'
        'print(f"  one-shot: expanded={pkg[\"oneShot\"][\"expanded\"]}, settings_written={pkg[\"oneShot\"][\"settingsWritten\"]}")\n'
        'print(f"  remove: unlisted={not pkg[\"remove\"][\"stillListed\"]}, unexpands={not pkg[\"remove\"][\"stillExpands\"]}")\n'
        "print()\n"
        'assert not pkg["install"]["copiedIntoAgentDir"]\n'
        'assert pkg["install"]["relativeToSettings"] == "../my-pkg"\n'
        'assert pkg["list"]["showsPackage"]\n'
        'assert pkg["oneShot"]["expanded"] and not pkg["oneShot"]["settingsWritten"]\n'
        'assert not pkg["remove"]["stillListed"] and not pkg["remove"]["stillExpands"]\n'
        'print("held: install records relative path, copies nothing; remove unloads; -e is one-shot")',
    ),
    (
        "md",
        """## Interpretation

A Pi package is the distribution unit for your agent customizations. The key
mechanics and their boundaries:

| Mechanism | What it does | The boundary |
|---|---|---|
| `pi install ./pkg` | Records relative path in `settings.json` | **Copies nothing** — the package stays where it is |
| `pi list` | Shows installed packages | User packages vs project packages |
| `pi -e ./pkg` | One-shot load | **Writes nothing to settings** |
| `pi remove` | Removes from settings | Package no longer loads |
| Settings object form | Filters by resource type | `prompts: []` excludes prompts; `skills: ["a"]` keeps only `a` |
| Package `pi` manifest | Declares resources explicitly | **Replaces** conventional discovery — undeclared resources don't load |
| `pi install --local` | Writes to `.pi/settings.json` | **Requires trust** — project must be approved |

The dependency rule:
* `dependencies: { "@earendil-works/pi-ai": "*" }` → **warning** (host provides it)
* `peerDependencies: { "@earendil-works/pi-ai": "*" }` → **no warning**

The filter rule:
* Filters **narrow** what the package declares
* Filters **cannot expose** what the package did not declare
* Identity is the **resolved path** — same package twice = loads once

Practical rules:
1. **Use relative local paths** — `pi install ./my-pkg` records `../my-pkg`, works across machines.
2. **Don't bundle host packages** — declare them in `peerDependencies` with `*`.
3. **Use the object form to filter** — keep what you want, exclude what you don't.
4. **`--local` is for project-specific packages** — they require trust approval.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=22,
            mode="**Run** — the shipped binary (`pi`) offline: `install`, `list`, `remove`, `-e`, `--local` under `--approve`/`--no-approve`.",
            scope="`shipped_binary`. The package mechanics are the real Pi CLI.",
            provenance=[
                "**Ran** `drivers/ch22-install.ts`: real package directory installed with shipped binary.",
                "**Ran** `drivers/ch22-scope.ts`: `--local` trust gating and identity deduplication.",
                "**Ran** `drivers/ch22-depends.ts`: dependency warning and filter narrowing/exposure rules.",
                "**Ran** `ch22-packages/packages.test.ts` (11 tests).",
                "**Read** `examples/evidence.json`, chapter 22 rows (11 claims).",
            ],
            limits=[
                "**No npm or git source** — every source is a local path and every run is offline; no published package is exercised end to end (`ch22-lim1`).",
                "**No skill theme loading** is demonstrated — the tests focus on prompts and extensions.",
                "**The `pi` manifest's `mcpServers` field** is not exercised here.",
            ],
        ),
    ),
]