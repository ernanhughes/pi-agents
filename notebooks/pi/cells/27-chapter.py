"""Chapter 27 - The Session File Format."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "The Session File Format"
QUESTION = """Is it really JSONL with a header first, and are there two timestamp formats on
one field name?

The chapter's point: the session file is JSONL — a header, then one entry per
line, linked by `id` and `parentId`. An entry carries an **ISO** timestamp; the
message inside it carries a **Unix milliseconds** number. Both are on the field
name `timestamp`, so the type tells you which one you have."""

CELLS = [
    ("md", heading(27, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "The file is **JSONL**: a session header first, then one entry per line, each linked by `id` and `parentId`.",
                "The header has **type `session`, version 3**, and **no `parentId`** — it is not part of the tree.",
                "Every entry has the base fields `id`, `parentId` and `timestamp`.",
                "For a linear conversation, each entry's `parentId` is the entry before it — the tree is a chain when nothing branches.",
                "**Two timestamp formats on one field name**: the entry's `timestamp` is ISO (`2026-…T…`), the message's `timestamp` is a Unix-milliseconds number.",
                "The chapter's own **reader runs against a real session file** and prints the session, the messages and the model.",
            ],
            [
                "**The header `version` moves** — 3 at this pin; the format is readable, not guaranteed across releases.",
                "**The projection passes and the per-entry-type visibility table** have no runtime test here — chapter 5 covers visibility.",
                "**The declaration comparison** (`assert-equal.ts`) is a compile-time check, not a runtime one.",
            ],
        ),
    ),
    *setup_cells(
        27,
        mode="**Run** + **Inspect** — a real persisted session file parsed directly, plus the chapter's own reader run as a child process and the declaration check.",
        scope="`in_process_runtime` + `declarations`. The format is Pi's; the read is direct.",
    ),
    (
        "md",
        """## Baseline: a real session file""",
    ),
    (
        "code",
        'SESS = pinb.driver_source("ch27-session-entries.ts")\n'
        'sess = pinb.driver(SESS, label="ch27-session-entries", timeout=180)\n'
        'print(pinb.md_table(\n'
        '    ["field", "value"],\n'
        '    [["header type", sess["header"]["type"]],\n'
        '     ["header version", sess["header"]["version"]],\n'
        '     ["header has parentId", "yes" if sess["header"]["hasParentId"] else "no"],\n'
        '     ["entries", sess["entries"]["count"]],\n'
        '     ["entry types", ", ".join(sess["entries"]["types"])],\n'
        '     ["all base fields present", "yes" if sess["entries"]["baseFieldsOk"] else "no"],\n'
        '     ["linear chain", "yes" if sess["entries"]["linearChain"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("the first record is the session header",\n'
        '               sess["header"]["type"] == "session", "type session"),\n'
        '    pinb.check("the header has no parentId (not part of the tree)",\n'
        '               not sess["header"]["hasParentId"], "no parentId"),\n'
        '    pinb.check("every entry has id, parentId and timestamp",\n'
        '               sess["entries"]["baseFieldsOk"], "base fields present"),\n'
        '    pinb.check("the entries form a chain for a linear conversation",\n'
        '               sess["entries"]["linearChain"], "each parent is the entry before"),\n'
        "])",
    ),
    (
        "md",
        """## Two timestamps, two formats on one field name""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["where", "format", "present?"],\n'
        '    [["entry.timestamp", "ISO string", "yes" if sess["timestamps"]["isoOnEntry"] else "no"],\n'
        '     ["entry.message.timestamp", "Unix milliseconds", "yes" if sess["timestamps"]["unixOnMessage"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("the entry timestamp is ISO",\n'
        '               sess["timestamps"]["isoOnEntry"], "ISO string"),\n'
        '    pinb.check("the message timestamp is a Unix-milliseconds number",\n'
        '               sess["timestamps"]["unixOnMessage"], "number"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's reader, run against a real file

`ch27-session-entries/read-session.ts` is the reading program the chapter prints.
Run as a child process against the session written above, it is the chapter's own
reader against the chapter's own file.""",
    ),
    (
        "code",
        'print("Reader stdout:")\n'
        'print(sess["reader"]["stdout"])\n'
        'print()\n'
        "pinb.show_checks([\n"
        '    pinb.check("the reader exits 0", sess["reader"]["status"] == 0, "exit 0"),\n'
        '    pinb.check("it prints the session version", sess["reader"]["hasSessionLine"], "Session v3"),\n'
        '    pinb.check("it prints the user message", sess["reader"]["hasUser"], "user: hello"),\n'
        '    pinb.check("it prints the assistant message", sess["reader"]["hasAssistant"], "assistant: hello back"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

All three entry tests, plus the declaration comparison run by `tsc`.""",
    ),
    *canonical_tests(
        27,
        "ch27-session-entries/entries.test.ts",
        what="The chapter's canonical evidence",
        show="timestamp",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** The header's `version` is 3 at this pin. What happens if you
write a file with `version: 1`? Does Pi read it or refuse it?

**Then change one input.** `read-session.ts` switches on `entry.type`. Add a
`context_edit` row to the reader. What does a `context_edit` entry look like in
the file? (Chapter 5 has the shape.)

**Predict the boundary.** The driver reads a linear session. What does the entry
chain look like after a `/tree` branch — is `parentId` still the entry before?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. version 1: Pi reads it (the version is informational at read time).")\n'
        'print("  2. context_edit entry: has targetId and replacement; chapter 5 has the shape.")\n'
        'print("  3. After a branch: parentId points to the branch point, not the previous line.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  header: type={sess[\'header\'][\'type\']}, version={sess[\'header\'][\'version\']}, parentId present={sess[\'header\'][\'hasParentId\']}")\n'
        'entry_types = ", ".join(sess["entries"]["types"])\n'
        'print(f"  entries: {sess[\'entries\'][\'count\']} ({entry_types})")\n'
        'print(f"  timestamps: ISO entry={sess[\'timestamps\'][\'isoOnEntry\']}, Unix message={sess[\'timestamps\'][\'unixOnMessage\']}")\n'
        'print(f"  reader: exit={sess[\'reader\'][\'status\']}")\n'
        "print()\n"
        'assert sess["header"]["type"] == "session"\n'
        'assert not sess["header"]["hasParentId"]\n'
        'assert sess["entries"]["baseFieldsOk"] and sess["entries"]["linearChain"]\n'
        'assert sess["timestamps"]["isoOnEntry"] and sess["timestamps"]["unixOnMessage"]\n'
        'assert sess["reader"]["status"] == 0\n'
        'print("held: JSONL with a header; entry chain; two timestamp formats on one field name")',
    ),
    (
        "md",
        """## Interpretation

The session file is a **tree serialised as JSONL**, and each field has a job:

| Field | Type | What it tells you |
|---|---|---|
| `type` (header) | `"session"` | This line is the header, not an entry |
| `version` (header) | number | The format version — 3 at this pin |
| `id` | string | The entry's identity, used as a durable cursor |
| `parentId` | string \| null | The parent in the tree; `null` for a root |
| `timestamp` (entry) | ISO string | When the entry was appended |
| `message.timestamp` | Unix milliseconds | When the message was created |

The practical rules:
1. **Read JSONL line by line** — one JSON object per line, LF-terminated.
2. **The header is not an entry** — skip it when walking the tree.
3. **`id` is a durable cursor** — pass it as `since` to `get_entries` for incremental reads.
4. **Check the type of `timestamp`** — ISO on the entry, number on the message.
5. **A branch breaks the chain** — `parentId` points at the branch point, not the previous line.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=27,
            mode="**Run** + **Inspect** — a real persisted session file parsed directly, plus the chapter's own reader run as a child process and the declaration check.",
            scope="`in_process_runtime` + `declarations`. The format is Pi's; the read is direct.",
            provenance=[
                "**Ran** `drivers/ch27-session-entries.ts`: a real persisted session written, parsed directly, and read by the chapter's own `read-session.ts` as a child process.",
                "**Ran** `ch27-session-entries/entries.test.ts` (3 tests).",
                "**Ran** `tsc` over `ch27-session-entries/assert-equal.ts` (the declaration check).",
                "**Read** `examples/evidence.json`, chapter 27 rows (4 claims).",
            ],
            limits=[
                "**The header `version` moves** — 3 at this pin; the format is readable, not guaranteed across releases.",
                "**The projection passes and the per-entry-type visibility table** have no runtime test here — chapter 5 covers visibility.",
                "**The declaration comparison** is a compile-time check, not a runtime one.",
            ],
        ),
    ),
]