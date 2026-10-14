"""Chapter 30 - Debugging by Layer."""

from _common import establishes, heading, setup_cells, sources_and_limits

TITLE = "Debugging by Layer"
QUESTION = """For one symptom, which layer does it survive when the layer below is replaced?

The chapter's method: **replace the layer below the one you suspect, and ask
whether the symptom survives.** The layer list and the method are the book's
**proposal**, not a Pi procedure. This notebook demonstrates the method on
machinery that exists: the scripted provider and the session harness."""

CELLS = [
    ("md", heading(30, TITLE, QUESTION)),
    (
        "md",
        """## A note on what this chapter is

Chapter 30 has **no example directory and no ledger rows**. Its method is the
book's own formulation — a **proposal**, not a Pi contract — and the chapter's
only code fence is marked `documented-not-run`. This notebook therefore
**demonstrates** the method on machinery that does exist, instead of presenting a
scripted result as evidence about Pi.

The chain of thought is the chapter's; the code that runs it is the book's own
harness and the pinned packages.""",
    ),
    (
        "md",
        establishes(
            [
                "The **replacement test** can be run on real machinery: a scripted provider stands in for the model, and the symptom either survives or disappears.",
                "A symptom that **survives** a provider replacement is in the code above the model — the tool, the gate, or the loop.",
                "A symptom that **disappears** when the interface is replaced was presentation.",
                "The demonstration uses the same `faux` provider and `makeSession` harness as every other chapter; it adds no new mechanism.",
            ],
            [
                "**The layer list and the method are the book's proposal** (`ch30-lim3`), not documented by Pi.",
                "**The method is unvalidated against a set of real failures** — it is a heuristic that worked on the failures described, not a procedure.",
                "**The `onPayload` snippet in the chapter is `documented-not-run`** — it is a real `pi-ai` API, not exercised here.",
                "**No real model is called** — this demonstrates the method, not a diagnosis of any particular failure.",
            ],
        ),
    ),
    *setup_cells(
        30,
        mode="**Demonstrate** + Inspect — the replacement method run on the scripted provider and the session harness. The layer list is the book's proposal.",
        scope="`in_process_runtime`. The mechanism (faux provider, sessions) is Pi's; the method is the book's.",
    ),
    (
        "md",
        """## The suspects

```text
interface              terminal, print, JSON, RPC, SDK: how you watch it
host / application     extensions, settings, trust, context files, sessions
tool / effect          what a tool did, and what a gate let through
agent core             the loop: turns, hooks, events, queues
model access (pi-ai)   one request: auth, payload, stop reason, usage
provider               the service that answered
```

The one question: **replace the layer below the one you suspect. Does the
symptom survive?**""",
    ),
    (
        "code",
        'LAYERS = pinb.driver_source("ch30-layers.ts")\n'
        'layers = pinb.driver(LAYERS, label="ch30-layers", timeout=180)\n'
        'print(pinb.md_table(\n'
        '    ["case", "isError?", "text"],\n'
        '    [["tool throws", layers["symptom"]["throwingTool"]["isError"], layers["symptom"]["throwingTool"]["text"][:40]],\n'
        '     ["tool returns", layers["symptom"]["returningTool"]["isError"], layers["symptom"]["returningTool"]["text"][:40]],\n'
        '     ["gate blocks", layers["symptom"]["gate"]["isError"], layers["symptom"]["gate"]["text"][:40]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("a throwing tool produces a failed result the model can read",\n'
        '               layers["symptom"]["throwingTool"]["isError"], "isError: true"),\n'
        '    pinb.check("a returning tool produces a successful result",\n'
        '               not layers["symptom"]["returningTool"]["isError"], "isError: false"),\n'
        '    pinb.check("a gate block produces a failed result",\n'
        '               layers["symptom"]["gate"]["isError"], "isError: true"),\n'
        "])",
    ),
    (
        "md",
        """## Step 1: replace the provider

The scripted provider stands in for the model. If the symptom survives with a
scripted provider, the cause is **not the model** — it is the tool, the gate, or
the loop.""",
    ),
    (
        "code",
        'r = layers["replaceProvider"]\n'
        'print("Symptom survives with a scripted provider:", r["symptomSurvivesWithScriptedProvider"])\n'
        'print("Conclusion:", r["conclusion"])\n'
        'print()\n'
        'pinb.show_checks([\n'
        '    pinb.check("the failure survives the provider replacement",\n'
        '               r["symptomSurvivesWithScriptedProvider"] is True,\n'
        '               "symptom is above the model"),\n'
        "])",
    ),
    (
        "md",
        """## Step 2: replace the interface

The same command, run with a UI and without one. The symptom (a notification)
**disappears** without a UI — it was presentation, not the guard logic.""",
    ),
    (
        "code",
        'i = layers["replaceInterface"]\n'
        'print("With UI: notifications =", i["withUI"])\n'
        'print("No UI:   notifications =", i["noUI"])\n'
        'print()\n'
        'pinb.show_checks([\n'
        '    pinb.check("with a UI the command notifies",\n'
        '               len(i["withUI"]) > 0, "notification delivered"),\n'
        '    pinb.check("without a UI the notification disappears (presentation)",\n'
        '               len(i["noUI"]) == 0, "no notification"),\n'
        '    pinb.check("so the symptom was the interface, not the logic",\n'
        '               i["symptomDisappears"], "interface layer"),\n'
        "])",
    ),
    (
        "md",
        """## The decision diagram

```mermaid
flowchart TD
  S["a symptom"] --> Q1{"Survives with a scripted provider?"}
  Q1 -->|"no"| MODEL["model, credential or request"]
  Q1 -->|"yes"| Q2{"Survives in a bare Agent, no coding agent?"}
  Q2 -->|"no"| HOST["host or application"]
  Q2 -->|"yes"| Q3{"Survives with every hook removed?"}
  Q3 -->|"no"| HOOK["a hook or a gate"]
  Q3 -->|"yes"| CORE["the loop, or your own tools"]
```

*The diagram is the book's proposal. The demonstration above walks two of its
edges with real machinery.*""",
    ),
    (
        "md",
        """## Your turn: assign a symptom

**Predict first.** The model "keeps retrying". The tool returns an object saying
`{ failed: true }` rather than setting `isError: true`. Is that a failure the
model sees as failed?

**Then change one input.** In the demonstration, the gate blocks. Remove the
`tool_call` handler and re-run. Which layer's symptom disappears?

**Predict the boundary.** The chapter says the hardest failures are where two
layers each look correct. Give one: an effect with no cause in the transcript.
What else runs with the process's permissions (chapter 42)?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. { failed: true } without isError: true is NOT a failure to the model.")\n'
        'print("  2. Remove the gate: the block symptom disappears - it was the gate.")\n'
        'print("  3. An effect with no transcript cause: an extension, a postinstall, or an MCP server.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  throwing tool: isError={layers[\'symptom\'][\'throwingTool\'][\'isError\']}")\n'
        'print(f"  gate: isError={layers[\'symptom\'][\'gate\'][\'isError\']}")\n'
        'print(f"  symptom survives provider replacement: {layers[\'replaceProvider\'][\'symptomSurvivesWithScriptedProvider\']}")\n'
        'print(f"  interface symptom disappears without UI: {layers[\'replaceInterface\'][\'symptomDisappears\']}")\n'
        "print()\n"
        'assert layers["symptom"]["throwingTool"]["isError"]\n'
        'assert not layers["symptom"]["returningTool"]["isError"]\n'
        'assert layers["replaceProvider"]["symptomSurvivesWithScriptedProvider"]\n'
        'assert layers["replaceInterface"]["symptomDisappears"]\n'
        'print("held (demonstration): the replacement test assigns a symptom to a layer on real machinery")',
    ),
    (
        "md",
        """## Interpretation

The method is one question, asked of each layer in turn:

> **Replace the layer below the one you suspect. Does the symptom survive?**

| To test this layer… | …replace this | And look for |
|---|---|---|
| Your code above the model | the provider, with the faux provider | The symptom survives: it is your code or the loop |
| The agent loop | the coding agent, with a bare `Agent` | The symptom disappears: it is in the host |
| An extension | run with extensions off (`-ne`) | The symptom disappears: it is that extension |
| The interface | `--mode json` or the SDK | The symptom disappears: it was presentation |
| The provider | one request through `pi-ai` directly | The symptom survives with no agent: it is the model |

**Proposed, not documented.** The layer list and the method are this book's
formulation. They follow from the layers being separable (chapters 1 and 37) and
have not been validated against a set of real failures. Use them as a heuristic.

The artefacts cut across layers: `/debug` and `pi-debug.log`, `/bug`, `/session`,
`/hotkeys`, the startup header, and `pi --export`. Review any of them before
sharing — they can contain prompts, responses, tool output and file contents.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=30,
            mode="**Demonstrate** + Inspect — the replacement method run on the scripted provider and the session harness. The layer list is the book's proposal.",
            scope="`in_process_runtime`. The mechanism (faux provider, sessions) is Pi's; the method is the book's.",
            provenance=[
                "**Ran** `drivers/ch30-layers.ts`: real sessions demonstrating the replacement test (tool throws, tool returns, gate blocks, command with/without UI).",
                "**Read** `content/books/pi/30-chapter.md` — the layer list, the decision diagram, the artefacts table.",
            ],
            limits=[
                "**The layer list and the method are the book's proposal** (`ch30-lim3`), not documented by Pi.",
                "**The method is unvalidated against a set of real failures** — a heuristic, not a procedure.",
                "**The `onPayload` snippet is `documented-not-run`** — a real `pi-ai` API, not exercised here.",
                "**No real model is called** — no diagnosis of any particular failure is made.",
            ],
            unrun=[
                "The `onPayload` payload-logging snippet (documented, not run).",
                "`/debug`, `/bug`, `/session`, `/hotkeys`, `pi --export` (terminal artefacts, not run here).",
                "The bare-`Agent` replacement step (chapter 37 has the bare agent; this notebook does not re-run it).",
            ],
        ),
    ),
]