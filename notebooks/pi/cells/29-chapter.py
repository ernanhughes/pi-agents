"""Chapter 29 - Failures, Retries, and Recovery."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Failures, Retries, and Recovery"
QUESTION = """Does a normalised overflow error produce a compact-and-retry, and does it leave
a `context_edit` rather than deleting anything?

The chapter's point: Pi recognises a **specific** context-overflow signal. A
provider whose message Pi does not recognise needs a `message_end` handler that
normalises it. The recovery compacts, **omits the failed attempt with a
`context_edit`**, and runs again — it does not delete anything."""

CELLS = [
    ("md", heading(29, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "A provider's own overflow message, **normalised** by a `message_end` handler, triggers Pi's compact-and-retry recovery as a fresh run.",
                "The recovery emits `compaction_start:overflow` and `compaction_end:overflow`, then runs again.",
                "The failed attempt is **omitted from context with a `context_edit`**, not deleted from the file — a `compaction` entry is also written.",
                "**Without the handler** the same message is just a failure: no recovery is attempted.",
                "A **rate limit that happens to contain 'length'** is left alone — Pi's classification is specific, not substring-based on a generic word.",
            ],
            [
                "**Retry timings and a provider's transient-error classification are not verified** (`ch29-lim1`).",
                "**The substring is a stand-in** for a real provider's message — the handler matches `model is too long`.",
                "**One compact-and-retry attempt**, not a loop, is Pi's documented recovery limit.",
                "**The handler only rewrites the error message** — it does not change the model, the run, or the retry policy.",
            ],
        ),
    ),
    *setup_cells(
        29,
        mode="**Run** — real sessions with the chapter's `message_end` handler, driven by a scripted model that returns an overflow error.",
        scope="`in_process_runtime`. The classification, recovery and context_edit are Pi's.",
    ),
    (
        "md",
        """## Baseline: a normalised overflow triggers compact-and-retry""",
    ),
    (
        "code",
        'FAIL = pinb.driver_source("ch29-failures.ts")\n'
        'fail = pinb.driver(FAIL, label="ch29-failures", timeout=300)\n'
        'n = fail["normalisedOverflow"]\n'
        'print("Event sequence:", " -> ".join(n["events"]))\n'
        'print()\n'
        'pinb.show_checks([\n'
        '    pinb.check("recovery compacted with reason overflow",\n'
        '               n["compactionStartOverflow"], "compaction_start:overflow"),\n'
        '    pinb.check("and then ran again (compaction_end before agent_end)",\n'
        '               n["compactionEndBeforeAgentEnd"], "ran again"),\n'
        '    pinb.check("the failed attempt was omitted with a context_edit, not deleted",\n'
        '               n["hasContextEdit"], "context_edit written"),\n'
        '    pinb.check("a compaction entry was written", n["hasCompaction"], "compaction written"),\n'
        '    pinb.check("the run recovered", n["recovered"], "recovered after compaction"),\n'
        "])",
    ),
    (
        "md",
        """## Contrasting case: without the handler, no recovery""",
    ),
    (
        "code",
        'w = fail["withoutHandler"]\n'
        'print("Event sequence without the handler:", " -> ".join(w["events"]))\n'
        'print()\n'
        'pinb.show_checks([\n'
        '    pinb.check("without the handler, Pi does not recognise the message as an overflow",\n'
        '               not w["compactionStarted"], "no compaction started"),\n'
        "])",
    ),
    (
        "md",
        """## The classification is specific: a rate limit with 'length' is left alone""",
    ),
    (
        "code",
        'rl = fail["rateLimit"]\n'
        'print("Event sequence for a rate limit:", " -> ".join(rl["events"]))\n'
        'print()\n'
        'pinb.show_checks([\n'
        '    pinb.check("a rate limit containing the word length is not treated as an overflow",\n'
        '               not rl["compactionStarted"], "no compaction started"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

All three failure tests.""",
    ),
    *canonical_tests(
        29,
        "ch29-failures/overflow.test.ts",
        what="The chapter's canonical evidence",
        show="overflow",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** The handler matches `model is too long`. What happens if the
provider says `too many tokens` instead — does the handler normalise it?

**Then change one input.** Change the handler to match a broader string like
`too long`. What happens to a message that says `the file name is too long`?

**Predict the boundary.** Pi allows **one** compact-and-retry. What happens if the
retry also overflows — does it try again, or fail?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. too many tokens: NOT normalised - the handler matches only model is too long.")\n'
        'print("  2. Broader match: a file-name error would be misclassified as an overflow.")\n'
        'print("  3. Retry overflows again: Pi fails - the recovery is one attempt, not a loop.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  normalised: start={n[\'compactionStartOverflow\']}, end-before-agent-end={n[\'compactionEndBeforeAgentEnd\']}, recovered={n[\'recovered\']}")\n'
        'print(f"  context_edit written: {n[\'hasContextEdit\']}, compaction written: {n[\'hasCompaction\']}")\n'
        'print(f"  without handler: compaction started={w[\'compactionStarted\']}")\n'
        'print(f"  rate limit with length: compaction started={rl[\'compactionStarted\']}")\n'
        "print()\n"
        'assert n["compactionStartOverflow"] and n["compactionEndBeforeAgentEnd"]\n'
        'assert n["hasContextEdit"] and n["hasCompaction"] and n["recovered"]\n'
        'assert not w["compactionStarted"] and not rl["compactionStarted"]\n'
        'print("held: normalised overflow recovers with a context_edit; without it, failure; the classification is specific")',
    ),
    (
        "md",
        """## Interpretation

Recovery is a **repair path with a hard limit**, and the chapter shows the
boundaries:

| Signal | What happens | The boundary |
|---|---|---|
| Pi-recognised overflow | Compact-and-retry | **One** attempt, not a loop |
| Normalised by handler | Compact-and-retry | The handler rewrites the message only |
| Unrecognised error | Plain failure | No recovery attempted |
| Rate limit with "length" | Plain failure | Classification is specific, not substring |

The failed attempt is **omitted** from context with a `context_edit`, and a
`compaction` entry is written. Nothing is deleted from the file — the same
property chapter 23 found for compaction.

Practical rules:
1. **Know your provider's overflow message.** If Pi does not recognise it, normalise it with `message_end`.
2. **Match precisely.** A broad substring match misclassifies unrelated errors.
3. **Recovery is one attempt.** A retry that also overflows fails.
4. **The failure is not deleted.** `context_edit` omits it from context; the file keeps it.
5. **`session_compact_failed`** is the terminal counterpart for telemetry.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=29,
            mode="**Run** — real sessions with the chapter's `message_end` handler, driven by a scripted model that returns an overflow error.",
            scope="`in_process_runtime`. The classification, recovery and context_edit are Pi's.",
            provenance=[
                "**Ran** `drivers/ch29-failures.ts`: three real sessions (normalised overflow, no handler, rate limit with 'length').",
                "**Ran** `ch29-failures/overflow.test.ts` (3 tests).",
                "**Read** `examples/evidence.json`, chapter 29 rows (3 claims).",
            ],
            limits=[
                "**Retry timings and a provider's transient-error classification are not verified** (`ch29-lim1`).",
                "**The substring is a stand-in** for a real provider's message — the handler matches `model is too long`.",
                "**One compact-and-retry attempt**, not a loop, is Pi's documented recovery limit.",
            ],
        ),
    ),
]