"""Chapter 12 - Prompt Templates."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Prompt Templates"
QUESTION = """Send `/review` through a real session and read **the message the provider
actually received**. What was substituted, what was not, and who saw the raw text
before expansion?

A template is text plus a substitution table. Everything interesting is in the
edges: defaults, quoting, and what happens when an extension registers a command of
the same name."""

CELLS = [
    ("md", heading(12, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "The **default** `${1:-correctness, security, and error handling}` applies "
                "with no argument; an argument replaces it entirely.",
                "Shell-like quoting is honoured: `/review \"API compatibility\"` produces "
                "one argument, not two.",
                "The substitution table is `$1`, `$2`, `$@`, `$ARGUMENTS`, `${@:N}` and "
                "`${@:N:L}` — all six, in one request, asserted exactly.",
                "An `input` handler sees the **raw** text `/review \"API compatibility\"`, "
                "before expansion; an extension command of the same name preempts the "
                "template entirely, and the model is never asked (0 requests).",
            ],
            [
                "**A template can ask the model to run a command but cannot ensure it ran.** "
                "`metadata/12-chapter.yaml` records that limit; nothing here changes it.",
                "**Prompt templates are discovered non-recursively** — direct `.md` children "
                "of the conventional directories. Skills are recursive; that contrast is "
                "chapter 13.",
                "**Command/extension collision resolution is left open** by the chapter "
                "(`ch12-q2`). What is shown above is the observed behaviour: the extension "
                "wins and the model is not called.",
            ],
        ),
    ),
    *setup_cells(
        12,
        mode="**Run** — a real template in a real agent directory, sent through a real "
        "session, with the provider's request captured.",
        scope="`in_process_runtime`. Expansion, discovery and precedence are Pi's.",
    ),
    (
        "md",
        """## Baseline: what the model receives

The driver loads a template with an argument hint and a default, sends `/review`
twice — once bare, once with a quoted argument — and captures two different things
per run:

* `rawSeen` — what an `input` handler was given, which is the text as typed;
* `sentUser` — the `user` message content in the request the provider received.

If those two were the same string, the substitution would not be happening.""",
    ),
    (
        "code",
        'TEMPLATES = pinb.driver_source("ch12-templates.ts")\n'
        'templates = pinb.driver(TEMPLATES, label="ch12-templates", timeout=300)\n'
        'print("template body:")\n'
        'print("    Review the uncommitted git changes.")\n'
        'print("    Focus on ${1:-correctness, security, and error handling}.")\n'
        "print()\n"
        'rows = [\n'
        '    ["/review", templates["default"]["rawSeen"], templates["default"]["sentUser"]],\n'
        '    [\'/review "API compatibility"\', templates["argument"]["rawSeen"], templates["argument"]["sentUser"]],\n'
        "]\n"
        'print(pinb.md_table(\n'
        '    ["typed", "raw text an input handler saw", "the user message the provider received"],\n'
        '    [[typed, raw, sent.replace(chr(10), " / ")] for typed, raw, sent in rows],\n'
        "))",
    ),
    (
        "code",
        'd, a = templates["default"], templates["argument"]\n'
        "\n"
        "pinb.show_checks([\n"
        '    pinb.check("the default applies with no argument",\n'
        '               "correctness, security, and error handling" in d["sentUser"], "default present"),\n'
        '    pinb.check("an argument replaces the default entirely",\n'
        '               "API compatibility" in a["sentUser"] and "correctness" not in a["sentUser"],\n'
        '               a["sentUser"].splitlines()[-1]),\n'
        '    pinb.check("a quoted phrase is one argument",\n'
        '               a["sentUser"].rstrip().endswith("Focus on API compatibility."), "no split"),\n'
        '    pinb.check("the input handler sees the raw text, before expansion",\n'
        '               a["rawSeen"] == \'/review "API compatibility"\', repr(a["rawSeen"])),\n'
        '    pinb.check("the raw text still contains the quotes the model never sees",\n'
        '               \'"\' in a["rawSeen"] and \'"\' not in a["sentUser"], "quotes consumed by expansion"),\n'
        "])",
    ),
    (
        "md",
        """## The substitution table, all six at once

One template, six forms, one request. The expected string is fixed, so this is a
real assertion rather than a demonstration: if Pi's parser changed a form, this row
changes.""",
    ),
    (
        "code",
        'table = templates["substitutionTable"]\n'
        'print("template body:")\n'
        'print("    A=[$1] B=[$2] ALL=[$@] ARGUMENTS=[$ARGUMENTS] FROM2=[${@:2}] 2of2=[${@:2:2}] NONE=[$3]")\n'
        'print("invoked as: /t a b c")\n'
        "print()\n"
        'print("the provider received:")\n'
        'print("   ", table)\n'
        "print()\n"
        'expected = "A=[a] B=[b] ALL=[a b c] ARGUMENTS=[a b c] FROM2=[b c] 2of2=[b c] NONE=[c]"\n'
        "\n"
        "pinb.show_checks([\n"
        '    pinb.check("every form in the table substituted as documented",\n'
        '               table == expected, "exact match" if table == expected else repr(table)),\n'
        '    pinb.check("$1 and $2 are positional", "A=[a] B=[b]" in table, "positional"),\n'
        '    pinb.check("$@ and $ARGUMENTS are the whole argument list",\n'
        '               "ALL=[a b c]" in table and "ARGUMENTS=[a b c]" in table, "both present"),\n'
        '    pinb.check("${@:N} drops the first N, and ${@:N:L} also takes a length",\n'
        '               "FROM2=[b c]" in table and "2of2=[b c]" in table, "slice forms"),\n'
        '    pinb.check("a positional beyond the arguments falls through to the next argument",\n'
        '               "NONE=[c]" in table, "$3 resolved to c rather than being left literal"),\n'
        "])",
    ),
    (
        "md",
        """(The seventh form, `${1:-default}`, is the one asserted in the first table — the
default applied when the argument was absent and was replaced when one was given.)

## Contrasting case: an extension command of the same name

Preemption is total. The handler runs, the template does not, and — the number that
matters — **the model is never asked**: `requests == 0`.""",
    ),
    (
        "code",
        'withCommand = templates["withCommand"]\n'
        "print(pinb.md_table(\n"
        '    ["/review with an extension command of the same name registered", "the provider received"],\n'
        '    [["user message sent to the model", withCommand["sentUser"] or "(nothing)"],\n'
        '     ["provider requests", withCommand["requests"]]],\n'
        "))\n"
        "\n"
        "pinb.show_checks([\n"
        '    pinb.check("the template was discovered", "review" in withCommand["templates"], ", ".join(withCommand["templates"])),\n'
        '    pinb.check("but the extension command preempts it", withCommand["sentUser"] == "", "no user message"),\n'
        '    pinb.check("and the model was never asked", withCommand["requests"] == 0, str(withCommand["requests"])),\n'
        "])",
    ),
    *canonical_tests(
        12,
        "ch12-templates/templates.test.ts",
        what="The chapter's canonical evidence",
        show="template",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** Write a template with `${1:-A} and ${2:-B}` and invoke it with
`/x first`. What reaches the model — and how many words is it?

**Then change one input.** `TEMPLATE_BODY` below is what the driver writes. Add
`${@}` next to `$1` and re-run the table.

**Predict the boundary.** Why is `${3}` in the table above left as the literal `$3`
in one reading and as `c` in another? Decide which behaviour you would want for a
template whose third argument is genuinely optional, and say what the current
behaviour costs you.""",
    ),
    (
        "code",
        'TABLE_ROW = "A=[$1] B=[$2] ALL=[$@] ARGUMENTS=[$ARGUMENTS] FROM2=[${@:2}] 2of2=[${@:2:2}] NONE=[$3]"\n'
        "import re\n"
        "\n"
        "\n"
        "def substitute(body: str, args: list[str]) -> str:\n"
        '    """A Python restatement of the documented table, for inspection only.\n'
        "\n"
        "    The authoritative result is the request Pi built, shown two cells above.\n"
        '    """\n'
        "    out = body\n"
        "    for i, a in enumerate(args, 1):\n"
        '        out = out.replace(f"${i}", a)\n'
        '        out = re.sub(r"\\$\\{%d(?::-([^}]*))?\\}" % i, a or (r"\\1" or ""), out)\n'
        '    out = out.replace("$@", " ".join(args)).replace("$ARGUMENTS", " ".join(args))\n'
        '    out = re.sub(r"\\$\\{@:(\\d+)(?::(\\d+))?\\}",\n'
        '                 lambda m: " ".join(args[int(m.group(1)) - 1:(int(m.group(1)) - 1 + int(m.group(2))) if m.group(2) else None]), out)\n'
        "    return out\n"
        "\n"
        "\n"
        'print("template:", TABLE_ROW)\n'
        'print("args    : a b c")\n'
        'print("result  :", substitute(TABLE_ROW, ["a", "b", "c"]))\n'
        'print("observed:", templates["substitutionTable"])\n'
        "\n"
        'assert substitute(TABLE_ROW, ["a", "b", "c"]) == templates["substitutionTable"], (\n'
        '    "the restated table must agree with what Pi actually built")\n'
        'print()\n'
        'print("held: the rule, restated in Python, produces byte-identical output to Pi")\n'
        'print()\n'
        'print("Now change one input. What does ${3} cost you when the third argument is optional?")',
    ),
    (
        "md",
        """## Interpretation

A prompt template is three things stacked, and each one can fail quietly:

1. **Discovery** — conventional directories, direct `.md` children only. A nested
   template is not found, with no error.
2. **Precedence** — an extension command of the same name wins, and the model is
   never asked. Cheap to check (`requests == 0`) and invisible if you only read the
   output.
3. **Expansion** — the table above, applied to the raw text.

The practical rules that follow:

* **Put the instruction in the template, not in the habit.** A template is a file a
  team can review; a habit is a sentence in somebody's head.
* **Do not use a template to assert something happened.** It can *ask* the model to
  run a check. It cannot know whether it did. That is the limit
  `metadata/12-chapter.yaml` records, and it is chapter 16's subject.
* **Check nesting before syntax.** A template one directory too deep is not a
  template with a bug; it is not a template.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=12,
            mode="**Run** — four real sessions with a real template in a real agent "
            "directory, capturing the provider's request each time.",
            scope="`in_process_runtime`. Expansion, discovery and command precedence are Pi's.",
            provenance=[
                "**Ran** `drivers/ch12-templates.ts`: four sessions, each with its own "
                "temporary agent directory and its own `prompts/*.md`.",
                "**Captured the `user` message** out of the provider request in a faux "
                "response factory, so the assertion is about what the provider received.",
                "**Ran** `ch12-templates/templates.test.ts`.",
                "**Read** `examples/evidence.json`, chapter 12 rows (7 claims).",
            ],
            limits=[
                "**Substitution is not sandboxing.** A template body is text handed to a "
                "model. Nothing here establishes that the model will do what the template "
                "says, only that it was told it in this exact form.",
                "**The Python `substitute` in the exercise is a restatement**, not an "
                "implementation, and its only claim is that it agrees byte-for-byte with "
                "what Pi built in the cell above. The authority is the observed request.",
                "**Command precedence is observed, not specified.** The chapter leaves "
                "`ch12-q2` open; what is shown is what this release does.",
            ],
        ),
    ),
]