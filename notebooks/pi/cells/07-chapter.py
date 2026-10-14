"""Chapter 07 - Settings and Where Configuration Comes From."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Settings and Where Configuration Comes From"
QUESTION = """Two layers, one `settings.json` each: a scalar in your agent directory and
one in the project's `.pi`. **Which value wins, and which list wins?**

The answer differs by kind, and the difference is the chapter: scalars replace,
resource lists are merged — with a filter that only bites in the file it was
written in."""

CELLS = [
    ("md", heading(7, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "A scalar the project sets **wins**; a nested key the project omits still "
                "comes from the user file. Resolution is per key, not per object.",
                "`defaultTools` **amends** when every project entry is `+name` / `-name` and "
                "**replaces** outright when any entry is a plain name. Within one list, "
                "plain names form the selection and `+`/`-` apply in order.",
                "An **untrusted project's settings file is not read at all** — and granting "
                "trust later makes the project layer apply, with no restart.",
                "`defaultProjectTrust` cannot come from a project file. It is an "
                "agent-directory setting, and the getter still returns `ask`.",
            ],
            [
                "**The getter is not the loader.** `getSkillPaths()` returns one scope's "
                "list; the union happens when resources load. Chapter 6's notebook shows the "
                "same boundary from the tool side.",
                "**Nothing about every default.** `metadata/07-chapter.yaml` records that "
                "the chapter does not enumerate every setting, nor define resolution when "
                "two layers set the same key to different *types*.",
                "**Environment variables and command-line flags are documented per setting**, "
                "not as layers. Only the `--session-dir` / env / `sessionDir` precedence is "
                "exercised here, and that is chapter 5's evidence.",
            ],
        ),
    ),
    *setup_cells(
        7,
        mode="**Run** — Pi's own `SettingsManager` over real settings files, plus the "
        "chapter's own tests.",
        scope="`in_process_runtime`. No session, no model, no network: this is configuration.",
    ),
    (
        "md",
        """## Experiment 1: scalars replace, keys are independent

The user file sets two compaction keys; the project file sets one of them. The
resolved object answers both questions at once: which file won, and what happened
to the key nobody overrode.""",
    ),
    (
        "code",
        'SETTINGS = pinb.driver_source("ch07-settings.ts")\n'
        'settings = pinb.driver(SETTINGS, label="ch07-settings", timeout=240)\n'
        "\n"
        'print(pinb.md_table(\n'
        '    ["user 1000 / project 2000", "resolved reserveTokens", "resolved keepRecentTokens"],\n'
        '    [["compaction", settings["scalars"]["bothSet"]["reserveTokens"], settings["scalars"]["bothSet"]["keepRecentTokens"]]],\n'
        "))\n"
        'print()\n'
        'trust = settings["scalars"]["projectTrustGrantedLater"]\n'
        'print(pinb.md_table(\n'
        '    ["project trust", "resolved reserveTokens"],\n'
        '    [["untrusted (project file not read)", trust["before"]["reserveTokens"]],\n'
        '     ["trusted afterwards, same object", trust["after"]["reserveTokens"]]],\n'
        "))",
    ),
    (
        "code",
        's = settings["scalars"]\n'
        "\n"
        "pinb.show_checks([\n"
        '    pinb.check("a scalar the project sets wins",\n'
        '               s["bothSet"]["reserveTokens"] == 2000, str(s["bothSet"]["reserveTokens"])),\n'
        '    pinb.check("a nested key the project omits still comes from the user file",\n'
        '               s["bothSet"]["keepRecentTokens"] == 5000, str(s["bothSet"]["keepRecentTokens"])),\n'
        '    pinb.check("an untrusted project file is not read at all",\n'
        '               s["projectTrustGrantedLater"]["before"]["reserveTokens"] == 1000,\n'
        '               str(s["projectTrustGrantedLater"]["before"]["reserveTokens"])),\n'
        '    pinb.check("granting trust later applies the project layer, with no restart",\n'
        '               s["projectTrustGrantedLater"]["after"]["reserveTokens"] == 2000,\n'
        '               str(s["projectTrustGrantedLater"]["after"]["reserveTokens"])),\n'
        '    pinb.check("defaultProjectTrust cannot be set by a project file",\n'
        '               s["defaultProjectTrustCannotComeFromProject"]["defaultProjectTrust"] == "ask",\n'
        '               str(s["defaultProjectTrustCannotComeFromProject"]["defaultProjectTrust"])),\n'
        "])",
    ),
    (
        "md",
        """## Experiment 2: the `defaultTools` grammar

Four project lists against the same user selection. The third column is the
resolved selection; the difference between rows 1 and 2 is the entire grammar.""",
    ),
    (
        "code",
        'grammar = settings["defaultToolsGrammar"]\n'
        'USER_TOOLS = ["read", "bash", "edit", "write"]\n'
        "\n"
        "\n"
        "def entries(label: str) -> list[str]:\n"
        '    """Recover the project list from the driver\'s row label."""\n'
        "    return [e.strip() for e in label.removeprefix(\"project: \").strip(\"[]\").split(\",\") if e.strip()]\n"
        "\n"
        "\n"
        "def resolve(user: list[str], project: list[str]) -> list[str]:\n"
        '    """The documented grammar, restated for comparison."""\n'
        "    if not project:\n"
        "        return list(user)\n"
        '    if any(e[0] not in "+-" for e in project):\n'
        "        return list(project)\n"
        "    out = list(user)\n"
        "    for e in project:\n"
        "        name = e[1:]\n"
        '        if e[0] == "+":\n'
        "            if name not in out:\n"
        "                out.append(name)\n"
        "        elif name in out:\n"
        "            out.remove(name)\n"
        "    return out\n"
        "\n"
        "\n"
        'print("user selection:", USER_TOOLS)\n'
        "print()\n"
        'print(pinb.md_table(\n'
        '    ["project defaultTools", "kind", "Pi resolved", "the rule restated agrees?"],\n'
        "    [[\", \".join(entries(g[\"label\"])),\n"
        '      \"amend\" if all(e[0] in \"+-\" for e in entries(g[\"label\"])) else \"replace\",\n'
        '      \", \".join(g[\"defaultTools\"]),\n'
        '      g[\"defaultTools\"] == resolve(USER_TOOLS, entries(g[\"label\"]))]\n'
        "     for g in grammar],\n"
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("only +/- entries amend the user selection",\n'
        '               grammar[0]["defaultTools"] == USER_TOOLS + ["grep", "find", "ls"],\n'
        '               ", ".join(grammar[0]["defaultTools"])),\n'
        '    pinb.check("any plain name replaces the selection outright",\n'
        '               grammar[1]["defaultTools"] == ["read", "powershell"], ", ".join(grammar[1]["defaultTools"])),\n'
        '    pinb.check("within one list, plain names first then +/- in order",\n'
        '               grammar[2]["defaultTools"] == ["read", "grep"], ", ".join(grammar[2]["defaultTools"])),\n'
        '    pinb.check("-name removes from the user list",\n'
        '               grammar[3]["defaultTools"] == ["read", "edit", "write"], ", ".join(grammar[3]["defaultTools"])),\n'
        "])",
    ),
    (
        "md",
        """## Contrasting case: a filter that only bites where it is written

The headline failure this chapter found on 1.0.4 is not about precedence at all. A
user file listing skills with an exclusion filter removes things. **The same filter
text in the project file does not** — so a repository cannot switch off something
you configured personally, and cannot be said to have tried.

Both arms are in the chapter's own tests, and both run below.""",
    ),
    *canonical_tests(
        7,
        ["ch07-settings/settings.test.ts", "ch07-settings/union.test.ts"],
        what="The chapter's canonical evidence",
        show="exclusion",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** User selection `["read", "bash"]`, project `["-bash", "+grep"]`.
What is resolved?

**Then change one input.** `PROJECT` below feeds a second run of the same grammar.
Try `["+ls"]` (amend) and `["read"]` (replace) and watch which column changes.

**Predict the boundary.** What is the smallest project list that changes the
resolved selection at all? Is `[]` a replacement with nothing, or a no-op?""",
    ),
    (
        "code",
        'PROJECT = ["+ls"]\n'
        'CANDIDATES = [["+ls"], ["read"], ["-bash"], ["+bash"]]\n'
        "\n"
        "import json as _json\n"
        "\n"
        'print("predicted for", PROJECT, ":", resolve(USER_TOOLS, PROJECT))\n'
        "print()\n"
        "for candidate in CANDIDATES:\n"
        "    got = pinb.driver(\n"
        "        SETTINGS,\n"
        '        label="ch07-grammar",\n'
        "        timeout=240,\n"
        "        env={\"NB_PROJECT\": _json.dumps(candidate)},\n"
        '    )["defaultToolsGrammar"][0]\n'
        '    print(f"  project {str(candidate):12s} -> {got[\'defaultTools\']}")\n'
        "\n"
        'print()\n'
        'print("the smallest project list that changes the selection: any single entry.")',
    ),
    (
        "md",
        """## Interpretation

The chapter's practical rules, all of them now visible in output rather than prose:

| Kind of setting | Resolution | Consequence |
|---|---|---|
| scalar | project wins, per key | a project can retune one value and inherit the rest |
| resource list (`defaultTools`) | union, then grammar | see below |
| resource list (`skills`, extensions) | union at load time | the getter shows one scope; the loader shows both |
| `defaultProjectTrust`, `httpProxy` | agent directory only | a project cannot move these |
| `cacheWarming` | global only | neither layer |
| `sessionDir` | read before trust resolves | the one thing trust cannot undo (chapter 5) |

And the one that is a genuine trap rather than a rule: **an exclusion filter works
in the file that lists the resource.** The chapter records this as observed on
1.0.4 and not stated either way in `settings.md`.

### What this chapter does not settle

Two limits from `metadata/07-chapter.yaml` survive: not every default is
enumerated, and the resolution of two layers setting the same key to different
*types* is undefined. This notebook does not attempt either.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=7,
            mode="**Run** — `SettingsManager.create` over real files, then the chapter's own "
            "two test files.",
            scope="`in_process_runtime`. Configuration only: no session, no model, no network.",
            provenance=[
                "**Ran** `drivers/ch07-settings.ts`: eight `SettingsManager` instances over "
                "freshly written user and project `settings.json` files.",
                "**Ran** `ch07-settings/settings.test.ts` and `ch07-settings/union.test.ts`.",
                "**Read** `examples/evidence.json`, chapter 7 rows (16 claims).",
            ],
            limits=[
                "**The union is shown through `defaultTools`, which the getter resolves "
                "directly.** The skills union is a *loading* property; it is asserted by "
                "`union.test.ts`, not by this driver.",
                "**Only the keys this notebook names are resolved.** The chapter does not "
                "enumerate every default and neither does this.",
                "**No environment variable and no command-line flag is set anywhere here.** "
                "Their interaction is documented per setting; the one precedence that is "
                "exercised is the session-directory one in chapter 5.",
            ],
        ),
    ),
]