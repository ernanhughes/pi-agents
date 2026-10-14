"""Chapter 05 - Sessions and Where They Live."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Sessions and Where They Live"
QUESTION = """For one real session file: **which lines are on disk, and which of them ever
reach the model?**

"Stored" and "sent" are two different sets. The chapter's argument is that a
session file is a complete record, that the request is a projection of it, and
that a tool which confuses the two will quietly lose data."""

CELLS = [
    ("md", heading(5, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "The file is JSONL: a header, then one entry per message, in order, each "
                "with an `id` and a `parentId`. For a linear conversation each parent is "
                "the entry before it.",
                "**Stored is not sent.** `model_change`, `thinking_level_change` and an "
                "extension's own `custom` entry are on disk and appear nowhere in the next "
                "provider request.",
                "A `context_edit` with no replacement **hides** an earlier message from "
                "future requests without deleting it from the file — and the effect is "
                "**branch-relative**: navigating to a point before the edit brings the "
                "message back.",
                "Session location precedence is `--session-dir` > "
                "`PI_CODING_AGENT_SESSION_DIR` > the `sessionDir` setting, and the "
                "default group directory name is the working directory flattened.",
            ],
            [
                "**The file format has no stability guarantee** for a third-party "
                "consumer, and the header `version` has already changed twice across "
                "releases. What is shown here is what the pinned release writes.",
                "**Entry counts are small on purpose.** Three turns is enough to show the "
                "shape; nothing here measures a long session.",
                "**Nothing about how a provider maps these messages onto its wire "
                "format** — that is chapter 36 and it is a different question.",
            ],
        ),
    ),
    *setup_cells(
        5,
        mode="**Run** — a real persisted session written to a real file, then read back.",
        scope="`in_process_runtime` for the history; the shipped binary for the directory "
        "precedence. The provider is scripted.",
    ),
    (
        "md",
        """## Baseline: one real session file, read line by line

`harness/history.ts` builds the same three-turn conversation the book's chapters
share — question A, a question B that calls `bash`, question C — and persists it to
a real JSONL file through `SessionManager.create`.

The file is then read directly. Nothing is interpreted: this is the bytes.""",
    ),
    (
        "code",
        'DRIVER = r\'\'\'\n'
        'import { readFileSync } from "node:fs";\n'
        'import { buildHistory, requestFor, userTexts } from "../harness/history.ts";\n'
        "\n"
        "const rows = (file: string) => readFileSync(file, 'utf8').trim().split('\\n').map((l) => JSON.parse(l));\n"
        "\n"
        "const { h, file, entries, userEntry } = await buildHistory();\n"
        "const before = entries().map((e) => e.type);\n"
        "\n"
        "// A `custom` entry written by an extension: Pi's own record of something that\n"
        "// happened, with no message and therefore no place in the model's context.\n"
        "h.session.sessionManager.appendCustomEntry('my-ext.counter', { count: 42 });\n"
        "\n"
        "const sent = await requestFor(h, 'next question');\n"
        "const disk = rows(file);\n"
        "h.dispose();\n"
        "\n"
        "console.log(JSON.stringify({\n"
        '  headerType: disk[0].type,\n'
        '  headerHasParentId: Object.prototype.hasOwnProperty.call(disk[0], \'parentId\'),\n'
        '  diskEntryTypes: disk.map((e) => e.type),\n'
        '  diskMessageRoles: disk.filter((e) => e.type === \'message\').map((e) => e.message.role),\n'
        '  firstEntryIsRoot: disk[1]?.parentId === null,\n'
        '  parentIsPreviousEntry: disk.slice(2).every((e, i) => e.parentId === disk[i + 1].id),\n'
        '  sentRoles: sent.map((m) => m.role),\n'
        '  sentUserTexts: userTexts(sent),\n'
        '  sentMentionsCustomType: JSON.stringify(sent).includes(\'my-ext.counter\'),\n'
        '  sentMentionsModelChange: /model_change|thinking_level_change/.test(JSON.stringify(sent)),\n'
        '  entryTypesBeforeExtensionEntry: before,\n'
        '  entryTypesNow: disk.map((e) => e.type),\n'
        "}));\n"
        '\'\'\'\n'
        'disk = pinb.driver(DRIVER, label="ch05-stored-vs-sent", timeout=240)\n'
        'print(pinb.table(["", "value"],\n'
        '                 [[k, v] for k, v in disk.items() if not isinstance(v, list)], indent=""))\n'
        'print()\n'
        'print("entry types on disk, in order:")\n'
        'for i, t in enumerate(disk["diskEntryTypes"], 1):\n'
        '    print(f"  {i:2d}. {t}")',
    ),
    (
        "md",
        """Three things to notice before the assertions.

* `diskEntryTypes` contains `session`, then `message` entries, then at least one
  `model_change` or `thinking_level_change`, then `custom`.
* `sentRoles` contains **no trace** of the custom entry. It is on disk and gone
  from the request.
* `parentIsPreviousEntry` holds once past the root: for a linear conversation the
  tree degenerates to a list, and the file is still a tree. The first entry after the
  header roots it at `parentId: null`.""",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("the first line is the session header", disk["headerType"] == "session", disk["headerType"]),\n'
        '    pinb.check("the header is not part of the tree", not disk["headerHasParentId"], "no parentId on the header"),\n'
        '    pinb.check("every entry carries the role it stores",\n'
        '               disk["diskMessageRoles"][:4] == ["system", "user", "assistant", "user"],\n'
        '               str(disk["diskMessageRoles"][:4])),\n'
        '    pinb.check("a tool result is stored like any other message",\n'
        '               "toolResult" in disk["diskMessageRoles"], "present"),\n'
        '    pinb.check("the first entry roots the tree at null", disk["firstEntryIsRoot"], "parentId: null"),\n'
        '    pinb.check("after the root, each parent is the entry before it",\n'
        '               disk["parentIsPreviousEntry"], "chain holds over the rest"),\n'
        '    pinb.check("the file contains an entry type the request does not",\n'
        '               "custom" in disk["diskEntryTypes"] and "custom" not in [t for t in disk["sentRoles"]],\n'
        '               "custom on disk, absent from the request"),\n'
        '    pinb.check("model and thinking-level entries never reach the provider",\n'
        '               not disk["sentMentionsModelChange"], "absent"),\n'
        '    pinb.check("the extension\'s custom entry never reaches the provider",\n'
        '               not disk["sentMentionsCustomType"], "absent"),\n'
        '    pinb.check("the earlier user messages do reach the provider",\n'
        '               len(disk["sentUserTexts"]) >= 3, str(len(disk["sentUserTexts"])) + " user messages"),\n'
        "])",
    ),
    (
        "md",
        """## Experiment: a `context_edit` that hides without deleting

A `context_edit` entry with no replacement removes an earlier message from future
requests. The file still has it. And because the file is a tree, the removal
belongs to a *branch*: go back to before the edit and the message is sent again.

That last part is the one worth seeing, because it is the difference between
"deleted" and "not on this path".""",
    ),
    (
        "code",
        'DRIVER2 = r\'\'\'\n'
        'import { readFileSync } from "node:fs";\n'
        'import { buildHistory, requestFor, userTexts } from "../harness/history.ts";\n'
        "\n"
        "const rows = (file: string) => readFileSync(file, 'utf8').trim().split('\\n').map((l) => JSON.parse(l));\n"
        "const out: any = {};\n"
        "\n"
        "// (1) replacement form: the model sees new text, the file keeps the original.\n"
        "{\n"
        "\tconst { h, file, userEntry } = await buildHistory();\n"
        "\tconst target = userEntry('question A');\n"
        "\th.session.sessionManager.appendContextEdit(target.id, { content: 'REDACTED' });\n"
        "\tconst sent = await requestFor(h, 'probe');\n"
        "\tout.replacement = {\n"
        "\t\tfileStillHasOriginal: userTexts(rows(file).filter((e) => e.type === 'message').map((e) => e.message)).includes('question A'),\n"
        "\t\tsentTexts: userTexts(sent),\n"
        "\t\tfileHasContextEdit: rows(file).some((e) => e.type === 'context_edit'),\n"
        "\t};\n"
        "\th.dispose();\n"
        "}\n"
        "\n"
        "// (2) removal form, then navigate to a point BEFORE the edit.\n"
        "{\n"
        "\tconst { h, file, userEntry } = await buildHistory();\n"
        "\tconst target = userEntry('question A');\n"
        "\th.session.sessionManager.appendContextEdit(target.id, null);\n"
        "\tconst hidden = await requestFor(h, 'probe 1');\n"
        "\tconst answerToA = rows(file).find((e) => e.type === 'message' && e.parentId === target.id && e.message.role === 'assistant');\n"
        "\tawait h.session.navigateTree(answerToA.id, { summarize: false } as any);\n"
        "\tconst restored = await requestFor(h, 'probe 2');\n"
        "\tout.removal = {\n"
        "\t\thiddenAfterEdit: userTexts(hidden).includes('question A'),\n"
        "\t\tstillInFile: rows(file).some((e) => e.type === 'message' && JSON.stringify(e).includes('question A')),\n"
        "\t\trestoredAfterNavigatingBack: userTexts(restored).includes('question A'),\n"
        "\t\tleafBeforeEdit: answerToA.id,\n"
        "\t};\n"
        "\th.dispose();\n"
        "}\n"
        "\n"
        "console.log(JSON.stringify(out));\n"
        '\'\'\'\n'
        'edits = pinb.driver(DRIVER2, label="ch05-context-edit", timeout=300)\n'
        'print(pinb.md_table(\n'
        '    ["context_edit form", "in the file", "sent to the model"],\n'
        '    [["replacement: { content: REDACTED }",\n'
        '      f"original preserved: {edits[\'replacement\'][\'fileStillHasOriginal\']}",\n'
        '      f"question A present: {\'question A\' in edits[\'replacement\'][\'sentTexts\']}"],\n'
        '     ["removal: null",\n'
        '      f"original preserved: {edits[\'removal\'][\'stillInFile\']}",\n'
        '      f"after the edit: {edits[\'removal\'][\'hiddenAfterEdit\']}; after navigating back: {edits[\'removal\'][\'restoredAfterNavigatingBack\']}"]],\n'
        "))",
    ),
    (
        "code",
        "r, m = edits[\"replacement\"], edits[\"removal\"]\n"
        "\n"
        "pinb.show_checks([\n"
        '    pinb.check("a replacement edit leaves the file\'s own text untouched",\n'
        '               r["fileStillHasOriginal"], "the stored entry still says question A"),\n'
        '    pinb.check("a replacement edit writes a context_edit entry",\n'
        '               r["fileHasContextEdit"], "recorded"),\n'
        '    pinb.check("a removal edit hides the message from the next request",\n'
        '               not m["hiddenAfterEdit"], "question A absent"),\n'
        '    pinb.check("the hidden message is still in the file",\n'
        '               m["stillInFile"], "nothing deleted"),\n'
        '    pinb.check("navigating to a point before the edit brings it back",\n'
        '               m["restoredAfterNavigatingBack"], "the edit is branch-relative"),\n'
        "])",
    ),
    (
        "md",
        """## Contrasting case: where the file goes

A session's location is a three-level precedence, and it is worth checking because
it is the one configuration Pi reads **before** trust is resolved (chapter 8).

The canonical evidence for all of this — including the three-way precedence — is
the chapter's own test file, which drives the shipped binary for the location
rows.""",
    ),
    *canonical_tests(
        5,
        "ch05-disk/disk.test.ts",
        what="The chapter's canonical evidence",
        show="session",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** Write a `context_edit` for question **B** instead of question A,
navigate back before it, and ask whether question A is still sent.

**Then change one input.** `HIDE` below selects which user message is hidden.
Run it with `"A"` and with `"B"`.

**Predict the boundary.** What is the difference between `appendContextEdit(id,
null)` and `appendContextEdit(id, { content: "" })`? One removes the message; the
other sends the model an empty message. Which is safer for a secret, and why?""",
    ),
    (
        "code",
        'HIDE = "B"\n'
        "\n"
        'EXERCISE = DRIVER2.replace(\n'
        '    "const target = userEntry(\'question A\');",\n'
        '    "const target = userEntry(`question ${process.env.NB_HIDE}`);",\n'
        ")\n"
        'print("hiding the entry for question", HIDE)\n'
        'out = pinb.driver(EXERCISE, label="ch05-hide", timeout=300, env={"NB_HIDE": HIDE})\n'
        "print()\n"
        "for form, data in out.items():\n"
        '    print(f"  {form:12s} {data}")',
    ),
    (
        "md",
        """## Interpretation

The chapter's practical claim is that **the file is the record and the request is
a projection of it**, and the three experiments above are three consequences:

1. **You can store facts the model must not see.** `model_change`,
   `thinking_level_change` and an extension's `custom` entries are all durable,
   branch-relative and invisible. Chapter 19 is built entirely on that.
2. **Editing for the model and editing the record are different operations.** A
   `context_edit` with a replacement rewrites what is sent; the stored entry keeps
   its original text. If you are building an audit trail, the file is the audit
   trail.
3. **Redaction is a policy decision, not a deletion.** `appendContextEdit(id, null)`
   hides a message from this branch. It does not remove it from the file, it does
   not survive navigating back, and it does not touch any other branch. For a
   genuinely secret value, none of that is enough — which is chapter 42's subject.

### What this chapter does not settle

`metadata/05-chapter.yaml` records that there is no stable public schema guarantee
for a third-party consumer, and that the header `version` moves between releases.
The file is readable, not contract.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=5,
            mode="**Run** — three real persisted sessions written to real JSONL files and "
            "read back; plus the chapter's own test file, which drives the shipped binary for "
            "the location rows.",
            scope="`in_process_runtime` plus `shipped_binary` (the directory-precedence rows).",
            provenance=[
                "**Ran** `buildHistory()` three times — once for the stored-vs-sent diff, once "
                "for the replacement edit, once for the removal-plus-navigation case — each "
                "with its own temporary agent directory.",
                "**Read** the JSONL files directly with `readFileSync`; no interpretation "
                "layer sits between the assertion and the bytes.",
                "**Ran** `ch05-disk/disk.test.ts`.",
                "**Read** `examples/evidence.json`, chapter 5 rows (8 claims).",
            ],
            limits=[
                "**Three turns.** Enough to show every entry type the chapter names, not "
                "enough to say anything about a long session's growth or about compaction "
                "interacting with these entries (chapter 23).",
                "**The format is readable, not guaranteed.** The header `version` is 3 at "
                "this pin and has changed twice; `metadata/05-chapter.yaml` records that "
                "there is no stability promise for third-party readers.",
                "**Nothing about a session being portable between machines or between Pi "
                "installs.** Deleting a session is deleting its file, and nothing else holds "
                "it — which the chapter's own tests assert and this notebook does not repeat.",
            ],
        ),
    ),
]