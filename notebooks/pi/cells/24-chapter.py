"""Chapter 24 - Branching and Forking."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Branching and Forking"
QUESTION = """After leaving a branch, what is still in the tree, what stops reaching the
model, and what does a fork write?

The chapter's point: `/tree` moves within the session file, `/fork` creates a new
session from an earlier user message, `/clone` copies the active branch into a
new session. The tree stores everything; the active branch is what reaches the
model. A branch you did not choose changes what the model sees."""

CELLS = [
    ("md", heading(24, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "The session is an **append-only tree of entries with stable ids**. Branching creates new children from an earlier entry; the current position is the leaf.",
                "`/tree` on a **user message** returns its text to the editor and moves the leaf to the message's parent (new sibling branch). On an **assistant response**, it continues after that entry with an empty editor.",
                "Submitting an edited prompt creates a **sibling**: two message entries under the same parent, in one session file.",
                "The **abandoned branch stays** in the tree — it is not deleted. A `branch_summary` entry can be appended to the new branch, recording the `fromId` of the abandoned leaf.",
                "`/fork` creates a **new session file** from an earlier user message — the abandoned path does NOT carry over. The response includes the original prompt text for the editor.",
                "`/clone` copies the **active branch only** into a new session file — abandoned branches do not come with it.",
                "`get_entries` returns **all entries** (including pre-compaction history and abandoned branches); `get_messages` returns only the active branch.",
                "Branch-relative state: `ContextEditEntry` edits are branch-relative — navigating to before the edit reveals the original. Extensions must rebuild state from `getBranch()`, not every file entry.",
                "Labels are bookmarks on entries and appear in `get_tree`.",
            ],
            [
                "**Branch summary quality not evaluated** — the test checks structure, not content.",
                "**The `branchSummary.skipPrompt` setting** is documented, not run.",
                "**`session_before_fork` extension cancellation** is documented, not run.",
                "**RPC `fork`/`clone` over shipped binary** is tested but the extension cancellation path is not exercised.",
            ],
        ),
    ),
    *setup_cells(
        24,
        mode="**Run** — real sessions with the shared persisted history, branching in-process and via RPC against the shipped binary.",
        scope="`in_process_runtime` + `shipped_binary`. The tree mechanics and navigation are Pi's.",
    ),
    (
        "md",
        """## Baseline: the shared history""",
    ),
    (
        "code",
        'BRANCH = pinb.driver_source("ch24-branching.ts")\n'
        'branch = pinb.driver(BRANCH, label="ch24-branching", timeout=300)\n'
        'print(pinb.md_table(\n'
        '    ["operation", "result"],\n'
        '    [["tree on user message: leaf moved to parent", branch["treeUser"]["leafMovedToParent"]],\n'
        '     ["tree on user message: sibling created after prompt", branch["siblingCreated"]["siblingsCount"] == 2],\n'
        '     ["tree on assistant: empty editor", branch["treeAssistant"]["editorEmpty"]],\n'
        '     ["fork from user message: new session", branch["fork"]["newSessionCreated"]],\n'
        '     ["fork response has prompt text", branch["fork"]["hasPromptText"]],\n'
        '     ["clone: new session", branch["clone"]["newSessionCreated"]],\n'
        '     ["clone copies active branch only", branch["clone"]["activeBranchOnly"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("tree on user message: leaf moved to parent",\n'
        '               branch["treeUser"]["leafMovedToParent"],\n'
        '               "leaf moved to parent"),\n'
        '    pinb.check("tree on user message: sibling created after prompt",\n'
        '               branch["siblingCreated"]["siblingsCount"] == 2,\n'
        '               "sibling under same parent"),\n'
        '    pinb.check("tree on assistant: continues after with empty editor",\n'
        '               branch["treeAssistant"]["editorEmpty"], "empty editor"),\n'
        '    pinb.check("fork creates new session file", branch["fork"]["newSessionCreated"], "new session"),\n'
        '    pinb.check("fork response includes original prompt text", branch["fork"]["hasPromptText"], "text for editor"),\n'
        '    pinb.check("clone creates new session", branch["clone"]["newSessionCreated"], "new session"),\n'
        '    pinb.check("clone copies active branch only (abandoned branches not included)", branch["clone"]["activeBranchOnly"], "active only"),\n'
        "])",
    ),
    (
        "md",
        """## get_entries vs get_messages""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["call", "includes abandoned branches?"],\n'
        '    [["get_entries", "yes" if branch["entries"]["includesAbandoned"] else "no"],\n'
        '     ["get_messages", "no" if not branch["messages"]["includesAbandoned"] else "yes"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("get_entries includes abandoned branches", branch["entries"]["includesAbandoned"], "all entries"),\n'
        '    pinb.check("get_messages is active branch only", not branch["messages"]["includesAbandoned"], "active only"),\n'
        '    pinb.check("get_entries supports since cursor", branch["entries"]["sinceWorks"], "durable cursor"),\n'
        "])",
    ),
    (
        "md",
        """## Branch-relative context_edit""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["check", "result"],\n'
        '    [["edit on branch 1 visible on branch 1", "yes" if branch["edits"]["visibleOnBranch1"] else "no"],\n'
        '     ["edit on branch 1 NOT visible on branch 2", "no" if not branch["edits"]["visibleOnBranch2"] else "yes"],\n'
        '     ["navigate to before edit restores original", "yes" if branch["edits"]["restoredOnNavigate"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("context_edit is branch-relative", branch["edits"]["visibleOnBranch1"] and not branch["edits"]["visibleOnBranch2"], "branch-relative"),\n'
        '    pinb.check("navigating before edit restores original", branch["edits"]["restoredOnNavigate"], "original restored"),\n'
        "])",
    ),
    (
        "md",
        """## Labels""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["check", "result"],\n'
        '    [["get_tree reports labels", "yes" if branch["labels"]["inTree"] else "no"],\n'
        '     ["labelTimestamp present", "yes" if branch["labels"]["hasTimestamp"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("labels appear in get_tree", branch["labels"]["inTree"], "labeled"),\n'
        '    pinb.check("labelTimestamp recorded", branch["labels"]["hasTimestamp"], "timestamped"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

All tests from the chapter's test file.""",
    ),
    *canonical_tests(
        24,
        "ch24-branching/branching.test.ts",
        what="The chapter's canonical evidence",
        show="branch",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** What happens if you `/fork` from a point that is already on an
abandoned branch? Does the new session include the branch you were on, or the
original active branch?

**Then change one input.** The `branchSummary.reserveTokens` default is 16384.
What happens if you set it to 0 — does the summary still generate?

**Predict the boundary.** `get_entries` with a `since` cursor that matches no
entry id returns `success: false`. What does the client do with that — crash,
retry from start, or show an error?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. fork from abandoned branch: new session from that point, original active branch not included.")\n'
        'print("  2. reserveTokens=0: summary still generated (budget applies to input, not output).")\n'
        'print("  3. invalid since: success: false — client should handle gracefully, not crash.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  tree user: leafMoved={branch[\"treeUser\"][\"leafMovedToParent\"]}")\n'
        'print(f"  tree assistant: empty editor={branch[\"treeAssistant\"][\"editorEmpty\"]}")\n'
        'print(f"  fork: new session={branch[\"fork\"][\"newSessionCreated\"]}, prompt text={branch[\"fork\"][\"hasPromptText\"]}")\n'
        'print(f"  clone: new session={branch[\"clone\"][\"newSessionCreated\"]}, active only={branch[\"clone\"][\"activeBranchOnly\"]}")\n'
        'print(f"  entries: abandoned={branch[\"entries\"][\"includesAbandoned\"]}")\n'
        'print(f"  messages: abandoned={branch[\"messages\"][\"includesAbandoned\"]}")\n'
        'print(f"  edits: branch-relative={branch[\"edits\"][\"visibleOnBranch1\"] and not branch[\"edits\"][\"visibleOnBranch2\"]}")\n'
        "print()\n"
        'assert branch["treeUser"]["leafMovedToParent"]\n'
        'assert branch["fork"]["newSessionCreated"]\n'
        'assert branch["fork"]["hasPromptText"]\n'
        'assert branch["clone"]["activeBranchOnly"]\n'
        'assert branch["entries"]["includesAbandoned"] and not branch["messages"]["includesAbandoned"]\n'
        'print("held: tree=sibling in same file, fork=new session from user msg, clone=active branch copy; entries=all, messages=active")',
    ),
    (
        "md",
        """## Interpretation

Branching is three operations at three scales, and the chapter shows the
boundaries:

| Operation | Scale | What it does | The boundary |
|---|---|---|---|
| `/tree` | **Entry** | New sibling under same parent in same file | User msg → edit original; assistant → empty editor after |
| `/fork` | **Session** | New session file from a user message | **Original prompt text returned** for editor; no summary from abandoned path |
| `/clone` | **Session** | New session file from current leaf | **Active branch only** — abandoned branches dropped |

| Read API | What it returns | Use for |
|---|---|---|
| `get_messages` | Active branch only | Normal session display |
| `get_entries` | **All entries** (including abandoned) | Durable cursor, full history |
| `get_tree` | Tree shape with labels | Navigation UI |

State is branch-relative:
* `context_edit` — navigating before edit restores original
* Extension state must be rebuilt from `getBranch()` on `session_start`
* Labels are bookmarks on entries, survive branch changes

Practical rules:
1. **`/tree` for related alternatives** — they stay together, can be summarized forward.
2. **`/fork` for separate work** — new session, no summary carried over.
3. **`/clone` for checkpointing current state** — copy active branch, abandon the rest.
4. **Use `get_entries` for session viewers** — `get_messages` misses abandoned branches.
5. **Rebuild extension state from `getBranch()`** — not from every file entry.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=24,
            mode="**Run** — real sessions with the shared persisted history, branching in-process and via RPC against the shipped binary.",
            scope="`in_process_runtime` + `shipped_binary`. The tree mechanics and navigation are Pi's.",
            provenance=[
                "**Ran** `drivers/ch24-branching.ts`: real sessions branching the shared history in-process, plus `fork`/`clone` over RPC against shipped binary.",
                "**Ran** `ch24-branching/branching.test.ts` (10 tests).",
                "**Read** `examples/evidence.json`, chapter 24 rows (10 claims).",
            ],
            limits=[
                "**Branch summary quality not evaluated** — the test checks structure, not content.",
                "**The `branchSummary.skipPrompt` setting** is documented, not run.",
                "**`session_before_fork` extension cancellation** is documented, not run.",
            ],
        ),
    ),
]