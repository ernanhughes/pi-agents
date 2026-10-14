"""Chapter 31 - The Interface Is Not the Agent."""

import json

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "The Interface Is Not the Agent"
QUESTION = """Do print, JSON and RPC give the same answer and the same events, with only the
failure contract differing?

The chapter's point: the interface is an **observer**. The same agent runs under
each, produces the same answer and the same lifecycle events. What differs is
what you can watch — print has no events, JSON has no responses, RPC has both —
and how a failure is reported."""

CELLS = [
    ("md", heading(31, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "The same scripted run through **print, JSON and RPC** gives the same final answer.",
                "The **same lifecycle events, in the same order**, appear under JSON and RPC.",
                "What differs is the **observer**: print has no events, JSON has no responses, RPC has both.",
                "The **failure contract differs** by interface: print exits non-zero, JSON carries the failure in the stream and exits 0, RPC's command succeeds with the failure in the stream.",
                "The harness spawns the entry the package publishes as `pi` — the **shipped binary**, not a module inside `dist/`.",
                "A fresh **1.0.4 trace** is regenerated from the chapter's own exporter and compared with the published **1.0.2 recording**.",
            ],
            [
                "**Recorded inspection and fresh execution are different.** The published recording is 1.0.2 and stays labelled 1.0.2.",
                "**A browser replay is an inspection interface**, not proof that code ran in a browser or that a real model was called.",
                "**The model is scripted** — this measures the code around the model, not model behaviour.",
                "**The recording may be absent** from this checkout; if so the notebook reports it NOT INSPECTED instead of inventing it.",
            ],
        ),
    ),
    *setup_cells(
        31,
        mode="**Run** + **Inspect** — a fresh 1.0.4 run through the shipped binary, a fresh 1.0.4 trace from the chapter's exporter, and (when present) the published 1.0.2 recording.",
        scope="`shipped_binary`. The model is scripted; no real model is called.",
    ),
    (
        "md",
        """## Baseline: one agent, three drivers

The same scripted run — a `bash` call then an answer — through print, JSON and
RPC on the shipped binary.""",
    ),
    (
        "code",
        'THREE = pinb.driver_source("ch31-three.ts")\n'
        'three = pinb.driver(THREE, label="ch31-three", timeout=420)\n'
        's = three["success"]\n'
        'print(pinb.md_table(\n'
        '    ["driver", "final answer", "exit", "tool wrote file?", "has events?", "has responses?"],\n'
        '    [["print", s["print"]["text"], s["print"]["exit"], "yes" if s["print"]["toolWroteFile"] else "no", "no", "no"],\n'
        '     ["JSON", s["json"]["text"], s["json"]["exit"], "yes" if s["json"]["toolWroteFile"] else "no", "yes" if s["json"]["hasEvents"] else "no", "yes" if s["json"]["hasResponses"] else "no"],\n'
        '     ["RPC", s["rpc"]["text"], s["rpc"]["exit"], "yes" if s["rpc"]["toolWroteFile"] else "no", "yes" if s["rpc"]["hasEvents"] else "no", "yes" if s["rpc"]["hasResponses"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("all three drivers give the same final answer",\n'
        '               s["print"]["text"] == s["json"]["text"] == s["rpc"]["text"] == "the answer is forty-two",\n'
        '               "same answer"),\n'
        '    pinb.check("the tool ran under every driver (ran.flag exists)",\n'
        '               s["print"]["toolWroteFile"] and s["json"]["toolWroteFile"] and s["rpc"]["toolWroteFile"],\n'
        '               "tool ran three times"),\n'
        '    pinb.check("print has no events and no responses",\n'
        '               not s["print"]["hasEvents"] and not s["print"]["hasResponses"], "one string"),\n'
        '    pinb.check("JSON has events and no responses",\n'
        '               s["json"]["hasEvents"] and not s["json"]["hasResponses"], "events only"),\n'
        '    pinb.check("RPC has both events and responses",\n'
        '               s["rpc"]["hasEvents"] and s["rpc"]["hasResponses"], "both observers"),\n'
        "])",
    ),
    (
        "md",
        """## The same lifecycle events, in the same order""",
    ),
    (
        "code",
        'print("JSON lifecycle:", " -> ".join(s["json"]["lifecycle"]))\n'
        'print("RPC lifecycle: ", " -> ".join(s["rpc"]["lifecycle"]))\n'
        'print()\n'
        'pinb.show_checks([\n'
        '    pinb.check("JSON and RPC see the same lifecycle events in the same order",\n'
        '               s["json"]["lifecycle"] == s["rpc"]["lifecycle"], "identical"),\n'
        '    pinb.check("the tool executed in both",\n'
        '               "tool_execution_end" in s["json"]["lifecycle"], "tool_execution_end present"),\n'
        '    pinb.check("RPC sends a response before the first lifecycle event (accepted, not finished)",\n'
        '               s["rpc"]["responseBeforeFirstEvent"], "response first"),\n'
        "])",
    ),
    (
        "md",
        """## The failure contract differs by interface

The same provider failure, three ways. This is the one thing the interface
changes.""",
    ),
    (
        "code",
        'f = three["failure"]\n'
        'print(pinb.md_table(\n'
        '    ["driver", "exit", "where the failure is"],\n'
        '    [["print", f["print"]["exit"], "on stderr, no stdout" if f["print"]["messageOnStderr"] else "?"],\n'
        '     ["JSON", f["json"]["exit"], f"in the stream (stopReason={f[\'json\'][\'streamStopReason\']})"],\n'
        '     ["RPC", "-", f"in the stream (stopReason={f[\'rpc\'][\'streamStopReason\']}); command success={f[\'rpc\'][\'promptCommandSucceeded\']}"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("print mode exits non-zero on a failed response",\n'
        '               f["print"]["exit"] != 0, f"exit {f[\'print\'][\'exit\']}"),\n'
        '    pinb.check("print mode writes nothing to stdout",\n'
        '               f["print"]["stdoutEmpty"], "stdout empty"),\n'
        '    pinb.check("JSON mode exits 0 and carries the failure in the stream",\n'
        '               f["json"]["exit"] == 0 and f["json"]["streamStopReason"] == "error",\n'
        '               "exit 0, stopReason error"),\n'
        '    pinb.check("RPC command succeeds with the failure in the stream",\n'
        '               f["rpc"]["promptCommandSucceeded"] and f["rpc"]["streamStopReason"] == "error",\n'
        '               "response success=true, stopReason error"),\n'
        "])",
    ),
    (
        "md",
        """## A fresh 1.0.4 trace from the chapter's exporter

`experiences/ch31.ts` is a real exporter: it runs the scripted scenario against
the shipped binary and writes a `book-evidence-trace/1` envelope. Nothing here
writes a trace by hand.""",
    ),
    (
        "code",
        'TRACE = pinb.driver_source("ch31-trace.ts")\n'
        'trace = pinb.driver(TRACE, label="ch31-trace", timeout=420)\n'
        'print(pinb.md_table(\n'
        '    ["field", "value"],\n'
        '    [["schema", trace["schema"]],\n'
        '     ["result", trace["result"]],\n'
        '     ["evidenceScope", trace["evidenceScope"]],\n'
        '     ["claimClass", trace["claimClass"]],\n'
        '     ["recordedAt", trace["recordedAt"]],\n'
        '     ["runs", ", ".join(r["label"] for r in trace["runs"])],\n'
        '     ["environment pi-ai", trace["environment"].get("pi-ai", "?")]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("the exporter produces a schema-valid trace",\n'
        '               trace["schema"] == "book-evidence-trace/1", "schema ok"),\n'
        '    pinb.check("the fresh trace records the pinned pi-ai version",\n'
        '               trace["environment"].get("pi-ai") == pinb.PIN, f"pi-ai {trace[\'environment\'].get(\'pi-ai\')}"),\n'
        '    pinb.check("the fresh trace passes its own observations",\n'
        '               trace["result"] == "PASS", "PASS"),\n'
        '    pinb.check("the trace is labelled OBSERVED",\n'
        '               trace["claimClass"] == "OBSERVED", "OBSERVED"),\n'
        "])",
    ),
    (
        "md",
        """## The published recording (historical, Pi 1.0.2)

The browser experience at `/tools/ai/pi/31-chapter/` replays a recording captured
on **Pi 1.0.2**. It is evidence about that release, not about this pin. If its
directory is present it is inspected and labelled; if not, the notebook says so
rather than inventing it.

Set `PIN_EXPERIENCES` to the site repo's `content/tools/ai/pi` to inspect it.""",
    ),
    (
        "code",
        'import json\n'
        'exp = pinb.experience_dir(31)\n'
        'if exp is None:\n'
        '    pinb.unrun("the published 1.0.2 recording", "not present in this checkout; set PIN_EXPERIENCES to the site repo\'s content/tools/ai/pi")\n'
        'else:\n'
        '    rec = pinb.read_trace(exp / "recorded-trace.json")\n'
        '    meta = json.loads((exp / "experiment.json").read_text(encoding="utf-8"))\n'
        '    print("Published experience:", meta["id"])\n'
        '    print("Pinned version:", meta["pinnedVersion"])\n'
        '    print("Recorded at:", rec.get("recordedAt"))\n'
        '    print("Environment at capture:", rec.get("environment"))\n'
        '    print()\n'
        '    print("This is a RECORDED inspection of 1.0.2 evidence, not a fresh run.")\n'
        '    pinb.show_checks([\n'
        '        pinb.check("the recording is clearly labelled 1.0.2",\n'
        '                   meta["pinnedVersion"] == "1.0.2", "labelled 1.0.2"),\n'
        '        pinb.check("the recording is NOT relabelled to the current pin",\n'
        '                   rec.get("environment", {}).get("pi-ai") != pinb.PIN or meta["pinnedVersion"] == pinb.PIN,\n'
        '                   "not silently re-grounded"),\n'
        '    ])',
    ),
    (
        "md",
        """## The chapter's own tests

All six shipped-binary tests. They exercise the public bundled executable, which
is the strongest evidence this chapter has.""",
    ),
    *canonical_tests(
        31,
        "ch31-interface/binary.test.ts",
        what="The chapter's canonical evidence (shipped binary)",
        show="interface",
        timeout=420,
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** Print mode exits non-zero on a failed response. What does it
exit with on a *successful* run — 0, or the model's stop reason?

**Then change one input.** The script runs a `bash` tool. Remove it and run
`ch31-three.ts` again with only `{ text: ... }`. Does the lifecycle lose
`tool_execution_*` in all three drivers?

**Predict the boundary.** RPC's command succeeds even when the model failed.
What would a client that only checks `success` do wrong here?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. A successful print run exits 0.")\n'
        'print("  2. Without the tool, tool_execution_* disappears from JSON and RPC alike.")\n'
        'print("  3. A client checking only success would report a failed run as fine.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  success: print exit={s[\'print\'][\'exit\']}, JSON exit={s[\'json\'][\'exit\']}, RPC exit={s[\'rpc\'][\'exit\']}")\n'
        'print(f"  answers: {s[\'print\'][\'text\']} | {s[\'json\'][\'text\']} | {s[\'rpc\'][\'text\']}")\n'
        'print(f"  failure: print exit={f[\'print\'][\'exit\']}, JSON exit={f[\'json\'][\'exit\']}, RPC success={f[\'rpc\'][\'promptCommandSucceeded\']}")\n'
        "print()\n"
        'assert s["print"]["text"] == s["json"]["text"] == s["rpc"]["text"]\n'
        'assert s["json"]["lifecycle"] == s["rpc"]["lifecycle"]\n'
        'assert f["print"]["exit"] != 0 and f["json"]["exit"] == 0\n'
        'assert f["rpc"]["promptCommandSucceeded"] and f["rpc"]["streamStopReason"] == "error"\n'
        'print("held: same agent under three drivers; the interface changes only the observer and the failure contract")',
    ),
    (
        "md",
        """## Interpretation

The interface is an **observer**, and the chapter shows what each one can see:

| Driver | Output | Events | Responses | Failure contract |
|---|---|---|---|---|
| **print** | Final text | No | No | Non-zero exit, stderr |
| **JSON** | Event stream | Yes | No | Exit 0, failure in the stream |
| **RPC** | Line-framed JSONL | Yes | Yes | Command succeeds, failure in the stream |

The practical rules:
1. **The interface does not change the agent.** Same answer, same lifecycle events.
2. **Choose by what you need to observe** — a final answer (print), events (JSON), or a control channel (RPC).
3. **Check the failure contract.** A script that only checks an exit status will miss a JSON-mode failure; a client that only checks `success` will miss an RPC-mode one.
4. **Recorded is not fresh.** The published experience is a 1.0.2 recording and stays labelled that way.
5. **A browser replay is an inspection interface** — it is not proof that code ran in a browser or that a real model was called.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=31,
            mode="**Run** + **Inspect** — a fresh 1.0.4 run through the shipped binary, a fresh 1.0.4 trace from the chapter's exporter, and (when present) the published 1.0.2 recording.",
            scope="`shipped_binary`. The model is scripted; no real model is called.",
            provenance=[
                "**Ran** `drivers/ch31-three.ts`: the same scripted run and the same failure through print, JSON and RPC on the shipped binary.",
                "**Ran** `drivers/ch31-trace.ts`: `experiences/ch31.ts` regenerated a fresh 1.0.4 `book-evidence-trace/1` envelope.",
                "**Inspected** the published 1.0.2 recording at `/tools/ai/pi/31-chapter/` when `PIN_EXPERIENCES` resolves it (recorded, not fresh).",
                "**Ran** `ch31-interface/binary.test.ts` (6 tests).",
                "**Read** `examples/evidence.json`, chapter 31 rows (6 claims).",
            ],
            limits=[
                "**The published recording is 1.0.2** and is not relabelled.",
                "**A browser replay is an inspection interface**, not proof of execution.",
                "**The model is scripted** — no real-model behaviour is measured.",
            ],
            unrun=[
                "The published browser experience is inspected only when its directory is present; otherwise it is reported NOT INSPECTED.",
            ],
        ),
    ),
]