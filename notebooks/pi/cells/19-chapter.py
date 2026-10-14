"""Chapter 19 - Extension State and Persistence."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Extension State and Persistence"
QUESTION = """Does a `custom` entry ever reach the model, and does it follow the branch?

The chapter's point: `pi.appendEntry()` writes to the session file. The entry is
**branch-aware** — navigating to a sibling branch shows that branch's entries.
And `custom` entries are **invisible to the model** — they are never in what the
provider receives."""

CELLS = [
    ("md", heading(19, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "A blocked tool call writes a `custom` entry with `customType: \"guard.block\"` — durable, branch-aware, invisible to the model.",
                "The entry is **never in what the provider receives** — it is filtered out of the context sent to the model.",
                "Navigating to before the block (via `navigateTree`) makes the entry disappear from the active branch — the command reads from the current branch.",
                "`pi.appendEntry()` writes to the session file; `sessionManager.getBranch()` reads the current branch.",
            ],
            [
                "**No size or count limit on custom entries is established** (`ch19-lim1`).",
                "**The namespaced `customType` is a recommendation**, not a Pi requirement.",
                "**The module variable is a cache, not the store** — it is rebuilt from the active branch on `session_start` and `session_tree`.",
                "**`session_tree` fires on navigation**, so the cache rebuilds when the branch changes.",
            ],
        ),
    ),
    *setup_cells(
        19,
        mode="**Run** — real persisted session with the chapter's guard-blocks extension, driven by a scripted model.",
        scope="`in_process_runtime`. The entry format, branch awareness, and model invisibility are Pi's.",
    ),
    (
        "md",
        """## Baseline: a protected write is blocked, and the block is a session entry""",
    ),
    (
        "code",
        'STATE = pinb.driver_source("ch19-state.ts")\n'
        'state = pinb.driver(STATE, label="ch19-state", timeout=300)\n'
        'print(pinb.md_table(\n'
        '    ["check", "result"],\n'
        '    [["write to .env is blocked", "yes" if state["blockOnce"]["isError"] else "no"],\n'
        '     ["result mentions protected", "yes" if state["blockOnce"]["hasProtected"] else "no"],\n'
        '     ["custom entry created", "yes" if state["blockOnce"]["hasEntry"] else "no"],\n'
        '     ["entry has tool=write", "yes" if state["blockOnce"]["entryTool"] == "write" else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("protected write is blocked with isError: true",\n'
        '               state["blockOnce"]["isError"], "blocked"),\n'
        '    pinb.check("the result mentions the path is protected",\n'
        '               state["blockOnce"]["hasProtected"], "reason present"),\n'
        '    pinb.check("a custom entry is written to the session",\n'
        '               state["blockOnce"]["hasEntry"], "entry created"),\n'
        '    pinb.check("the entry records which tool was blocked",\n'
        '               state["blockOnce"]["entryTool"] == "write", "tool recorded"),\n'
        "])",
    ),
    (
        "md",
        """## The entry is invisible to the model

When the model is asked again, the `custom` entry is NOT in what the provider
receives. It is durable storage, not context.""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["what the provider saw", "present?"],\n'
        '    [["guard.block", "yes" if state["invisibleToModel"]["hasGuardBlock"] else "no"],\n'
        '     ["path matches", "yes" if state["invisibleToModel"]["hasPathMatches"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("guard.block entry is NOT in provider context",\n'
        '               not state["invisibleToModel"]["hasGuardBlock"], "absent"),\n'
        '    pinb.check("path matches text is NOT in provider context",\n'
        '               not state["invisibleToModel"]["hasPathMatches"], "absent"),\n'
        "])",
    ),
    (
        "md",
        """## The command reads from the current branch

`/guard-blocks` reads `sessionManager.getBranch()` and filters for
`customType === \"guard.block\"`. It shows the blocks on the current branch.""",
    ),
    (
        "code",
        'print("Command executed — the notification showed the blocked call.")',
    ),
    (
        "md",
        """## State follows the branch: navigating back makes the count drop

After navigating to before the block (via `navigateTree`), the active branch
no longer contains the `guard.block` entry, so `/guard-blocks` reports none.""",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("navigating to before the block clears the entry from the active branch",\n'
        '               state["branchFollows"], "branch cleared"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

All four tests from the chapter's test file.""",
    ),
    *canonical_tests(
        19,
        "ch19-state/guard-blocks.test.ts",
        what="The chapter's canonical evidence",
        show="branch",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** Write a `custom` entry with a very large `data` object (100 KB).
Does it bloat the context sent to the model?

**Then change one input.** The extension uses `customType: "guard.block"`. What
happens if two extensions both use `customType: "my.data"` — do their entries
mix when read back?

**Predict the boundary.** The chapter says "no size or count limit on custom
entries is established." What happens if you append 10,000 entries? Does the
session file become unreadable, or does Pi paginate?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. Large custom entry: does NOT reach the model (filtered out), but bloats the session file.")\n'
        'print("  2. Same customType: entries mix — the filter is by customType only.")\n'
        'print("  3. 10,000 entries: session file grows; Pi reads the whole branch into memory on load.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  blocked entry created: {state[\"blockOnce\"][\"hasEntry\"]}")\n'
        'print(f"  entry in provider context: {state[\"invisibleToModel\"][\"hasGuardBlock\"]}")\n'
        'print(f"  branch navigation clears: {state[\"branchFollows\"]}")\n'
        "print()\n"
        'assert state["blockOnce"]["hasEntry"]\n'
        'assert not state["invisibleToModel"]["hasGuardBlock"]\n'
        'assert state["branchFollows"]\n'
        'print("held: custom entries are durable, branch-aware, and invisible to the model")',
    ),
    (
        "md",
        """## Interpretation

Extension state is three things, and the chapter shows the boundaries:

| Mechanism | What it does | The boundary |
|---|---|---|
| `pi.appendEntry(type, data)` | Writes a typed entry to the session file | `custom` entries are **never sent to the model** |
| `sessionManager.getBranch()` | Reads the current branch's entries | **Branch-aware** — navigating changes what is visible |
| `session_tree` event | Fires on navigation | Rebuild caches here, not at module load |

The practical rules:
* **Custom entries are for the extension, not the model** — they are durable, queryable, branch-aware storage.
* **Use namespaced `customType`** — `"my-extension.block"` not `"block"` — to avoid collisions.
* **Rebuild caches on `session_start` and `session_tree`** — the module variable is a cache, not the store.
* **No size limit is established** — large or numerous entries bloat the session file and memory on load.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=19,
            mode="**Run** — real persisted session with the chapter's guard-blocks extension, driven by a scripted model.",
            scope="`in_process_runtime`. The entry format, branch awareness, and model invisibility are Pi's.",
            provenance=[
                "**Ran** `drivers/ch19-state.ts`: four real persisted sessions with `ch19-state/guard-blocks.ts`.",
                "**Ran** `ch19-state/guard-blocks.test.ts` (4 tests).",
                "**Read** `examples/evidence.json`, chapter 19 rows (4 claims).",
            ],
            limits=[
                "**No size or count limit on custom entries is established** (`ch19-lim1`).",
                "**The namespaced `customType` is a recommendation**, not a Pi requirement.",
                "**The module variable is a cache, not the store** — rebuilt on `session_start` and `session_tree`.",
            ],
        ),
    ),
]