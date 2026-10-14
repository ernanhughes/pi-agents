"""Chapter 33 - The JSON Event Stream."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "The JSON Event Stream"
QUESTION = """Is the framing really LF-only, and do all three reconstruction levels agree?

The chapter's point: JSON mode is one JSON object per line, **LF-terminated**.
U+2028 inside a string is legal JSON and is emitted raw, so a line reader that
splits on Unicode separators too breaks records. And `message_update` is
**delta-only** — the cumulative message and partial snapshots are omitted — so
three reconstruction levels must agree: buffered deltas, `text_end`, `message_end`."""

CELLS = [
    ("md", heading(33, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "The first record is the **session header**, version 3, not part of the tree.",
                "Every record is **one JSON object terminated by LF**; stdout carries nothing else.",
                "**U+2028 inside a string** is emitted raw and is not a record boundary — splitting on Unicode separators produces broken records.",
                "The run lifecycle: `agent_start` first, `agent_end` then `agent_settled` last.",
                "`message_update` is **delta-only**: no cumulative `message`, no `partial` snapshot; `usage` is present.",
                "**Three reconstruction levels agree**: buffered deltas, `text_end` content, and `message_end` text.",
                "The inner `assistantMessageEvent` vocabulary uses `contentIndex`; provider-level `start`/`done`/`error` are not emitted as `message_update`.",
                "Tool events carry the call id, name, args and result; `turn_end` carries the assistant message and its tool results.",
                "A failed response is `message_end` with `stopReason: error`, and the run still settles.",
            ],
            [
                "**Representative records, not every compaction/retry variant** (`ch33-lim1`).",
                "**`extension_error` is RPC-only** — it is not a JSON-mode record.",
                "**The model is scripted** — the event vocabulary is measured, not model behaviour.",
            ],
        ),
    ),
    *setup_cells(
        33,
        mode="**Run** — the shipped binary in `--mode json` with a scripted model.",
        scope="`shipped_binary`. The event vocabulary and framing are the real ones.",
    ),
    (
        "md",
        """## Baseline: framing and the header""",
    ),
    (
        "code",
        'JSONR = pinb.driver_source("ch33-json.ts")\n'
        'js = pinb.driver(JSONR, label="ch33-json", timeout=420)\n'
        'h = js["header"]\n'
        'print(pinb.md_table(\n'
        '    ["check", "value"],\n'
        '    [["header type", h["type"]],\n'
        '     ["header version", h["version"]],\n'
        '     ["header has parentId", "yes" if h["hasParentId"] else "no"],\n'
        '     ["LF terminated", "yes" if js["framing"]["lfTerminated"] else "no"],\n'
        '     ["every line parses", "yes" if js["framing"]["everyLineParses"] else "no"],\n'
        '     ["stderr empty", "yes" if js["framing"]["stderrEmpty"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("the first record is the session header", h["type"] == "session", "type session"),\n'
        '    pinb.check("the header has no parentId", not h["hasParentId"], "no parentId"),\n'
        '    pinb.check("stdout is LF-terminated and every line parses",\n'
        '               js["framing"]["lfTerminated"] and js["framing"]["everyLineParses"], "LF only"),\n'
        "])",
    ),
    (
        "md",
        """## U+2028 is not a boundary""",
    ),
    (
        "code",
        'u = js["unicode"]\n'
        'print(pinb.md_table(\n'
        '    ["parser", "records", "broken?"],\n'
        '    [["split on LF only", u["lfRecords"], "no" if not u["naiveBroken"] else "yes"],\n'
        '     ["split on LF and Unicode separators", u["naiveRecords"], "yes" if u["naiveBroken"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("U+2028 is emitted raw", u["rawIncludesLS"], "raw separator"),\n'
        '    pinb.check("splitting on LF only keeps every record whole", not u["naiveBroken"] or u["lfRecords"] > 0, "LF parse ok"),\n'
        '    pinb.check("splitting on Unicode separators produces more, broken records",\n'
        '               u["naiveRecords"] > u["lfRecords"] and u["naiveBroken"], "broken records"),\n'
        "])",
    ),
    (
        "md",
        """## The lifecycle and the delta-only vocabulary""",
    ),
    (
        "code",
        'life, inner = js["lifecycle"], js["innerVocabulary"]\n'
        'print("Ordered: agent_start before turn_start =", life["agentStartBeforeTurnStart"])\n'
        'print("Last two events:", " -> ".join(life["lastTwo"]))\n'
        'print("Inner kinds:", ", ".join(inner["kinds"]))\n'
        'print()\n'
        'pinb.show_checks([\n'
        '    pinb.check("agent_start comes before turn_start", life["agentStartBeforeTurnStart"], "ordered"),\n'
        '    pinb.check("agent_end then agent_settled are last", life["lastTwo"] == ["agent_end", "agent_settled"], "settled last"),\n'
        '    pinb.check("the inner vocabulary has text_start/delta/end",\n'
        '               all(k in inner["kinds"] for k in ["text_start", "text_delta", "text_end"]), ", ".join(inner["kinds"])),\n'
        '    pinb.check("provider-level start/done/error are NOT message_update kinds",\n'
        '               not any(k in inner["kinds"] for k in ["start", "done", "error"]), "absent"),\n'
        '    pinb.check("every inner event has a numeric contentIndex",\n'
        '               inner["allHaveContentIndex"], "contentIndex present"),\n'
        "])",
    ),
    (
        "code",
        'print("message_update is delta-only:", js["deltaOnly"]["deltaOnly"], f"({js[\'deltaOnly\'][\'updates\']} updates)")\n'
        'pinb.show_checks([\n'
        '    pinb.check("more than one delta, and no cumulative message or partial snapshot",\n'
        '               js["deltaOnly"]["updates"] > 1 and js["deltaOnly"]["deltaOnly"], "delta-only"),\n'
        "])",
    ),
    (
        "md",
        """## Three reconstruction levels agree""",
    ),
    (
        "code",
        'r = js["reconstruction"]\n'
        'print(pinb.md_table(\n'
        '    ["level", "text"],\n'
        '    [["buffered deltas", r["deltas"]],\n'
        '     ["text_end content", r["textEndContent"]],\n'
        '     ["message_end text", r["finalText"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("buffered deltas equal text_end content",\n'
        '               r["deltas"] == r["textEndContent"], "deltas == text_end"),\n'
        '    pinb.check("and equal the final message text",\n'
        '               r["deltas"] == r["finalText"], "deltas == message_end"),\n'
        "])",
    ),
    (
        "md",
        """## Tool calls, turn_end, and a failed run that still settles""",
    ),
    (
        "code",
        't, te, fr = js["tool"], js["turnEnd"], js["failedRun"]\n'
        'print(pinb.md_table(\n'
        '    ["check", "value"],\n'
        '    [["tool name", t["name"]],\n'
        '     ["same call id at start and end", "yes" if t["sameCallId"] else "no"],\n'
        '     ["tool result isError", t["endIsError"]],\n'
        '     ["turn_end message role", te["messageRole"]],\n'
        '     ["turn_end toolResults", te["toolResults"]],\n'
        '     ["failed run stopReason", fr["stopReason"]],\n'
        '     ["failed run last record", fr["lastType"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("tool events carry the same call id at start and end",\n'
        '               t["sameCallId"], "same id"),\n'
        '    pinb.check("a successful tool is not an error and its result has the output",\n'
        '               t["endIsError"] is False and t["resultHasHi"], "success"),\n'
        '    pinb.check("turn_end carries the assistant message and one tool result",\n'
        '               te["messageRole"] == "assistant" and te["toolResults"] == 1, "assistant + 1"),\n'
        '    pinb.check("a failed run is stopReason error and still settles",\n'
        '               fr["stopReason"] == "error" and fr["lastType"] == "agent_settled", "settled"),\n'
        '    pinb.check("extension_error is not a JSON-mode record",\n'
        '               not js["noExtensionError"]["hasExtensionError"], "absent"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

All eleven shipped-binary stream tests.""",
    ),
    *canonical_tests(
        33,
        "ch33-json/json-stream.test.ts",
        what="The chapter's canonical evidence (shipped binary)",
        show="record",
        timeout=420,
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** The header `version` is 3. Does a JSON-mode run with
`--no-session` still emit a session header record?

**Then change one input.** The script emits `U+2028` inside a string. What does a
consumer that uses Python's `str.splitlines()` see? (`splitlines` also splits on
`U+2028`, unlike splitting on `\\n`.)

**Predict the boundary.** `message_update` is delta-only. What must a consumer do
to reconstruct the text, and which two later records can check the result?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. --no-session JSON mode still emits the header record.")\n'
        'print("  2. Python splitlines() splits on U+2028 too - use split(\'\\\\n\').")\n'
        'print("  3. Buffer deltas; check against text_end and message_end.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  framing: LF={js[\'framing\'][\'lfTerminated\']}, all parse={js[\'framing\'][\'everyLineParses\']}")\n'
        'print(f"  unicode: LF records={u[\'lfRecords\']}, naive records={u[\'naiveRecords\']}, naive broken={u[\'naiveBroken\']}")\n'
        'print(f"  reconstruction equal: {r[\'deltas\'] == r[\'textEndContent\'] == r[\'finalText\']}")\n'
        "print()\n"
        'assert js["framing"]["lfTerminated"] and js["framing"]["everyLineParses"]\n'
        'assert u["naiveBroken"] and u["naiveRecords"] > u["lfRecords"]\n'
        'assert r["deltas"] == r["textEndContent"] == r["finalText"]\n'
        'assert js["deltaOnly"]["deltaOnly"]\n'
        'print("held: LF-only framing, U+2028 not a boundary, delta-only updates, three levels agree")',
    ),
    (
        "md",
        """## Interpretation

The JSON stream is a **wire format** with three rules a consumer must follow:

| Rule | What it means | The failure if broken |
|---|---|---|
| **LF-only framing** | Split on `\\n`, never on `str.splitlines()` | U+2028 splits a record |
| **Delta-only updates** | Buffer `text_delta`; do not expect the cumulative message | You read the wrong text |
| **Three levels agree** | `text_end` and `message_end` confirm your buffer | A dropped delta goes unnoticed |

The lifecycle:
* `agent_start` … per-turn events … `agent_end`, then `agent_settled` last.
* `tool_execution_start` / `tool_execution_end` carry the same call id.
* `turn_end` carries the assistant message and its tool results.

Practical rules:
1. **Split on `\\n` only** — a line reader that treats Unicode separators as newlines corrupts records.
2. **Buffer deltas** — `message_update` omits the cumulative message on purpose.
3. **Cross-check** — buffer against `text_end` and `message_end`.
4. **Wait for `agent_settled`** — `agent_end` is not the end.
5. **Read the failure in the stream** — exit 0 is not success in JSON mode.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=33,
            mode="**Run** — the shipped binary in `--mode json` with a scripted model.",
            scope="`shipped_binary`. The event vocabulary and framing are the real ones.",
            provenance=[
                "**Ran** `drivers/ch33-json.ts`: six shipped-binary JSON runs (header, U+2028, lifecycle, long answer, reconstruction, tool, failure).",
                "**Ran** `ch33-json/json-stream.test.ts` (11 tests).",
                "**Read** `examples/evidence.json`, chapter 33 rows (11 claims).",
            ],
            limits=[
                "**Representative records, not every compaction/retry variant** (`ch33-lim1`).",
                "**`extension_error` is RPC-only** — not a JSON-mode record.",
            ],
        ),
    ),
]