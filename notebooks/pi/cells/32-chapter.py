"""Chapter 32 - Headless Pi."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Headless Pi"
QUESTION = """With a failed response, is the failure an exit status or only in the stream — and
does `--tools` stop `bash`?

The chapter's point: print mode is a Unix program (exit status, stderr), JSON mode
is a stream (exit 0, failure recorded in the stream), and `--tools` is a real
allowlist — a `bash` call the model makes when `bash` is not in the list gets a
failed result and nothing runs."""

CELLS = [
    ("md", heading(32, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "Print mode: the whole interface is the final text on stdout; a **failed** final response exits non-zero with the message on **stderr** and nothing on stdout.",
                "JSON mode: the same failure is in the event stream (`stopReason: error`) and the **exit status is 0**.",
                "With stdin and stdout redirected and no mode given, Pi **chooses print mode**.",
                "**Piped stdin is prepended** to the first prompt.",
                "`@path` includes a text file in the first prompt; `--` lets a prompt begin with a dash.",
                "`--tools` is a **real allowlist**: a `bash` call gets a failed result and **nothing runs**.",
                "`--no-session` writes no session file; without it a run against a real directory does.",
            ],
            [
                "**The four-tool claim is about built-ins.** As of 1.0.4 `--tools` no longer removes MCP tools, so `--no-mcp` is part of the command, not a footnote.",
                "**The model is scripted** — this measures the CLI's plumbing, not model behaviour.",
                "**No real credential or network** is used.",
            ],
        ),
    ),
    *setup_cells(
        32,
        mode="**Run** — the shipped binary as a child process with a scripted model, offline.",
        scope="`shipped_binary`. The CLI's contract is the real one.",
    ),
    (
        "md",
        """## Baseline: print vs JSON on the same failure""",
    ),
    (
        "code",
        'HEADLESS = pinb.driver_source("ch32-headless.ts")\n'
        'headless = pinb.driver(HEADLESS, label="ch32-headless", timeout=420)\n'
        'p, j = headless["print"], headless["json"]\n'
        'print(pinb.md_table(\n'
        '    ["run", "exit", "stdout", "stderr"],\n'
        '    [["print success", p["okExit"], repr(p["okStdout"]), "-"],\n'
        '     ["print failure", p["badExit"], "(empty)" if p["badStdoutEmpty"] else "(non-empty)", "has message" if p["badStderrHasMessage"] else "-"],\n'
        '     ["JSON failure", j["badExit"], f"stopReason={j[\'stopReason\']}", "-"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("print success exits 0 with the answer on stdout",\n'
        '               p["okExit"] == 0 and p["okStdout"] == "the final answer\\n", "exit 0, answer"),\n'
        '    pinb.check("print failure exits non-zero and writes nothing to stdout",\n'
        '               p["badExit"] != 0 and p["badStdoutEmpty"], "non-zero, stdout empty"),\n'
        '    pinb.check("the failure message is on stderr",\n'
        '               p["badStderrHasMessage"], "message on stderr"),\n'
        '    pinb.check("JSON failure exits 0 with the failure in the stream",\n'
        '               j["badExit"] == 0 and j["stopReason"] == "error", "exit 0, stopReason error"),\n'
        "])",
    ),
    (
        "md",
        """## Prompt inputs: implicit print, piped stdin, `@path`, `--`""",
    ),
    (
        "code",
        'i, piped, at, dash = headless["implicit"], headless["piped"], headless["atPath"], headless["dash"]\n'
        'print(pinb.md_table(\n'
        '    ["input", "observed"],\n'
        '    [["implicit print mode", repr(i["stdout"])],\n'
        '     ["piped stdin first", "yes" if piped["addedBeforePrompt"] else "no"],\n'
        '     ["@path included", "yes" if at["includesMarker"] else "no"],\n'
        '     ["-- prompt kept", "yes" if dash["includesDashPrompt"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("redirected, no mode given: Pi chooses print mode",\n'
        '               i["exit"] == 0 and i["stdout"] == "implicit\\n", "implicit print"),\n'
        '    pinb.check("piped stdin comes before the prompt", piped["addedBeforePrompt"], "stdin first"),\n'
        '    pinb.check("@path includes the file", at["includesMarker"], "marker present"),\n'
        '    pinb.check("-- lets a prompt begin with a dash", dash["includesDashPrompt"], "dash prompt kept"),\n'
        "])",
    ),
    (
        "md",
        """## `--tools` is a real allowlist""",
    ),
    (
        "code",
        'n, d = headless["narrowed"], headless["defaultTools"]\n'
        'print(pinb.md_table(\n'
        '    ["run", "bash result isError?", "ran.flag created?"],\n'
        '    [["--tools read,grep,find,ls", n["isError"], "yes" if n["ranFlagExists"] else "no"],\n'
        '     ["default tools", "n/a", "yes" if d["ranFlagExists"] else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("--tools makes a bash request a failed result",\n'
        '               n["isError"] is True, "isError true"),\n'
        '    pinb.check("and nothing runs (no ran.flag)",\n'
        '               not n["ranFlagExists"], "no side effect"),\n'
        '    pinb.check("the default tool set can run bash",\n'
        '               d["ranFlagExists"], "ran.flag created"),\n'
        "])",
    ),
    (
        "md",
        """## Sessions""",
    ),
    (
        "code",
        's = headless["session"]\n'
        'print(pinb.md_table(\n'
        '    ["run", "session file written?"],\n'
        '    [["--no-session (default in this harness)", "no" if s["noSessionDir"] else "yes"],\n'
        '     ["session: true", f"{s[\'keptSessionFiles\']} .jsonl file(s)"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("a run with no session writes no session directory",\n'
        '               s["noSessionDir"], "no sessions dir"),\n'
        '    pinb.check("a session run writes exactly one .jsonl",\n'
        '               s["keptSessionFiles"] == 1, "one file"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

All ten shipped-binary tests.""",
    ),
    *canonical_tests(
        32,
        "ch32-headless/headless.test.ts",
        what="The chapter's canonical evidence (shipped binary)",
        show="mode",
        timeout=420,
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** `--tools read,grep,find,ls` blocks `bash`. Does it also block
`edit` and `write`?

**Then change one input.** Add `--no-mcp` to the `--tools` run. What changes at
1.0.4, where `--tools` no longer removes MCP tools?

**Predict the boundary.** Print mode exits non-zero on a failure. What exit status
does a *successful* run with a non-empty `errorMessage` on the message return?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. --tools read,grep,find,ls also blocks edit and write - they are not in the list.")\n'
        'print("  2. --no-mcp removes MCP tools; --tools alone keeps them as of 1.0.4.")\n'
        'print("  3. A successful run exits 0 regardless of a message errorMessage.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  print: ok exit={p[\'okExit\']}, bad exit={p[\'badExit\']}, bad stdout empty={p[\'badStdoutEmpty\']}")\n'
        'print(f"  JSON failure: exit={j[\'badExit\']}, stopReason={j[\'stopReason\']}")\n'
        'print(f"  --tools: isError={n[\'isError\']}, ran.flag={n[\'ranFlagExists\']}")\n'
        "print()\n"
        'assert p["okExit"] == 0 and p["badExit"] != 0 and p["badStdoutEmpty"]\n'
        'assert j["badExit"] == 0 and j["stopReason"] == "error"\n'
        'assert n["isError"] is True and not n["ranFlagExists"] and d["ranFlagExists"]\n'
        'print("held: print is a Unix program, JSON is a stream, --tools is a real allowlist")',
    ),
    (
        "md",
        """## Interpretation

Headless Pi has three contracts, and the chapter shows each:

| Mode | Answer | Failure | Sessions |
|---|---|---|---|
| **print** | Final text on stdout | Non-zero exit, message on stderr | `--no-session` or default |
| **JSON** | Event stream | Exit 0, `stopReason: error` in the stream | as configured |
| **implicit** | print (when redirected, no flag) | as print | as configured |

Inputs:
* **Piped stdin** is prepended to the first prompt.
* **`@path`** includes a file's contents.
* **`--`** ends option parsing so a prompt can start with a dash.

The allowlist:
* `--tools read,grep,find,ls` — a `bash` call gets a failed result and nothing runs.
* As of **1.0.4**, `--tools` no longer removes MCP tools; add `--no-mcp`.

Practical rules:
1. **Print for scripts** — the exit status is the contract.
2. **JSON for observers** — the failure is a record, not a status.
3. **`--tools` for capability control** — it is an allowlist, not a hint.
4. **`--no-session` for one-shot work** — no file is written.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=32,
            mode="**Run** — the shipped binary as a child process with a scripted model, offline.",
            scope="`shipped_binary`. The CLI's contract is the real one.",
            provenance=[
                "**Ran** `drivers/ch32-headless.ts`: nine shipped-binary runs (print success/failure, JSON failure, implicit mode, piped stdin, `@path`, `--`, `--tools`, default tools, sessions).",
                "**Ran** `ch32-headless/headless.test.ts` (10 tests).",
                "**Read** `examples/evidence.json`, chapter 32 rows (10 claims).",
            ],
            limits=[
                "**As of 1.0.4 `--tools` no longer removes MCP tools** — `--no-mcp` is part of the command.",
                "**The model is scripted** — the CLI's plumbing is exercised, not model behaviour.",
            ],
        ),
    ),
]