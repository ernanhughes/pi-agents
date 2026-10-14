"""Chapter 10 - Writing a Task Pi Can Finish."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Writing a Task Pi Can Finish"
QUESTION = """Two things decide whether a task is finishable, and only one of them is
about the words. **What actually reaches the first prompt** — and when you type
mid-turn, where does your message land?

The chapter has no example directory. Its *mechanical* half is checkable; its
*argument* half is not, and this notebook is explicit about which is which."""

CELLS = [
    ("md", heading(10, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "`@path` in the **first** prompt attaches the file's contents, wrapped in "
                "a `<file>` block, alongside the rest of the prompt text.",
                "`--` terminates option parsing, so a prompt beginning with a dash reaches "
                "the model as that prompt.",
                "Piped stdin is **prepended** to the first prompt.",
                "A message sent while the agent is working has three possible homes, and "
                "they are not interchangeable: steering lands after the in-flight turn's "
                "tool calls; a follow-up waits until the agent would otherwise stop; and a "
                "plain prompt with no declared behaviour is **rejected** rather than guessed.",
            ],
            [
                "**Nothing about phrasing.** The chapter argues that *\"Fix the bug.\"* and "
                "a scoped task differ, and `metadata/10-chapter.yaml` records that the "
                "effect of any particular phrasing on completion rate **is not measured**. "
                "No experiment here could measure it: the model is scripted.",
                "**This chapter has no example directory and no ledger rows.** The evidence "
                "below is borrowed from chapters 32 and 25, where those mechanics already "
                "had tests, plus this notebook's own runs.",
                "**Compaction cuts at user-message boundaries** — a task with no second user "
                "message is a single span. Named, not exercised.",
            ],
        ),
    ),
    *setup_cells(
        10,
        mode="**Run** — the shipped binary for what reaches the prompt, and a real session "
        "with a slow tool for where a mid-turn message lands.",
        scope="`shipped_binary` for the input mechanics; `in_process_runtime` for delivery. "
        "This chapter has no example directory of its own.",
    ),
    (
        "md",
        """## Experiment 1: what actually reaches the first prompt

Four runs of the shipped binary, each in a fresh temporary directory, each reading
the `user` message out of the JSON event stream. The interesting comparison is
`@notes.md` against `go`: attaching a file does not replace the prompt, it is
inserted into it.""",
    ),
    (
        "code",
        'INPUTS = pinb.driver_source("ch10-inputs.ts")\n'
        'inputs = pinb.driver(INPUTS, label="ch10-inputs", timeout=300)\n'
        'print(pinb.md_table(\n'
        '    ["invocation", "exit", "what the model received as the first user message"],\n'
        '    [[k, v["exit"], (v["userText"][:110] + "...") if len(v["userText"]) > 110 else v["userText"]]\n'
        '     for k, v in inputs.items()],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("a bare prompt arrives unchanged", inputs["plain"]["userText"] == "go", repr(inputs["plain"]["userText"])),\n'
        '    pinb.check("@path attaches the file contents in a <file> block",\n'
        '               "<file" in inputs["attached"]["userText"] and "MEETING-NOTES-MARKER" in inputs["attached"]["userText"],\n'
        '               "marker present"),\n'
        '    pinb.check("the rest of the prompt survives the attachment",\n'
        '               inputs["attached"]["userText"].rstrip().endswith("summarise"), "summarise"),\n'
        '    pinb.check("-- stops option parsing",\n'
        '               inputs["optionTerminator"]["userText"] == "-5 degrees is cold",\n'
        '               repr(inputs["optionTerminator"]["userText"])),\n'
        '    pinb.check("piped stdin is prepended to the first prompt",\n'
        '               inputs["pipedStdin"]["userText"].startswith("PIPED-MARKER") and inputs["pipedStdin"]["userText"].endswith("go"),\n'
        '               repr(inputs["pipedStdin"]["userText"])),\n'
        '    pinb.check("every run exited cleanly", all(v["exit"] == 0 for v in inputs.values()), "exit 0"),\n'
        "])",
    ),
    (
        "md",
        """One detail worth noticing: the attachment appears **before** the remaining
prompt text. That is not cosmetic — it is why `@file` plus a question reads the way
it does to the model.

## Experiment 2: when you type while the agent is working

This is where the chapter's advice has a mechanical basis. A tool that takes 120 ms
gives a window; the driver sends a message into it and records the **shape of each
request** the provider received, in order.""",
    ),
    (
        "code",
        'DELIVERY = pinb.driver_source("ch10-delivery.ts")\n'
        'delivery = pinb.driver(DELIVERY, label="ch10-delivery", timeout=300)\n'
        "\n"
        "def show(label: str, requests: list[list[str]]) -> None:\n"
        '    print(f"{label}")\n'
        '    for i, req in enumerate(requests, 1):\n'
        '        print(f"  request {i}: " + " -> ".join(req))\n'
        "\n"
        'show("steering", delivery["steering"]["requests"])\n'
        "print()\n"
        'show("follow-up", delivery["followUp"]["requests"])\n'
        "print()\n"
        'print("a prompt with no declared behaviour:", delivery["refusal"])',
    ),
    (
        "code",
        "steer = delivery[\"steering\"][\"requests\"][0]\n"
        "follow = delivery[\"followUp\"][\"requests\"]\n"
        "\n"
        "pinb.show_checks([\n"
        '    pinb.check("steering lands after the in-flight turn\'s tool result",\n'
        '               steer == ["user:start", "assistant", "toolResult", "user:change direction"],\n'
        '               " -> ".join(steer)),\n'
        '    pinb.check("a follow-up is NOT in the request that was already under way",\n'
        '               "user:then also this" not in follow[0], "absent from request 1"),\n'
        '    pinb.check("a follow-up arrives in the next request, after the answer",\n'
        '               "user:then also this" in follow[1], "present in request 2"),\n'
        '    pinb.check("Pi refuses rather than guesses when no behaviour is declared",\n'
        '               delivery["refusal"].startswith("rejected"), delivery["refusal"]),\n'
        '    pinb.check("the refusal names the two behaviours it will accept",\n'
        '               "steer" in delivery["refusal"] and "followUp" in delivery["refusal"],\n'
        '               "both named"),\n'
        "])",
    ),
    (
        "md",
        """The difference between the two arms is the whole of the interaction design:

* **steering** joins the request the agent was *already going to make*, after the
  tool results it already had. The model sees your correction alongside the work it
  just did, and can act on both.
* **follow-up** waits for the agent to stop. It arrives in a fresh request, after
  an answer it did not need. That costs a turn, and it is the right choice when
  what you have to say is genuinely a new request.

And the third arm is the safety property: Pi does not guess. A message sent with no
declared behaviour is **rejected with a message naming both options**, rather than
delivered somewhere plausible.

### The chapter's own tests for the queue

Chapter 25 owns the full semantics — `queue_update` completeness, the two delivery
modes, `clearQueue()`. Those run below.""",
    ),
    *canonical_tests(
        10,
        ["ch25-queue/queue.test.ts", "ch32-headless/headless.test.ts"],
        what="The evidence chapter 10 delegates to",
        show="queue",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** Move `await h.session.steer(...)` to **after** `await running` in
the driver. Does the steering message still land in the same request? If not, where
does it go — and does it arrive at all?

**Then change one input.** `COMMAND` below is what the slow tool is asked to do.
Try a second `slow` call so the turn has two tool results, and see whether steering
still lands after both.

**Predict the boundary.** With `steeringMode: "all"` instead of the default
`one-at-a-time`, two queued messages delivered in one request would be an obvious
win. What is the cost — what does the model lose?""",
    ),
    (
        "code",
        'COMMAND = "two slow calls in one turn"\n'
        'print(f"predicted: with two tool results, steering still lands after the last one,")\n'
        'print(f"           so the request shape becomes start -> assistant -> toolResult -> toolResult -> your message")\n'
        "print()\n"
        "print(\"observed above, with ONE tool result:\")\n"
        'print("          " + " -> ".join(delivery["steering"]["requests"][0]))\n'
        "print()\n"
        'print("The chapter\'s own test asserts this same shape, and asserts the contrast:")\n'
        'print("  one-at-a-time (the default) delivers one steering message per turn;")\n'
        'print("  all delivers every queued message, at the cost of the model reading them")\n'
        'print("  as one undifferentiated block rather than one at a time.")\n'
        "\n"
        'assert delivery["steering"]["requests"][0][-1] == "user:change direction"\n'
        'print()\n'
        'print("held: your message is the last thing in the request, after the work already done")',
    ),
    (
        "md",
        """## Interpretation: two halves, only one of which is measurable here

**The mechanical half** — the part this notebook ran. Attachments, the option
terminator, piped stdin, and the three homes for a mid-turn message. All of it is
Pi's behaviour, all of it is checkable, and all of it will behave the same way for a
real model.

**The argument half** — the chapter's actual advice: name the input, name the
output, name the check. *\"Fix the bug.\"* delegates the definition of the task to
the model; *\"Summarise `@meeting-notes.md` and save the action items to
`action-items.md`.\"* does not.

That half is this book's reasoning, not Pi's contract, and it is **not measured**.
`metadata/10-chapter.yaml` says so, the faux provider could not measure it, and this
notebook does not pretend otherwise. If you want evidence for it, the mechanism
already exists in this repository: `examples/real-model/` freezes five inputs per
experiment in advance so a result cannot be fitted afterwards. No such run has been
accepted.

## Sources, execution mode and limitations

**Execution mode:** **Run** — the shipped binary for input mechanics, a real session
for delivery.

**Evidence scope:** `shipped_binary` and `in_process_runtime`.

### What was read or run

- **Ran** `drivers/ch10-inputs.ts`: four offline runs of the shipped binary, each in a
  fresh temporary directory, reading the `user` record out of the JSON stream.
- **Ran** `drivers/ch10-delivery.ts`: two real sessions with a 120 ms tool, recording
  the shape of every provider request, plus the refusal case.
- **Ran** `ch25-queue/queue.test.ts` and `ch32-headless/headless.test.ts`.
- **Read** `examples/evidence.json`: chapter 10 has **no rows**.

### Limitations

- **The phrasing claim is not measured and cannot be here.** No statement in this
  notebook supports it, and none is offered.
- **`@path` is only read in the first prompt**, which is what the driver exercised;
  attaching in a later turn is not tested here.
- **The 120 ms window is a real race.** The driver waits 40 ms before steering, which
  is well inside the window, but the test is timing-dependent in principle. It ran
  green here; a slower machine could make it flaky, which is why the assertion checks
  the request *shape* rather than a count of requests.""",
    ),
]
