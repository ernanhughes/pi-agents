"""Chapter 25 - Steering, Queuing, and Changing Direction."""

import json

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Steering, Queuing, and Changing Direction"
QUESTION = """Where does a queued message land relative to a turn's tool calls?

The chapter's point: steering lands **after the turn's tool calls and before the
next request**. A follow-up waits until the agent would otherwise stop. The queue
carries the complete state each time, not a delta. And the delivery mode controls
whether one or all queued messages are delivered per turn."""

CELLS = [
    ("md", heading(25, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "Steering lands **after the turn's tool calls and before the next request** — the queued message appears as a user message after the tool results.",
                "A **follow-up waits** until the agent would otherwise stop — it is not delivered while the agent still has work.",
                "Steering **drains before follow-ups** — if both are queued, the steering message is delivered first.",
                "`queue_update` carries the **complete queue each time, not a delta** — every update lists all queued messages.",
                "**One-at-a-time** (the default) delivers one steering message per turn; **all** delivers every queued message in one request.",
                "A prompt while streaming with **no behaviour** is an **error**, not a guess.",
                "`clearQueue()` returns the queued text — this is how an interface restores it into the editor on Escape.",
                "An **extension command runs immediately** even while the agent is streaming; steering one is **refused** (it is a UI action, not model input).",
            ],
            [
                "**Latency from typing to delivery not measured** (`ch25-lim1`) — the 120 ms tool is a stand-in for real work.",
                "**No ranking of the two delivery modes** (`ch25-lim2`) — the test shows what each does, not which is better.",
            ],
        ),
    ),
    *setup_cells(
        25,
        mode="**Run** — real sessions with a 120 ms tool, driven by a scripted model that calls it.",
        scope="`in_process_runtime`. The queue mechanics, delivery modes, and streaming rules are Pi's.",
    ),
    (
        "md",
        """## Baseline: steering lands after tool calls, before next request

A 120 ms tool gives a window in which to steer. The queued message appears
**after the tool results** in the next request.""",
    ),
    (
        "code",
        'QUEUE = pinb.driver_source("ch25-queue.ts")\n'
        'queue = pinb.driver(QUEUE, label="ch25-queue", timeout=300)\n'
        'print("Second request shape:", " -> ".join(queue["steering"]["second"]))\n'
        'print()\n'
        'pinb.show_checks([\n'
        '    pinb.check("steering lands after tool calls and before next request",\n'
        '               queue["steering"]["second"] == ["user:start", "assistant", "toolResult", "user:change direction"],\n'
        '               " -> ".join(queue["steering"]["second"])),\n'
        "])",
    ),
    (
        "md",
        """## Follow-up waits until the agent would otherwise stop""",
    ),
    (
        "code",
        'reqs = queue["followUp"]["requests"]\n'
        'first_has_follow = any("then also this" in x for x in reqs[0])\n'
        'second_has_follow = any("then also this" in x for x in reqs[1])\n'
        'print("First request has follow-up:", first_has_follow)\n'
        'print("Second request has follow-up:", second_has_follow)\n'
        'print()\n'
        'pinb.show_checks([\n'
        '    pinb.check("follow-up NOT delivered while agent still has work",\n'
        '               not first_has_follow, "not in first request"),\n'
        '    pinb.check("follow-up delivered once agent is done",\n'
        '               second_has_follow, "in second request"),\n'
        "])",
    ),
    (
        "md",
        """## Steering drains before follow-ups""",
    ),
    (
        "code",
        'reqs2 = queue["steerBeforeFollowUp"]["requests"]\n'
        'steer_in_first = any("STEER" in x for x in reqs2[0])\n'
        'follow_in_first = any("FOLLOW" in x for x in reqs2[0])\n'
        'print("First request has STEER:", steer_in_first, "| has FOLLOW:", follow_in_first)\n'
        'print()\n'
        'pinb.show_checks([\n'
        '    pinb.check("steering delivered before follow-up",\n'
        '               steer_in_first and not follow_in_first,\n'
        '               "STEER first, FOLLOW later"),\n'
        "])",
    ),
    (
        "md",
        """## queue_update carries the complete queue, not a delta""",
    ),
    (
        "code",
        'updates = queue["queueUpdate"]["updates"]\n'
        'for i, u in enumerate(updates):\n'
        '    print(f"  update {i}: steering={u[\'steering\']}, followUp={u[\'followUp\']}")\n'
        'print()\n'
        'expected_first = {"steering": ["one"], "followUp": []}\n'
        'expected_second = {"steering": ["one"], "followUp": ["two"]}\n'
        'expected_last = {"steering": [], "followUp": []}\n'
        'pinb.show_checks([\n'
        '    pinb.check("first update has steering only",\n'
        '               updates[0] == expected_first, "steering only"),\n'
        '    pinb.check("second update still lists first message (not a delta)",\n'
        '               updates[1] == expected_second, "complete queue"),\n'
        '    pinb.check("queue ends empty",\n'
        '               updates[-1] == expected_last, "empty"),\n'
        "])",
    ),
    (
        "md",
        """## Delivery modes: one-at-a-time vs all""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["mode", "messages in first request"],\n'
        '    [["one-at-a-time", ", ".join(queue["deliveryMode"]["one-at-a-time"])],\n'
        '     ["all", ", ".join(queue["deliveryMode"]["all"])]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("one-at-a-time delivers one message per turn",\n'
        '               queue["deliveryMode"]["one-at-a-time"] == ["user:S1"],\n'
        '               "one message"),\n'
        '    pinb.check("all delivers every queued message",\n'
        '               queue["deliveryMode"]["all"] == ["user:S1", "user:S2"],\n'
        '               "all messages"),\n'
        "])",
    ),
    (
        "md",
        """## Prompt while streaming is an error""",
    ),
    (
        "code",
        'print("Error:", queue["promptWhileStreaming"]["error"][:80])\n'
        'print()\n'
        'pinb.show_checks([\n'
        '    pinb.check("prompt while streaming with no behaviour is an error",\n'
        '               bool(queue["promptWhileStreaming"]["error"]), "error raised"),\n'
        "])",
    ),
    (
        "md",
        """## clearQueue returns the queued text""",
    ),
    (
        "code",
        'print("Cleared:", queue["clearQueue"]["cleared"])\n'
        'print("Pending after clear:", queue["clearQueue"]["pending"])\n'
        'print()\n'
        'pinb.show_checks([\n'
        '    pinb.check("clearQueue returns both queues",\n'
        '               queue["clearQueue"]["cleared"] == {"steering": ["S1"], "followUp": ["F1"]},\n'
        '               "both queues returned"),\n'
        '    pinb.check("pending count is 0 after clear",\n'
        '               queue["clearQueue"]["pending"] == 0, "zero pending"),\n'
        "])",
    ),
    (
        "md",
        """## Extension command runs immediately while streaming""",
    ),
    (
        "code",
        'print("Ran while streaming:", queue["commandWhileStreaming"]["ranWhileStreaming"])\n'
        'print("Steer error:", queue["commandWhileStreaming"]["steerError"][:80])\n'
        'print()\n'
        'pinb.show_checks([\n'
        '    pinb.check("extension command runs immediately during streaming",\n'
        '               queue["commandWhileStreaming"]["ranWhileStreaming"] is True,\n'
        '               "ran during stream"),\n'
        '    pinb.check("steering an extension command is refused",\n'
        '               bool(queue["commandWhileStreaming"]["steerError"]), "refused"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

All eight tests from the chapter's test file.""",
    ),
    *canonical_tests(
        25,
        "ch25-queue/queue.test.ts",
        what="The chapter's canonical evidence",
        show="steering",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** What happens if you steer a message that is identical to the
original prompt? Does Pi deduplicate it?

**Then change one input.** The `steeringMode` setting has two values. What happens
if you set it to an invalid value — does Pi fall back to the default or error?

**Predict the boundary.** The 120 ms tool is a stand-in. What happens with a real
tool that takes 30 seconds — does the steering window stay open the whole time?""",
    ),
    (
        "code",
        'import json as _json\n'
        'print("Predictions:")\n'
        'print("  1. Identical steer: not deduplicated - delivered as a new user message.")\n'
        'print("  2. Invalid steeringMode: falls back to default (one-at-a-time).")\n'
        'print("  3. Real 30s tool: steering window stays open - that is the point of the queue.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print("  steering:", queue["steering"]["second"])\n'
        'ff = any("then also this" in x for x in queue["followUp"]["requests"][0])\n'
        'sf = any("then also this" in x for x in queue["followUp"]["requests"][1])\n'
        'print(f"  follow-up: first has it={ff}, second has it={sf}")\n'
        'print(f"  queue updates: {len(queue[\'queueUpdate\'][\'updates\'])} updates")\n'
        'print(f"  delivery: one-at-a-time={queue[\'deliveryMode\'][\'one-at-a-time\']}, all={queue[\'deliveryMode\'][\'all\']}")\n'
        "print()\n"
        'assert queue["steering"]["second"] == ["user:start", "assistant", "toolResult", "user:change direction"]\n'
        'assert not ff and sf\n'
        'assert queue["clearQueue"]["pending"] == 0\n'
        'assert queue["commandWhileStreaming"]["ranWhileStreaming"] is True\n'
        'print("held: steering lands after tool calls; follow-up waits; queue is complete not delta; modes differ")',
    ),
    (
        "md",
        """## Interpretation

The queue is three mechanisms, and the chapter shows the boundaries:

| Mechanism | What it does | The boundary |
|---|---|---|
| **Steering** | Injects a user message after current tool calls | Lands **before the next request**, not during |
| **Follow-up** | Queues a message for when the agent stops | **Waits** until agent would otherwise stop |
| **queue_update** | Notifies of queue state | **Complete queue each time**, not a delta |

Delivery modes:
* **one-at-a-time** (default): one steering message per turn — finer control
* **all**: every queued message in one request — faster delivery

Streaming rules:
* Prompt while streaming with **no behaviour** → **error**
* Extension command while streaming → **runs immediately**
* Steering an extension command → **refused** (UI action, not model input)

Practical rules:
1. **Steer to change direction mid-turn** — the message lands after current tool calls.
2. **Follow up to add work** — it waits until the agent is done.
3. **Use `clearQueue()` on Escape** — returns the text so the editor can restore it.
4. **Subscribe to `queue_update`** — always carries the full queue, safe to diff yourself.
5. **Choose delivery mode by task** — one-at-a-time for careful steering, all for batch input.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=25,
            mode="**Run** — real sessions with a 120 ms tool, driven by a scripted model that calls it.",
            scope="`in_process_runtime`. The queue mechanics, delivery modes, and streaming rules are Pi's.",
            provenance=[
                "**Ran** `drivers/ch25-queue.ts`: eight real sessions covering steering, follow-up, queue updates, delivery modes, streaming errors, clearQueue, and command-while-streaming.",
                "**Ran** `ch25-queue/queue.test.ts` (8 tests).",
                "**Read** `examples/evidence.json`, chapter 25 rows (8 claims).",
            ],
            limits=[
                "**Latency from typing to delivery not measured** (`ch25-lim1`) — the 120 ms tool is a stand-in for real work.",
                "**No ranking of the two delivery modes** (`ch25-lim2`) — the test shows what each does, not which is better.",
            ],
        ),
    ),
]