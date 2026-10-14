"""Chapter 34 - SDK Sessions."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "SDK Sessions"
QUESTION = """Does assigning `agent.state.messages` change what the provider receives?

The chapter's point: the `SessionManager` is **authoritative**. The in-memory
`agent.state.messages` is a view; assigning to it does not change what the
provider is sent. The session manager's history does."""

CELLS = [
    ("md", heading(34, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "Streaming: subscribe **before** prompting, and text arrives as typed `text_delta` events; `getLastAssistantText()` returns the same text.",
                "A prompt sent while streaming **must say steer or follow-up**, or it rejects.",
                "`SessionManager` is **authoritative**: assigning `agent.state.messages` does not change what is sent.",
                "An in-memory `SessionManager` **writes no file** (`getSessionFile()` is undefined).",
                "`dispose()` **stops event delivery** — a disposed session delivers nothing to listeners.",
            ],
            [
                "**No latency, throughput or isolation-failure measurement** (`ch34-lim1`).",
                "**The chapter's `createAgentSession` snippets are `documented-not-run`** — the harness uses `createAgentSession` internally but the chapter's snippets are not executed here.",
                "**The model is scripted** — this measures the session around the model, not model behaviour.",
            ],
        ),
    ),
    *setup_cells(
        34,
        mode="**Run** — real `AgentSession`s through the book's harness.",
        scope="`in_process_runtime`. The session authority, streaming and disposal are Pi's.",
    ),
    (
        "md",
        """## Baseline: streaming and the session authority""",
    ),
    (
        "code",
        'SDK = pinb.driver_source("ch34-sdk.ts")\n'
        'sdk = pinb.driver(SDK, label="ch34-sdk", timeout=300)\n'
        's = sdk["streaming"]\n'
        'print(pinb.md_table(\n'
        '    ["check", "value"],\n'
        '    [["deltas received", s["deltas"]],\n'
        '     ["buffered text", s["joined"]],\n'
        '     ["getLastAssistantText", s["last"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("text arrives across more than one delta",\n'
        '               s["deltas"] > 1, f"{s[\'deltas\']} deltas"),\n'
        '    pinb.check("the deltas concatenate to the full answer",\n'
        '               s["joined"] == "the repository has three packages", "joined ok"),\n'
        '    pinb.check("getLastAssistantText matches the buffered text",\n'
        '               s["last"] == s["joined"], "same text"),\n'
        "])",
    ),
    (
        "md",
        """## Prompting while streaming requires steer or follow-up""",
    ),
    (
        "code",
        'b = sdk["streamingBehaviour"]\n'
        'print(pinb.md_table(\n'
        '    ["check", "value"],\n'
        '    [["was streaming", b["wasStreaming"]],\n'
        '     ["prompt without behaviour rejected", b["rejected"]],\n'
        '     ["steer disposition", b["steered"]],\n'
        '     ["followUp disposition", b["followed"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("the session was streaming", b["wasStreaming"] is True, "streaming"),\n'
        '    pinb.check("a prompt with no behaviour is rejected", b["rejected"], "rejected"),\n'
        '    pinb.check("steer is queued", b["steered"] == "queued", "queued"),\n'
        '    pinb.check("followUp is queued", b["followed"] == "queued", "queued"),\n'
        "])",
    ),
    (
        "md",
        """## SessionManager is authoritative

Overwrite the in-memory transcript, then send another prompt. The forged history
never reaches the provider; the session manager's real history does.""",
    ),
    (
        "code",
        'a = sdk["authoritative"]\n'
        'print(pinb.md_table(\n'
        '    ["check", "value"],\n'
        '    [["forged history reached the provider", a["sentHasForged"]],\n'
        '     ["real history reached the provider", a["sentHasReal"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("the forged transcript never reached the provider",\n'
        '               not a["sentHasForged"], "forged absent"),\n'
        '    pinb.check("the real history, from the session manager, did",\n'
        '               a["sentHasReal"], "real present"),\n'
        "])",
    ),
    (
        "md",
        """## In-memory writes no file; dispose stops delivery""",
    ),
    (
        "code",
        'd = sdk["dispose"]\n'
        'print(pinb.md_table(\n'
        '    ["check", "value"],\n'
        '    [["in-memory session file is undefined", sdk["inMemory"]["fileUndefined"]],\n'
        '     ["events before dispose", d["eventsBefore"]],\n'
        '     ["events after dispose", d["eventsAfter"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("an in-memory SessionManager writes no file",\n'
        '               sdk["inMemory"]["fileUndefined"], "no file"),\n'
        '    pinb.check("a disposed session delivers nothing to listeners",\n'
        '               d["stopped"], f"{d[\'eventsBefore\']} -> {d[\'eventsAfter\']}"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

All five SDK tests.""",
    ),
    *canonical_tests(
        34,
        "ch34-sdk/sdk.test.ts",
        what="The chapter's canonical evidence",
        show="session",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** The forged `agent.state.messages` did not reach the provider.
What *does* the `agent.state.messages` view return after the second prompt — the
forged array, or the session manager's history?

**Then change one input.** Use a persistent `SessionManager` (`persist: true`).
Does `getSessionFile()` return a path? Does `dispose()` delete the file?

**Predict the boundary.** `dispose()` stops delivery to listeners already
subscribed. What happens to a *new* subscriber added after dispose?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. agent.state.messages returns the session manager\'s history after the next prompt.")\n'
        'print("  2. Persistent: getSessionFile() returns a path; dispose() does not delete the file.")\n'
        'print("  3. A new subscriber after dispose receives nothing.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  streaming: deltas={s[\'deltas\']}, joined matches last={s[\'joined\'] == s[\'last\']}")\n'
        'print(f"  streaming behaviour: rejected={b[\'rejected\']}, steer={b[\'steered\']}, followUp={b[\'followed\']}")\n'
        'print(f"  authority: forged={a[\'sentHasForged\']}, real={a[\'sentHasReal\']}")\n'
        'print(f"  in-memory file undefined={sdk[\'inMemory\'][\'fileUndefined\']}, dispose stopped={d[\'stopped\']}")\n'
        "print()\n"
        'assert s["deltas"] > 1 and s["joined"] == s["last"]\n'
        'assert b["rejected"] and b["steered"] == "queued" and b["followed"] == "queued"\n'
        'assert not a["sentHasForged"] and a["sentHasReal"]\n'
        'assert sdk["inMemory"]["fileUndefined"] and d["stopped"]\n'
        'print("held: SessionManager is authoritative; streaming needs a behaviour; dispose stops delivery")',
    ),
    (
        "md",
        """## Interpretation

The SDK session has three contracts, and the chapter shows each:

| Contract | What it means | The boundary |
|---|---|---|
| **Session authority** | `SessionManager` decides what is sent | `agent.state.messages` is a view, not the source |
| **Streaming** | Subscribe first; deltas arrive typed | A prompt mid-stream needs `steer` or `follow-up` |
| **Disposal** | `dispose()` stops delivery | Already-subscribed listeners receive nothing after |

Practical rules:
1. **The session manager is the source of truth** — do not mutate the transcript and expect it to stick.
2. **Subscribe before prompting** — a subscriber added after the deltas begin misses them.
3. **Say `steer` or `follow-up`** — a bare prompt mid-stream is an error by design.
4. **`dispose()` when done** — it stops event delivery; an in-memory session leaves no file.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=34,
            mode="**Run** — real `AgentSession`s through the book's harness.",
            scope="`in_process_runtime`. The session authority, streaming and disposal are Pi's.",
            provenance=[
                "**Ran** `drivers/ch34-sdk.ts`: real sessions covering streaming, streaming behaviour, session authority, in-memory sessions, and disposal.",
                "**Ran** `ch34-sdk/sdk.test.ts` (5 tests).",
                "**Read** `examples/evidence.json`, chapter 34 rows (5 claims).",
            ],
            limits=[
                "**No latency, throughput or isolation-failure measurement** (`ch34-lim1`).",
                "**The chapter's `createAgentSession` snippets are `documented-not-run`**.",
            ],
        ),
    ),
]