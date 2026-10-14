"""Chapter 16 - Events and the Extension Lifecycle."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Events and the Extension Lifecycle"
QUESTION = """With no UI to ask, **does a `tool_call` guard leave the filesystem untouched** —
and does a handler that throws fail closed rather than open?

The chapter's point is that `tool_call` fires *before* the tool runs, so a return
value with `block: true` stops the effect. The fail-safe (a thrown handler
blocks the tool) means a buggy guard is a total outage, not an open door."""

CELLS = [
    ("md", heading(16, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "A `tool_call` handler that returns `{ block: true, reason }` **prevents the tool from running** — the filesystem is untouched.",
                "When `ctx.hasUI` is false (print/JSON mode), the guard **refuses rather than allowing silently**.",
                "A `tool_call` handler that **throws blocks the tool as a fail-safe** — the same as `block: true`.",
                "Handlers run in registration order; `session_start` resets per-session state, not at module load.",
            ],
            [
                "**Ordering within a process only.** Two independently installed extensions racing on `tool_call` is open (`ch16-q2`).",
                "**A blocklist is a heuristic**, not containment. A determined model can evade it; the honest framing is that it raises the cost of an accident.",
                "**`agent_end` is not the end.** `agent_before_settle` is the final actionable boundary; `agent_settled` is notification-only.",
                "**No real `bash` is executed.** The tool call is intercepted before execution; the shell command string is the only thing examined.",
            ],
        ),
    ),
    *setup_cells(
        16,
        mode="**Run** — real sessions with the chapter's two guards and a throwing variant, driven by a scripted model that asks for `bash`.",
        scope="`in_process_runtime`. The shell and `git` are the reader's; the event order and block effect are Pi's.",
    ),
    (
        "md",
        """## Baseline: the no-UI path — the one most likely to be wrong

The chapter tests five cases. The first four run without a UI, so `ctx.hasUI` is
false and the guard must refuse rather than allow silently.""",
    ),
    (
        "code",
        'EVENTS = pinb.driver_source("ch16-events.ts")\n'
        'events = pinb.driver(EVENTS, label="ch16-events", timeout=300)\n'
        'print(pinb.md_table(\n'
        '    ["case", "isError", "blocked?", "ran.flag created?"],\n'
        '    [["no UI: force push", events["noUIForcePush"]["isError"], "yes" if events["noUIForcePush"]["hasGuardBlocked"] else "no", "yes" if events["noUIForcePush"]["ran"] else "no"],\n'
        '     ["no UI: ordinary touch", events["noUIOrdinary"]["isError"], "no", "yes" if events["noUIOrdinary"]["ran"] else "no"],\n'
        '     ["no UI: reset --hard", events["noUIResetHard"]["isError"], "yes", "-"],\n'
        '     ["no UI: multi-hook guard", events["noUIMultiHook"]["isError"], "yes" if events["noUIMultiHook"]["hasForceWithLease"] else "no", "yes" if events["noUIMultiHook"]["ran"] else "no"]\n'
        '    ]))\n',
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("no UI: force push is blocked and ran.flag is NOT created",\n'
        '               events["noUIForcePush"]["isError"] and events["noUIForcePush"]["hasGuardBlocked"] and not events["noUIForcePush"]["ran"],\n'
        '               "blocked, no side effect"),\n'
        '    pinb.check("no UI: ordinary command runs and ran.flag IS created",\n'
        '               not events["noUIOrdinary"]["isError"] and events["noUIOrdinary"]["ran"],\n'
        '               "allowed, side effect present"),\n'
        '    pinb.check("no UI: reset --hard is blocked",\n'
        '               events["noUIResetHard"]["isError"], "blocked"),\n'
        '    pinb.check("no UI: multi-hook guard blocks with --force-with-lease reason",\n'
        '               events["noUIMultiHook"]["isError"] and events["noUIMultiHook"]["hasForceWithLease"] and not events["noUIMultiHook"]["ran"],\n'
        '               "blocked, no side effect"),\n'
        "])",
    ),
    (
        "md",
        """## With a UI: the person decides

When `ctx.hasUI` is true, the guard asks. Two runs: approve and decline.""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["case", "isError", "ran.flag created?"],\n'
        '    [["with UI: approved", events["withUIApproved"]["isError"], "yes" if events["withUIApproved"]["ran"] else "no"],\n'
        '     ["with UI: declined", events["withUIDeclined"]["isError"], "yes" if events["withUIDeclined"]["ran"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("with UI: approved runs the command",\n'
        '               not events["withUIApproved"]["isError"] and events["withUIApproved"]["ran"],\n'
        '               "allowed, side effect present"),\n'
        '    pinb.check("with UI: declined blocks and ran.flag is NOT created",\n'
        '               events["withUIDeclined"]["isError"] and not events["withUIDeclined"]["ran"],\n'
        '               "blocked, no side effect"),\n'
        "])",
    ),
    (
        "md",
        """## Fail-safe: a throwing handler blocks the tool

`extensions.md` says: a `tool_call` handler failure blocks the tool as a
fail-safe. This is observed, not just documented.""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["case", "isError", "ran.flag created?"],\n'
        '    [["throwing handler", events["throwing"]["isError"], "yes" if events["throwing"]["ran"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("a throwing tool_call handler blocks the tool (fail-safe)",\n'
        '               events["throwing"]["isError"] and not events["throwing"]["ran"],\n'
        '               "blocked, no side effect"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

The five cases above are the chapter's test file, executed unmodified.""",
    ),
    *canonical_tests(
        16,
        "ch16-events/guard.test.ts",
        what="The chapter's canonical evidence",
        show="blocked",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** Add a second guard extension that also blocks `bash` on a
different pattern. Which one sees the call first — and what happens if the first
one allows but the second blocks?

**Then change one input.** The regexes match against `JSON.stringify(event.input)`.
What happens if the model sends `{"command": "git push --force"}` vs
`{"command": "git push --force-with-lease"}` — does the second match the
`--force|-f` pattern?

**Predict the boundary.** The throwing handler is a fail-safe. What happens if
*every* `tool_call` handler in the stack throws? Is the first one the one that
wins, or does the error propagate?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. Handlers run in registration order; the first to return block wins.")\n'
        'print("  2. --force-with-lease does NOT match the --force|-f pattern.")\n'
        'print("  3. The first handler to throw wins — the error stops the chain.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  no UI force push: isError={events[\"noUIForcePush\"][\"isError\"]}, blocked={events[\"noUIForcePush\"][\"hasGuardBlocked\"]}, ran={events[\"noUIForcePush\"][\"ran\"]}")\n'
        'print(f"  throwing handler:   isError={events[\"throwing\"][\"isError\"]}, ran={events[\"throwing\"][\"ran\"]}")\n'
        "print()\n"
        'assert events["noUIForcePush"]["isError"] and not events["noUIForcePush"]["ran"]\n'
        'assert events["throwing"]["isError"] and not events["throwing"]["ran"]\n'
        'print("held: the guard refuses without UI, and a thrown handler fails closed")',
    ),
    (
        "md",
        """## Interpretation

An event handler is three things, and the chapter shows all three:

1. **A gate** — `tool_call` with `block: true` stops the effect before it runs.
2. **A dialog** — `ctx.ui.confirm` asks when `ctx.hasUI`; print/JSON mode has no
   UI, so the honest behaviour is to refuse.
3. **A fail-safe** — an unhandled error in `tool_call` blocks the tool, so a
   buggy guard is a total outage, not an open door.

The practical rules:

* **Use the event's declared result type.** `tool_call` returns `{ block?, reason?, terminate? }` — nothing else has an effect.
* **Reset per-session state in `session_start`, not at module load.** A module-level variable survives reload; `session_start` fires once per session.
* **Catch inside the handler.** A guard that throws on every call is a total outage.
* **Handlers run in registration order.** If another extension also guards `bash`, whichever loaded first sees the call first.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=16,
            mode="**Run** — real sessions with the chapter's two guards and a throwing variant, driven by a scripted model that asks for `bash`.",
            scope="`in_process_runtime`. The shell and `git` are the reader's; the event order and block effect are Pi's.",
            provenance=[
                "**Ran** `drivers/ch16-events.ts`: seven real sessions with `ch16-events/guard.ts`, `ch16-events/guard-status.ts`, and a throwing variant.",
                "**Ran** `ch16-events/guard.test.ts` (5 tests).",
                "**Read** `examples/evidence.json`, chapter 16 rows (5 claims).",
            ],
            limits=[
                "**Ordering within a process only.** Two independently installed extensions racing on `tool_call` is not exercised.",
                "**A blocklist is a heuristic, not containment.** The regexes match the serialised input; a determined model can evade them.",
                "**No real `bash` is executed.** The tool call is intercepted before execution; only the command string is examined.",
                "**`agent_end` is not the end** — `agent_before_settle` is the final actionable boundary. This is documented, not run here.",
            ],
        ),
    ),
]