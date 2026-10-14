"""Chapter 36 - Model Access Without the Coding Agent."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Model Access Without the Coding Agent"
QUESTION = """Can one `models.complete()` become a typed value, and what happens when the
arguments break the schema?

The chapter's point: `pi-ai` is a library. One `complete()` call can end in a
**typed value** when the model submits valid data, a **rejection** when the
arguments break the schema, an **error** when the model answers with prose, or
an **exception** when the request itself fails. The caller must distinguish all
four."""

CELLS = [
    ("md", heading(36, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "`models.complete()` can return a **typed value** — the model's `submit_assessment` tool call is decoded and validated against the schema.",
                "Arguments that **break the schema are rejected**, not passed on.",
                "**Prose instead of a tool call** is an error the caller can see.",
                "A **failed request** is an exception with the provider's message, not a silent value, and one request costs exactly one call.",
            ],
            [
                "**Real-model behaviour is not measured** (`ch36-lim2`) — everything runs through the scripted provider.",
                "**The `builtinModels` / `classify` snippets** are documented API, not run.",
                "**One request count is exact for the scripted control flow only** (`ch36-lim2`).",
            ],
        ),
    ),
    *setup_cells(
        36,
        mode="**Run** — the chapter's `assess` against the scripted provider (`createModels` + `fauxProvider`).",
        scope="`in_process_runtime`. Schema validation and error surfaces are Pi's.",
    ),
    (
        "md",
        """## Baseline: one call, a typed value, exactly one request""",
    ),
    (
        "code",
        'ACCESS = pinb.driver_source("ch36-model-access.ts")\n'
        'acc = pinb.driver(ACCESS, label="ch36-model-access", timeout=180)\n'
        'v = acc["valid"]\n'
        'print(pinb.md_table(\n'
        '    ["check", "value"],\n'
        '    [["verdict", v["verdict"]],\n'
        '     ["request count", v["callCount"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("a valid submission comes back as a typed value",\n'
        '               v["verdict"] == "supported", "supported"),\n'
        '    pinb.check("it cost exactly one request", v["callCount"] == 1, "callCount 1"),\n'
        "])",
    ),
    (
        "md",
        """## Three failure shapes""",
    ),
    (
        "code",
        'sb, pr, fr = acc["schemaBreaking"], acc["prose"], acc["failedRequest"]\n'
        'print(pinb.md_table(\n'
        '    ["case", "rejected?", "detail"],\n'
        '    [["schema-breaking arguments", "yes" if sb["rejected"] else "no", sb["error"]],\n'
        '     ["prose instead of a tool call", "yes" if pr["rejected"] else "no", pr["error"]],\n'
        '     ["failed request", "yes" if fr["rejected"] else "no", "provider message surfaced" if fr["hasProviderMessage"] else "-"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("schema-breaking arguments are rejected, not passed on",\n'
        '               sb["rejected"], "rejected"),\n'
        '    pinb.check("prose instead of a tool call is an error",\n'
        '               pr["rejected"], "error"),\n'
        '    pinb.check("a failed request is an exception with the provider message",\n'
        '               fr["rejected"] and fr["hasProviderMessage"], "429 message surfaced"),\n'
        '    pinb.check("the failed request still cost exactly one call",\n'
        '               fr["callCount"] == 1, "callCount 1"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

All four model-access tests.""",
    ),
    *canonical_tests(
        36,
        "ch36-model-access/assess.test.ts",
        what="The chapter's canonical evidence",
        show="schema",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** The schema requires `confidence` between 0 and 1. What does the
call return if the model sends `confidence: 7` — and what would it do if you
changed the schema to allow any number?

**Then change one input.** `assess()` takes `citations: string[]`. What happens if
the model's tool call omits `citations` entirely — is that a schema error or a
default?

**Predict the boundary.** A failed request is an exception. What kind of error is
a *rate limit* — a provider failure with the message, or something else?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. confidence: 7 is rejected by the schema (the check is on the type).")\n'
        'print("  2. Omitting citations: schema error if required, default if optional.")\n'
        'print("  3. A rate limit surfaces as a provider failure exception with its message.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  valid: verdict={v[\'verdict\']}, callCount={v[\'callCount\']}")\n'
        'print(f"  schema-breaking rejected: {sb[\'rejected\']}")\n'
        'print(f"  prose rejected: {pr[\'rejected\']}")\n'
        'print(f"  failed request: rejected={fr[\'rejected\']}, has provider message={fr[\'hasProviderMessage\']}")\n'
        "print()\n"
        'assert v["verdict"] == "supported" and v["callCount"] == 1\n'
        'assert sb["rejected"] and pr["rejected"] and fr["rejected"] and fr["hasProviderMessage"]\n'
        'print("held: one call becomes a typed value; schema breaks are rejected; prose and failures are errors")',
    ),
    (
        "md",
        """## Interpretation

`pi-ai` is a library with four outcomes, and the chapter shows the boundaries:

| Outcome | When | What the caller sees |
|---|---|---|
| **Typed value** | Valid tool call matching the schema | The decoded submission, one request |
| **Rejection** | Arguments break the schema | An error naming the problem |
| **Error** | Prose instead of a tool call | An error meaning "you asked for a tool call" |
| **Exception** | The request itself fails | The provider's message, one request |

Practical rules:
1. **A failed request is a value, not silence** — check `stopReason` and `errorMessage` first.
2. **The schema is the contract** — codify the tool's output type and decode it.
3. **Count requests** — a valid call costs one; a repair costs two.
4. **Distinguish the four outcomes** — a schema break is not a provider failure.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=36,
            mode="**Run** — the chapter's `assess` against the scripted provider (`createModels` + `fauxProvider`).",
            scope="`in_process_runtime`. Schema validation and error surfaces are Pi's.",
            provenance=[
                "**Ran** `drivers/ch36-model-access.ts`: the chapter's `assess` four ways (valid, schema-breaking, prose, failed request).",
                "**Ran** `ch36-model-access/assess.test.ts` (4 tests).",
                "**Read** `examples/evidence.json`, chapter 36 rows (4 claims).",
            ],
            limits=[
                "**Real-model behaviour is not measured** (`ch36-lim2`) — everything runs through the scripted provider.",
                "**The `builtinModels` / `classify` snippets** are documented API, not run.",
            ],
        ),
    ),
]