"""Chapter 35 - RPC."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "RPC"
QUESTION = """Does a successful `prompt` response mean *finished*, and does the UI
subprotocol block on the client?

The chapter's point: a `prompt` response means **accepted**, not finished —
`disposition: "started"`. The run follows as events, and a client waits for
`agent_settled`, not `agent_end`. The UI subprotocol is a request/answer pair
matched by id, and it blocks the client until the answer arrives."""

CELLS = [
    ("md", heading(35, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "Responses **repeat the command id**; two outstanding commands are matched by id, not by order.",
                "A successful `prompt` response means **accepted**: `disposition: \"started\"`, and it arrives **before the run's first event**.",
                "Session events carry **no command id** — only responses do.",
                "`agent_end` is not the end: **`agent_settled` follows it**, and is what a client waits for.",
                "A malformed JSON line produces a **parse response with no request id**; an unknown command is an error response and the process keeps serving.",
                "The **UI subprotocol** is a request/answer pair matched by id; the client blocks until it answers, and a UI response does **not** produce a normal command response.",
                "`get_entries` uses an entry id as a **durable cursor** (`since`), reports the leaf, and fails on an unknown cursor.",
                "`extension_error` is an RPC record: a handler that throws is reported and the run continues.",
            ],
            [
                "**`clear_queue` + `abort`, the UI timeout default and the less common dialog methods are not run** (`ch35-lim2`).",
                "**The Python client in the chapter was not executed** (`ch35-lim2`).",
                "**The model is scripted** — the protocol is measured, not model behaviour.",
            ],
        ),
    ),
    *setup_cells(
        35,
        mode="**Run** — real line-framed JSONL against the shipped binary, driven by the book's `RpcClient`.",
        scope="`shipped_binary`. The protocol is the real one.",
    ),
    (
        "md",
        """## Baseline: id matching, and `prompt` means accepted""",
    ),
    (
        "code",
        'RPC = pinb.driver_source("ch35-rpc.ts")\n'
        'rpc = pinb.driver(RPC, label="ch35-rpc", timeout=420)\n'
        'ids, acc = rpc["idMatching"], rpc["promptAccepted"]\n'
        'print(pinb.md_table(\n'
        '    ["check", "value"],\n'
        '    [["response a command", ids["aCommand"]],\n'
        '     ["response b command", ids["bCommand"]],\n'
        '     ["both succeeded", ids["bothSucceeded"]],\n'
        '     ["prompt disposition", acc["disposition"]],\n'
        '     ["response before first run event", acc["responseBeforeRun"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("two outstanding commands are matched by id",\n'
        '               ids["aCommand"] == "get_state" and ids["bCommand"] == "get_available_models", "matched by id"),\n'
        '    pinb.check("a successful prompt response means accepted (disposition started)",\n'
        '               acc["disposition"] == "started", "started"),\n'
        '    pinb.check("the response arrives before the run starts",\n'
        '               acc["responseBeforeRun"], "response first"),\n'
        "])",
    ),
    (
        "md",
        """## `agent_end` is not the end""",
    ),
    (
        "code",
        'e = rpc["agentEnd"]\n'
        'print(pinb.md_table(\n'
        '    ["check", "value"],\n'
        '    [["agent_end before agent_settled", e["agentEndBeforeSettled"]],\n'
        '     ["last record", e["last"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("agent_settled is what a client waits for",\n'
        '               e["agentEndBeforeSettled"] and e["last"] == "agent_settled", "settled last"),\n'
        "])",
    ),
    (
        "md",
        """## Protocol errors: malformed JSON and unknown commands""",
    ),
    (
        "code",
        'm, u = rpc["malformed"], rpc["unknown"]\n'
        'print(pinb.md_table(\n'
        '    ["case", "success", "has id", "process still serving"],\n'
        '    [["malformed JSON", m["success"], "yes" if m["hasId"] else "no", "-"],\n'
        '     ["unknown command", u["unknownSuccess"], "-", "yes" if u["stillServing"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("malformed JSON gives a failed parse response with no id",\n'
        '               m["success"] is False and not m["hasId"], "no id"),\n'
        '    pinb.check("an unknown command is an error, not a crash",\n'
        '               u["unknownSuccess"] is False and u["stillServing"], "still serving"),\n'
        "])",
    ),
    (
        "md",
        """## The UI subprotocol blocks on the client""",
    ),
    (
        "code",
        'ui = rpc["ui"]\n'
        'print(pinb.md_table(\n'
        '    ["check", "value"],\n'
        '    [["confirm title", ui["title"]],\n'
        '     ["blocked before the answer", ui["blockedBeforeAnswer"]],\n'
        '     ["notify after the answer", ui["noteMessage"]],\n'
        '     ["no normal command response", ui["noNormalResponse"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("the UI request carries a title and an id",\n'
        '               ui["title"] == "Clear session?", "title present"),\n'
        '    pinb.check("the client blocks until it answers",\n'
        '               ui["blockedBeforeAnswer"], "blocked"),\n'
        '    pinb.check("a UI response does not produce a normal command response",\n'
        '               ui["noNormalResponse"], "no response record"),\n'
        "])",
    ),
    (
        "md",
        """## `get_entries` as a durable cursor, and `extension_error`""",
    ),
    (
        "code",
        'cu, er = rpc["cursor"], rpc["extensionError"]\n'
        'print(pinb.md_table(\n'
        '    ["check", "value"],\n'
        '    [["leaf matches the last entry id", cu["leafMatchesCursor"]],\n'
        '     ["since cursor returns newer entries", cu["newerHasEntries"]],\n'
        '     ["unknown cursor fails", cu["invalidCursorFails"]],\n'
        '     ["extension_error event", er["event"]],\n'
        '     ["error message matches", er["errorMatches"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("get_entries reports the leaf and supports a since cursor",\n'
        '               cu["leafMatchesCursor"] and cu["newerHasEntries"], "cursor works"),\n'
        '    pinb.check("an unknown cursor fails", cu["invalidCursorFails"], "fails"),\n'
        '    pinb.check("a handler that throws is reported and the run continues",\n'
        '               er["event"] == "agent_start" and er["errorMatches"], "extension_error"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

All fourteen RPC tests.""",
    ),
    *canonical_tests(
        35,
        "ch35-rpc/rpc.test.ts",
        what="The chapter's canonical evidence (shipped binary)",
        show="response",
        timeout=420,
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** A `prompt` response says `disposition: "started"`. What does a
second prompt sent while the first is running return if it says `steer`?

**Then change one input.** Send `get_entries` with `since` set to the **first**
entry id instead of the last. How many entries come back?

**Predict the boundary.** The UI subprotocol blocks the client. What happens if
the client never answers — is there a timeout, and what value does the dialog
resolve to?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. A second prompt with steer returns success with disposition queued.")\n'
        'print("  2. since = first entry id returns every entry after it (all but the first).")\n'
        'print("  3. No answer: the client blocks until a timeout resolves the dialog (documented, not run).")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  id matching: a={ids[\'aCommand\']}, b={ids[\'bCommand\']}, both ok={ids[\'bothSucceeded\']}")\n'
        'print(f"  prompt disposition: {acc[\'disposition\']}, response first={acc[\'responseBeforeRun\']}")\n'
        'print(f"  agent_end before settled={e[\'agentEndBeforeSettled\']}, last={e[\'last\']}")\n'
        'print(f"  ui: blocked={ui[\'blockedBeforeAnswer\']}, note={ui[\'noteMessage\']}, no normal response={ui[\'noNormalResponse\']}")\n'
        "print()\n"
        'assert ids["bothSucceeded"] and acc["disposition"] == "started" and acc["responseBeforeRun"]\n'
        'assert e["agentEndBeforeSettled"] and e["last"] == "agent_settled"\n'
        'assert m["success"] is False and not m["hasId"]\n'
        'assert ui["blockedBeforeAnswer"] and ui["noNormalResponse"]\n'
        'assert cu["leafMatchesCursor"] and cu["invalidCursorFails"]\n'
        'print("held: prompt means accepted; agent_settled is the end; the UI subprotocol blocks and matches by id")',
    ),
    (
        "md",
        """## Interpretation

RPC has three contracts, and the chapter shows each:

| Contract | What it means | The boundary |
|---|---|---|
| **Responses** | Repeat the command id | Matched by id, not order |
| **`prompt`** | Accepted, not finished | `disposition: "started"`; wait for `agent_settled` |
| **Session events** | Carry no command id | Only responses have ids |
| **UI subprotocol** | Request/answer pair | Blocks the client; matched by id |
| **Errors** | Parse failure (no id), unknown command (error), handler throw (`extension_error`) | The process keeps serving |

Practical rules:
1. **Wait for `agent_settled`** — a `prompt` response is acceptance, not completion.
2. **Match responses by id** — do not assume order.
3. **Participate in the UI subprotocol** — answer request ids, or the client blocks.
4. **Use `since` as a durable cursor** — entry ids survive client restarts.
5. **Distinguish the error kinds** — a parse error has no id; a handler throw is an `extension_error` record.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=35,
            mode="**Run** — real line-framed JSONL against the shipped binary, driven by the book's `RpcClient`.",
            scope="`shipped_binary`. The protocol is the real one.",
            provenance=[
                "**Ran** `drivers/ch35-rpc.ts`: eight RPC scenarios (id matching, prompt acceptance, agent_settled, malformed JSON, unknown command, UI subprotocol, entry cursor, extension_error).",
                "**Ran** `ch35-rpc/rpc.test.ts` (14 tests).",
                "**Read** `examples/evidence.json`, chapter 35 rows (14 claims).",
            ],
            limits=[
                "**`clear_queue` + `abort`, the UI timeout default and the less common dialog methods are not run** (`ch35-lim2`).",
                "**The Python client in the chapter was not executed** (`ch35-lim2`).",
            ],
        ),
    ),
]