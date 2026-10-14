"""Chapter 01 - The Loop You Are Writing For."""

from _common import establishes, heading, setup_cells, sources_and_limits

TITLE = "The Loop You Are Writing For"
QUESTION = """One turn, with no `pi` binary, no terminal and no credential: what actually
happens, and **where in the stream is the decision "is anything else needed?"**

The chapter opens by taking everything away — no binary, no interface, no
credential — and then puts back the one loop that remains. The interesting
question is not what the loop does but *what ends it*, because that is the
thing you have to be able to see in order to control it."""

CELLS = [
    ("md", heading(1, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "A single prompt produces an ordered event stream beginning with "
                "`agent_start` and ending with `agent_end`.",
                "The loop continues **exactly** while the assistant's `stopReason` is "
                "`toolUse`, and stops on any other `stopReason`.",
                "One turn costs a countable number of provider requests: 2 for "
                "tool-then-answer, 3 when the model asks twice, 1 when the provider "
                "fails on the first call.",
                "The bare agent core does **not** emit `agent_settled`. That event "
                "belongs to the coding agent above the core, and a program reading the "
                "core's stream will not find it.",
            ],
            [
                "Nothing about a real model. The provider is scripted: every case "
                "exercised here is a case someone anticipated.",
                "Nothing about token accounting, retries or provider internals — the "
                "core has no notion of them (chapter 29).",
                "Nothing about how often a real model keeps asking for tools. The "
                "three-request case below is a script, not a measurement.",
            ],
        ),
    ),
    *setup_cells(
        1,
        mode="**Run** — the chapter's own example, then a structured capture of the same loop.",
        scope="`in_process_runtime` (`@earendil-works/pi-agent-core` only). No binary, no interface.",
    ),
    (
        "md",
        """## Baseline: the chapter's example, run unmodified

`examples/ch01-agent-core/agent-core.ts` is the file the chapter embeds verbatim.
It is 45 lines: a tool, two scripted responses, an `Agent`, and a subscriber that
prints two kinds of event. Running it is the smallest honest evidence that the
loop the book describes is the loop that exists.""",
    ),
    (
        "code",
        'r = pinb.run_node(["ch01-agent-core/agent-core.ts"], timeout=60)\n'
        "print(r.assert_ok('the chapter 1 example').describe())",
    ),
    (
        "md",
        """Three lines, and each one is a mechanism:

* `stop: toolUse` — the assistant asked for a tool, so the loop continues.
* `tool: word_count {"words":4}` — the tool's `execute()` ran and returned `details`.
* `stop: stop` — the assistant answered with no tool call, so the loop ends.

The example prints. What a program needs is the *sequence*, so the next cell runs
the same loop and records it.""",
    ),
    (
        "md",
        """## Experiment: make the stop decision queryable

`drivers/ch01-loop.ts` builds the same agent core the chapter builds — same tool,
same provider, same `Agent` constructor — and subscribes to the stream to record the
ordered event types plus each assistant message's `stopReason`.

This is orchestration, not re-implementation: it calls
`@earendil-works/pi-agent-core` and substitutes nothing except the model.""",
    ),
    (
        "code",
        'DRIVER = pinb.driver_source("ch01-loop.ts")\n'
        'runs = pinb.driver(DRIVER, label="ch01-loop", timeout=180)\n'
        "print(pinb.table(\n"
        '    ["run", "requests", "assistant stopReasons", "tool runs"],\n'
        "    [[name.replace(chr(95), ' '), r['requests'], ' -> '.join(r['stopReasons']), len(r['toolRuns'])]\n"
        "     for name, r in runs.items()],\n"
        '    indent="",\n'
        "))",
    ),
    (
        "code",
        'for name, r in runs.items():\n'
        '    print(f"\\n{name}:")\n'
        '    for i, ev in enumerate(r["stream"], 1):\n'
        '        print(f"  {i:2d}. {ev}")',
    ),
    (
        "md",
        """## The assertion that matters

Three facts, each checked against a boundary rather than against a string the
script just wrote:

* the request count, which is the only cost the loop imposes;
* the assistant's `stopReason` sequence, which *is* the termination decision;
* the absence of `agent_settled` from the core's own stream — a positive claim
  about what the core does not emit.""",
    ),
    (
        "code",
        'one = runs["oneToolThenAnswer"]\n'
        'many = runs["keepsAsking"]\n'
        'bad = runs["providerError"]\n'
        "\n"
        "pinb.show_checks([\n"
        '    pinb.check("the stream starts at agent_start", one["stream"][0] == "agent_start", one["stream"][0]),\n'
        '    pinb.check("tool-then-answer costs exactly two provider requests", one["requests"] == 2, str(one["requests"])),\n'
        '    pinb.check("the loop continued exactly while stopReason was toolUse",\n'
        '               one["stopReasons"] == ["toolUse", "stop"], str(one["stopReasons"])),\n'
        '    pinb.check("the tool body ran once, and its details reached the stream",\n'
        '               one["toolRuns"] == [{"words": 4}], str(one["toolRuns"])),\n'
        '    pinb.check("a model that keeps asking costs one request per ask",\n'
        '               many["requests"] == 3, str(many["requests"])),\n'
        '    pinb.check("a provider failure costs one request and runs no tool",\n'
        '               bad["requests"] == 1 and bad["toolRuns"] == [],\n'
        '               f"requests={bad[\'requests\']} tools={len(bad[\'toolRuns\'])}"),\n'
        '    pinb.check("the core emits no agent_settled",\n'
        '               not any(e.endswith("settled") for e in one["stream"]), "absent, as declared"),\n'
        "])",
    ),
    (
        "md",
        """## Contrasting case: what a failure looks like

The third run is the interesting one. The scripted response carries
`stopReason: "error"` and an error message. The loop does **not** retry, does
**not** call the tool, and still fires `agent_end`.

That matters for the book's argument in chapter 1: `agent_end` means *the run is
over*, not *the run succeeded*. A program that watches only for `agent_end` will
treat a 429 exactly like a finished answer. Chapter 29 is about the machinery
that makes the difference visible.""",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** `keepsAsking` has two `toolUse` responses and one `stop`.
Before running the cell below, write down: how many requests, and how many tool
executions?

**Then change one input.** `TEXTS` below is what the tool is asked to count. Each
string is a separate turn.

**Predict what breaks.** The request count follows the script length, not the
words. What *would* make the count change? (Chapter 38 is about exactly that:
what happens when a run does not terminate on its own.)""",
    ),
    (
        "code",
        'TEXTS = ["  spaced   out  ", "one"]\n'
        "import json as _json\n"
        "\n"
        'print("TEXTS to count:", TEXTS)\n'
        'print("predicted requests:", len(TEXTS) + 1, " predicted tool executions:", len(TEXTS))\n'
        "\n"
        'again = pinb.driver(DRIVER, label="ch01-exercise", timeout=180, env={"NB_TEXTS": _json.dumps(TEXTS)})\n'
        'observed = again["keepsAsking"]\n'
        'print("observed requests:", observed["requests"], " tool executions:", len(observed["toolRuns"]))\n'
        'print("observed word counts:", [r.get("words") for r in observed["toolRuns"]])\n'
        "\n"
        'assert observed["requests"] == len(TEXTS) + 1\n'
        'print("\\nheld: the count follows the script length; the word counts are data")',
    ),
    (
        "md",
        """## Interpretation: the decision you are actually writing

The loop has no "task complete" concept. It has one rule: **keep going while the
assistant's `stopReason` is `toolUse`.** Everything the chapter goes on to build
— compaction, steering, permissions, retries, the terminal — exists because that
rule needs supervising.

Two practical consequences:

1. **Termination is observable.** If you want to know whether work is finished,
   read `stopReason`. Anything else — `agent_end`, "the process exited", "it
   printed something" — is a proxy, and this notebook shows a proxy that lies.
2. **A loop with no bound is a liability.** `keepsAsking` terminated only because
   the script ran out. Chapter 38 puts a bound on the same shape and shows what
   happens when a model never submits.

### Read the ledger for this chapter

The book's own claim ledger has one row for chapter 1. Inspecting it is a useful
habit: a row names the file, the claim class and the evidence scope, so a number in
the text can be traced to the code that produced it.""",
    ),
    (
        "code",
        'rows = pinb.evidence_rows(1)\n'
        "print(pinb.table(\n"
        '    ["file", "claim", "claim class", "evidence scope", "compile", "runtime"],\n'
        '    [[r["file"], r["claim"], r["claim_class"], r["evidence_scope"], r["compile"], r["runtime"]] for r in rows],\n'
        '    indent="",\n'
        "))",
    ),
    (
        "md",
        sources_and_limits(
            chapter=1,
            mode="**Run.** `examples/ch01-agent-core/agent-core.ts` executed unmodified, then a "
            "structured capture of the same loop through `drivers/ch01-loop.ts`.",
            scope="`in_process_runtime`. `@earendil-works/pi-agent-core` and `@earendil-works/pi-ai`, "
            "neither of which imports an interface package — which is what makes the chapter's "
            "\"no binary, no terminal\" claim checkable rather than rhetorical.",
            provenance=[
                "**Ran** `ch01-agent-core/agent-core.ts` — the file the chapter embeds "
                "under `<!-- example: ch01-agent-core/agent-core.ts -->`, so `npm run check-embedded` "
                "already ties it to the manuscript.",
                "**Ran** `drivers/ch01-loop.ts` against the pinned packages; it adds a "
                "subscriber and nothing else.",
                "**Read** `examples/evidence.json`, chapter 1 row.",
            ],
            limits=[
                "**The model is scripted.** Every branch exercised here is a branch someone "
                "wrote down in advance. Nothing here is evidence about how often a real model "
                "asks for a tool, or how often it stops when it should not.",
                "**No provider internals.** Retries, rate limits and context overflow are not "
                "in the core; the `error` stop reason is the whole of what the loop can see. "
                "Chapter 29.",
                "**`agent_settled` is absent from the core's stream.** That is a reading of the "
                "pinned declarations *and* of the stream recorded above; it is not a promise "
                "about future releases.",
            ],
        ),
    ),
]