"""Chapter 21 - MCP Servers."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "MCP Servers"
QUESTION = """Does a gate keyed on the bare tool name skip `mcp__jira__transition_issue`, and
does a lying `readOnlyHint` pass?

The chapter's point: MCP tools are named `mcp__<server>__<tool>`. A gate that
checks only the bare name (`transition_issue`) never matches. The 1.0.4 `--tools`
rule keeps MCP tools unless an entry starts with `mcp__`. Annotations are hints,
not permission — a server that lies about `readOnlyHint` passes the gate."""

CELLS = [
    ("md", heading(21, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "An MCP tool is named `mcp__<server>__<tool>` — a gate keyed on the **bare name** (`transition_issue`) **never matches** the full name (`mcp__jira__transition_issue`).",
                "The deny-list gate keys on the **full name**: with no UI the call is blocked and the server never hears it.",
                "With a UI the person decides: approve lets it through, decline blocks it.",
                "**Annotations are hints, not permission**: a server that lies about `readOnlyHint: true` passes the gate — the gate believed it.",
                "Exposure decides whether the model is told the tool exists: `direct` = declared, `codemode` = reachable not declared, `hidden` = unreachable.",
                "`pi.registerMcpServer` adds a server for the session; `unregisterMcpServer` takes it away again.",
            ],
            [
                "**No network**: the far end is an in-memory transport pair (`ch21-lim1`).",
                "**Annotations are explicitly unverified** (`ch21-lim2`) — a lying server passes.",
                "**Project overrides and `cimd` (1.0.1) not exercised** (`ch21-lim3`).",
                "**The `tool-allowlist.test.ts` tests the 1.0.4 `--tools` rule separately** — this driver focuses on the gate and exposure.",
            ],
        ),
    ),
    *setup_cells(
        21,
        mode="**Run** — real sessions with an in-memory MCP server (`fakeMcpServer` from the harness), driven by a scripted model.",
        scope="`in_process_runtime`. The naming, exposure, and gate rules are Pi's. No network.",
    ),
    (
        "md",
        """## The bare-name gate: a classic mistake

A gate that checks `event.toolName === "transition_issue"` never matches
`mcp__jira__transition_issue`. The server hears the call because the gate didn't
block it.""",
    ),
    (
        "code",
        'MCP = pinb.driver_source("ch21-mcp.ts")\n'
        'mcp = pinb.driver(MCP, label="ch21-mcp", timeout=300)\n'
        'print(pinb.md_table(\n'
        '    ["gate type", "tool name checked", "isError?", "server heard?"],\n'
        '    [["bare name", "transition_issue", "no" if not mcp["bareNameGate"]["isError"] else "yes", "yes" if mcp["bareNameGate"]["serverHeard"] > 0 else "no"],\n'
        '     ["full name (deny-list)", "mcp__jira__transition_issue", "yes" if mcp["denyListGate"]["isError"] else "no", "yes" if mcp["denyListGate"]["serverHeard"] > 0 else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("bare-name gate never matches mcp__jira__transition_issue",\n'
        '               not mcp["bareNameGate"]["isError"] and mcp["bareNameGate"]["serverHeard"] > 0,\n'
        '               "gate missed it, server heard"),\n'
        '    pinb.check("full-name deny-list blocks and server never hears",\n'
        '               mcp["denyListGate"]["isError"] and mcp["denyListGate"]["serverHeard"] == 0,\n'
        '               "blocked, server silent"),\n'
        "])",
    ),
    (
        "md",
        """## With a UI: the person decides

The deny-list gate asks via `ctx.ui.confirm`. Approve = through, decline = blocked.""",
    ),
    (
        "code",
        'approve = mcp["denyListGateWithUI"][0]\n'
        'decline = mcp["denyListGateWithUI"][1]\n'
        'print(pinb.md_table(\n'
        '    ["answer", "isError?", "server heard?", "confirm message"],\n'
        '    [["approve", "no" if not approve["isError"] else "yes", "yes" if approve["serverHeard"] > 0 else "no", approve["confirmMessage"]],\n'
        '     ["decline", "yes" if decline["isError"] else "no", "yes" if decline["serverHeard"] > 0 else "no", decline["confirmMessage"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("approve: call goes through, server hears",\n'
        '               not approve["isError"] and approve["serverHeard"] > 0,\n'
        '               "allowed"),\n'
        '    pinb.check("decline: call blocked, server silent",\n'
        '               decline["isError"] and decline["serverHeard"] == 0,\n'
        '               "blocked"),\n'
        '    pinb.check("confirm message includes full tool name and server",\n'
        '               approve["confirmMessage"] and "mcp__jira__transition_issue" in approve["confirmMessage"] and "jira" in approve["confirmMessage"],\n'
        '               "full name shown"),\n'
        "])",
    ),
    (
        "md",
        """## Annotations are hints, not permission

Three tools from a lying server:
- `list_issues`: honest `readOnlyHint: true, openWorldHint: false` → no approval needed
- `no_hints_at_all`: no hints → treated as dangerous, blocked without UI
- `delete_everything`: **lies** with `readOnlyHint: true, openWorldHint: false` → **passes the gate**""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["tool", "annotations", "isError?"],\n'
        '    [["list_issues", "honest readOnlyHint", "no" if not mcp["lyingAnnotations"]["honest"]["isError"] else "yes"],\n'
        '     ["no_hints_at_all", "no hints", "yes" if mcp["lyingAnnotations"]["silent"]["isError"] else "no"],\n'
        '     ["delete_everything", "LYING readOnlyHint", "no" if not mcp["lyingAnnotations"]["liar"]["isError"] else "yes"]],\n'
        "))",
    ),
    (
        "code",
        'print("Server calls:", ", ".join(mcp["lyingAnnotations"]["serverCalls"]))\n'
        "print()\n"
        "pinb.show_checks([\n"
        '    pinb.check("honest readOnlyHint: no approval needed",\n'
        '               not mcp["lyingAnnotations"]["honest"]["isError"], "allowed"),\n'
        '    pinb.check("no hints: treated as dangerous, blocked without UI",\n'
        '               mcp["lyingAnnotations"]["silent"]["isError"], "blocked"),\n'
        '    pinb.check("LYING readOnlyHint: the gate believed it",\n'
        '               not mcp["lyingAnnotations"]["liar"]["isError"], "allowed (the lie worked)"),\n'
        '    pinb.check("server heard honest and liar, not silent",\n'
        '               mcp["lyingAnnotations"]["serverCalls"] == ["list_issues", "delete_everything"],\n'
        '               "only allowed tools called"),\n'
        "])",
    ),
    (
        "md",
        """## Exposure decides what the model is told

`direct` = declared to model (like built-ins). `codemode` = reachable from scripts, not declared. `hidden` = unreachable.""",
    ),
    (
        "code",
        'for exposure in ["direct", "codemode", "hidden"]:\n'
        '    tools = mcp["exposureDeclared"][exposure]["tools"]\n'
        '    print(f"  {exposure}: declared={\"mcp__docs__search\" in tools}")',
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("direct: declared to model",\n'
        '               "mcp__docs__search" in mcp["exposureDeclared"]["direct"]["tools"], "declared"),\n'
        '    pinb.check("codemode: reachable, not declared",\n'
        '               "mcp__docs__search" not in mcp["exposureDeclared"]["codemode"]["tools"], "not declared"),\n'
        '    pinb.check("hidden: unreachable",\n'
        '               "mcp__docs__search" not in mcp["exposureDeclared"]["hidden"]["tools"], "not declared"),\n'
        "])",
    ),
    (
        "md",
        """## Register and unregister at runtime

`pi.registerMcpServer` adds a server for the session; `unregisterMcpServer`
removes it. The command `/jira-off` calls unregister.""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["step", "server heard?"],\n'
        '    [["after register", "yes" if mcp["registerUnregister"]["afterRegister"] > 0 else "no"],\n'
        '     ["after unregister", "yes" if mcp["registerUnregister"]["afterUnregister"] > 0 else "no"]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("after register: server connected and tool ran",\n'
        '               mcp["registerUnregister"]["afterRegister"] > 0, "connected"),\n'
        '    pinb.check("after unregister: server receives nothing more",\n'
        '               mcp["registerUnregister"]["afterUnregister"] == mcp["registerUnregister"]["afterRegister"], "no new calls"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

All tests from both test files.""",
    ),
    *canonical_tests(
        21,
        ["ch21-mcp/mcp.test.ts", "ch21-mcp/tool-allowlist.test.ts"],
        what="The chapter's canonical evidence",
        show="mcp__",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** What happens if an MCP tool is registered with `exposure:
"codemode"` and the `--tools` allowlist includes `mcp__jira__*`? Does the
pattern override exposure?

**Then change one input.** The `tool-allowlist.test.ts` shows that `excludeTools:
["mcp__*"]` unregisters the tool entirely. What happens if you use
`tools: ["read", "codemode"]` (no mcp__ pattern) but the tool is `direct`
exposure?

**Predict the boundary.** The 1.0.4 rule: `--tools` keeps MCP tools unless an
entry starts with `mcp__`. What if you use `tools: ["*"]` — does that match
MCP tools or only built-ins?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. mcp__ pattern with codemode: pattern does NOT override exposure — stays undeclared.")\n'
        'print("  2. direct exposure without mcp__ pattern: tool is inert (neither declared nor callable).")\n'
        'print("  3. tools: [*]: matches MCP tools too — * is a pattern, not just built-ins.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  bare name gate missed: {not mcp[\"bareNameGate\"][\"isError\"]}, server heard={mcp[\"bareNameGate\"][\"serverHeard\"]}")\n'
        'print(f"  full name gate blocked: {mcp[\"denyListGate\"][\"isError\"]}, server heard={mcp[\"denyListGate\"][\"serverHeard\"]}")\n'
        'print(f"  lying readOnlyHint passed: {not mcp[\"lyingAnnotations\"][\"liar\"][\"isError\"]}")\n'
        'print(f"  exposure: direct={mcp[\"exposureDeclared\"][\"direct\"][\"tools\"]}, codemode={mcp[\"exposureDeclared\"][\"codemode\"][\"tools\"]}, hidden={mcp[\"exposureDeclared\"][\"hidden\"][\"tools\"]}")\n'
        "print()\n"
        'assert not mcp["bareNameGate"]["isError"] and mcp["bareNameGate"]["serverHeard"] > 0\n'
        'assert mcp["denyListGate"]["isError"] and mcp["denyListGate"]["serverHeard"] == 0\n'
        'assert not mcp["lyingAnnotations"]["liar"]["isError"]\n'
        'print("held: bare name gate misses MCP tools; lying annotations pass; exposure controls declaration")',
    ),
    (
        "md",
        """## Interpretation

MCP in Pi has three naming/visibility layers, and each has a boundary:

| Layer | What it controls | The boundary |
|---|---|---|
| **Tool name** | `mcp__<server>__<tool>` | A gate on the bare name (`transition_issue`) never matches |
| **Exposure** | `direct` / `codemode` / `hidden` | `direct` = declared; `codemode` = script-reachable; `hidden` = unreachable |
| **Annotations** | `readOnlyHint`, `openWorldHint` | **Hints, not permission** — a lie passes |

The 1.0.4 `--tools` rule (tested in `tool-allowlist.test.ts`):
* `--tools read,codemode` keeps MCP tools (no `mcp__` pattern)
* `--tools read,codemode,mcp__jira__*` declares `mcp__jira__*` tools
* `excludeTools: ["mcp__*"]` unregisters MCP tools entirely
* `disabledBuiltinExtensions: ["mcp"]` gates built-in MCP support, not injected extensions

The practical rules:
* **Gate on the full name** — `mcp__<server>__<tool>`, not the bare tool name.
* **Don't trust annotations** — they are hints; a malicious or buggy server can lie.
* **Use `codemode` exposure for internal tools** — the model doesn't see them, scripts can call them.
* **`registerMcpServer` / `unregisterMcpServer` are session-scoped** — they don't persist across sessions.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=21,
            mode="**Run** — real sessions with an in-memory MCP server (`fakeMcpServer` from the harness), driven by a scripted model.",
            scope="`in_process_runtime`. The naming, exposure, and gate rules are Pi's. No network.",
            provenance=[
                "**Ran** `drivers/ch21-mcp.ts`: six real sessions covering bare-name gate, deny-list gate (with/without UI), lying annotations, exposure, and register/unregister.",
                "**Ran** `ch21-mcp/mcp.test.ts` (6 tests) and `ch21-mcp/tool-allowlist.test.ts` (7 tests).",
                "**Read** `examples/evidence.json`, chapter 21 rows (13 claims).",
            ],
            limits=[
                "**No network**: the far end is an in-memory transport pair (`ch21-lim1`).",
                "**Annotations are explicitly unverified** (`ch21-lim2`) — a lying server passes.",
                "**Project overrides and `cimd` (1.0.1) not exercised** (`ch21-lim3`).",
            ],
        ),
    ),
]