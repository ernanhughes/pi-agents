"""Chapter 06 - The Built-In Tools."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "The Built-In Tools"
QUESTION = """What tools does a plain Pi session actually have, and **what does
`--tools` remove?**

The chapter has no example directory of its own — it deliberately delegates. What
it does have is a boundary worth checking: registered versus active versus declared
to the model, and the difference between a *narrowed* tool set and a *gated* one."""

CELLS = [
    ("md", heading(6, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "A default session registers **eight** tools and declares **four** to the "
                "model. The four that are declared are `read, bash, edit, write` — the "
                "`defaultTools` default.",
                "`--tools read,grep,find,ls` against the shipped binary makes a model request "
                "for `bash` come back as a **failed tool result**, and the command never "
                "runs. The default set runs the same command and creates the file.",
                "`defaultTools` in a project file **amends** when every entry is `+name` or "
                "`-name`, and **replaces** when any entry is a plain name.",
                "Each registered tool carries `exposure` and `annotations`, and those are "
                "readable from a live session.",
            ],
            [
                "**No MCP server is configured anywhere in this notebook.** As of 1.0.4 "
                "`--tools` does not remove MCP tools unless an entry starts with `mcp__`, so "
                "the four-tool result here is a statement about built-ins. Chapter 21 "
                "exercises the MCP case with a real in-memory server.",
                "**Tool descriptions, the codemode output limit and `tools.read()` on an "
                "image** are named by the chapter and not exercised here.",
                "**`-nt` / `-nbt` / `-xt` variants and the reload trap** are explicitly not "
                "run, by the chapter's own account.",
                "**No measurement** of codemode's context or latency effect for any workload.",
            ],
        ),
    ),
    *setup_cells(
        6,
        mode="**Run** — a live session's tool inventory, and the shipped binary with `--tools`.",
        scope="`in_process_runtime` for the inventory; `shipped_binary` for the narrowing. The "
        "provider is scripted.",
    ),
    (
        "md",
        """## Baseline: what a plain session has

Three sets, and the difference between them is the whole chapter:

* **registered** — every tool the runtime knows about;
* **active** — the subset in force for this session;
* **declared** — what the provider is told, which is the active set rendered into
  the system message.

The driver is `notebooks/pi/drivers/ch06-inventory.ts`. It is a real file in this
repository, so you can read it before running it.""",
    ),
    (
        "code",
        'INVENTORY = pinb.driver_source("ch06-inventory.ts")\n'
        'tools = pinb.driver(INVENTORY, label="ch06-inventory", timeout=240)\n'
        "print(pinb.md_table(\n"
        '    ["tool", "exposure", "readOnlyHint", "registered", "active", "declared to the model"],\n'
        '    [[t["name"], t["exposure"], str(t["readOnlyHint"]).lower(), "yes",\n'
        '      "yes" if t["name"] in tools["default"]["active"] else "-",\n'
        '      "yes" if t["name"] in tools["default"]["declared"] else "-"]\n'
        '     for t in tools["default"]["registered"]],\n'
        "))\n"
        'print()\n'
        'print(pinb.table(\n'
        '    ["session", "registered", "active", "declared"],\n'
        '    [["default", len(tools["default"]["registered"]), len(tools["default"]["active"]), len(tools["default"]["declared"])],\n'
        '     ["tools: read,grep,find,ls", len(tools["narrowed"]["registered"]), len(tools["narrowed"]["active"]), len(tools["narrowed"]["declared"])]],\n'
        '    indent="",\n'
        "))",
    ),
    (
        "code",
        'd, n = tools["default"], tools["narrowed"]\n'
        'meta = lambda s: {t["name"]: (t["exposure"], t["readOnlyHint"]) for t in s["registered"]}\n'
        "\n"
        "pinb.show_checks([\n"
        '    pinb.check("the default declared set is read, bash, edit, write",\n'
        '               d["declared"] == ["read", "bash", "edit", "write"], ", ".join(d["declared"])),\n'
        '    pinb.check("a default session registers more tools than it declares",\n'
        '               len(d["registered"]) > len(d["declared"]),\n'
        '               f"{len(d[\'registered\'])} registered, {len(d[\'declared\'])} declared"),\n'
        '    pinb.check("every declared tool is active",\n'
        '               set(d["declared"]) <= set(d["active"]), "declared is a subset of active"),\n'
        '    pinb.check("every active tool is registered",\n'
        '               set(d["active"]) <= set(meta(d)), "active is a subset of registered"),\n'
        '    pinb.check("narrowing with tools: removes from registration too",\n'
        '               n["declared"] == ["read", "grep", "find", "ls"] and len(n["registered"]) == 4,\n'
        '               f"declared {n[\'declared\']}, registered {len(n[\'registered\'])}"),\n'
        '    pinb.check("narrowing does not change the metadata of a kept tool",\n'
        '               meta(n) == {k: v for k, v in meta(d).items() if k in meta(n)},\n'
        '               "exposure and annotations are unchanged for the four kept tools"),\n'
        "])",
    ),
    (
        "md",
        """## Experiment: does a narrowed agent actually refuse?

A registered tool that is inactive is one thing; the question is what a **model
that asks for it anyway** receives. This runs the shipped binary: a scripted model
calls `bash`, and the driver reports both the tool result and whether the command
left any trace on disk.

That second half matters. A failed tool result and a command that ran and failed
look the same in a transcript and are different in the world.""",
    ),
    (
        "code",
        'NARROWED = pinb.driver_source("ch06-narrowed.ts")\n'
        'narrow = pinb.driver(NARROWED, label="ch06-narrowed", timeout=300)\n'
        "print(pinb.md_table(\n"
        '    ["--tools", "tools declared to the model", "model asked for", "result", "file on disk?"],\n'
        '    [[k, ", ".join(v["declaredTools"] or []), v["toolName"] or "-",\n'
        '      "error" if v["isError"] else ("ok" if v["isError"] is False else "no tool call"),\n'
        '      "YES" if v["fileCreated"] else "no"] for k, v in narrow.items()],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("with the default set, bash runs and leaves a file",\n'
        '               narrow["default"]["fileCreated"] and narrow["default"]["isError"] is False,\n'
        '               "ran.flag exists"),\n'
        '    pinb.check("--tools read,grep,find,ls does not declare bash",\n'
        '               "bash" not in (narrow["narrowed"]["declaredTools"] or []),\n'
        '               ", ".join(narrow["narrowed"]["declaredTools"] or [])),\n'
        '    pinb.check("a model that asks for a narrowed tool gets an error result",\n'
        '               narrow["narrowed"]["isError"] is True, "isError: true"),\n'
        '    pinb.check("and the command never ran",\n'
        '               not narrow["narrowed"]["fileCreated"], "ran.flag absent"),\n'
        '    pinb.check("--no-mcp does not change the built-in narrowing",\n'
        '               narrow["narrowedWithNoMcp"]["isError"] is True and not narrow["narrowedWithNoMcp"]["fileCreated"],\n'
        '               "same result; there are no MCP servers in this notebook"),\n'
        "])",
    ),
    (
        "md",
        """## Contrasting case: narrowing by configuration, not by flag

`--tools` is the command line. `defaultTools` is the file, and it has a grammar
that is easy to get wrong: **a project list of only `+name` / `-name` entries
amends** the user's selection; **a list containing any plain name replaces** it
outright. Within one list, plain names form the selection and `+`/`-` then apply
in order.

That is the chapter 6 / chapter 7 shared evidence, and it runs here because
chapter 6 has no example directory of its own.""",
    ),
    *canonical_tests(
        6,
        ["ch07-settings/settings.test.ts", "ch32-headless/headless.test.ts"],
        what="The evidence chapter 6 delegates to",
        show="tools",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** `defaultTools: ["+grep", "+find", "+ls"]` on top of a user
selection of `["read", "bash"]`. What is the result — and what if the project list
were `["read", "powershell"]` instead?

**Then change one input.** `TOOLS` below is what gets declared to the model. Try
`["bash"]` alone, then `["bash", "powershell"]`.

**Predict the boundary.** Which single entry turns an amendment into a
replacement?""",
    ),
    (
        "code",
        'TOOLS = ["bash"]\n'
        'USER_SELECTION = ["read", "bash"]\n'
        "\n"
        "\n"
        "def merge_default_tools(user: list[str], project: list[str]) -> list[str]:\n"
        '    """The documented grammar, restated so the amendment/replace rule is visible.\n'
        "\n"
        "    This is the rule chapter 6 states, not an implementation of Pi. The\n"
        "    authoritative check is Pi's own SettingsManager, asserted by\n"
        "    ch07-settings/settings.test.ts, which ran above.\n"
        '    """\n'
        "    if not project:\n"
        "        return list(user)\n"
        '    if any(e and e[0] not in "+-" for e in project):\n'
        "        return list(project)\n"
        "    out = list(user)\n"
        "    for entry in project:\n"
        '        name = entry[1:]\n'
        '        if entry.startswith("+"):\n'
        "            if name not in out:\n"
        "                out.append(name)\n"
        "        elif name in out:\n"
        "            out.remove(name)\n"
        "    return out\n"
        "\n"
        'for project in (["+grep", "+find", "+ls"], ["read", "powershell"], ["read", "bash", "-bash", "+grep"]):\n'
        '    print(f"  user {USER_SELECTION} + project {project} -> {merge_default_tools(USER_SELECTION, project)}")\n'
        'print()\n'
        'print("predicted declared set for TOOLS =", TOOLS)\n'
        "\n"
        "import json as _json\n"
        "\n"
        "again = pinb.driver(INVENTORY, label=\"ch06-exercise\", timeout=240, env={\"NB_TOOLS\": _json.dumps(TOOLS)})\n"
        'print("observed declared set:  ", again["narrowed"]["declared"])\n'
        "\n"
        'assert again["narrowed"]["declared"] == TOOLS, "the declared set is what was asked for, in order"\n'
        'assert set(TOOLS) <= set(meta(again["narrowed"])), "every declared tool is also registered"\n'
        'print("\\nheld: the declared set is the selection, not a filter over a larger one")',
    ),
    (
        "md",
        """## Interpretation: three mechanisms that are easy to confuse

| Mechanism | Where | What it stops | What it does **not** stop |
|---|---|---|---|
| `--tools` / `tools:` | command line / settings | the model being *told* about the tool | nothing — the tool was never given |
| `defaultTools` | a settings file | the same, from configuration | ditto |
| a `tool_call` gate | an extension (chapters 11, 16, 17, 21) | the tool **running** | the model still being offered it |

Only the third is a permission. The first two are menu control. A reader who
treats `--tools` as a safety mechanism has misread which boundary it is — which is
the mistake chapter 42 spends its length correcting.

### What this chapter does not settle

* **MCP tools and `--tools` since 1.0.4.** The narrowing above is a statement about
  built-ins; `--tools` keeps MCP tools unless an entry starts with `mcp__`. Chapter
  21 runs that case with a real in-memory MCP server.
* **Codemode.** Named, version-marked (1.0.1 for the output limit, 1.0.3 for
  `image()` writing to a temp file, 1.0.4 for `tools.read()` resolving to an image
  block), and not exercised here.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=6,
            mode="**Run** — a live session's tool inventory, three runs of the shipped binary "
            "with and without `--tools`, and the two test files this chapter delegates to.",
            scope="`in_process_runtime` plus `shipped_binary`. This chapter has no example "
            "directory of its own, so it has no ledger rows; that is why the two borrowed "
            "test files are named explicitly above.",
            provenance=[
                "**Ran** `makeSession` twice and read `getAllTools()`, `getActiveToolNames()`, "
                "`getCallableToolNames()` and the system message the provider received "
                "(`drivers/ch06-inventory.ts`).",
                "**Ran** the shipped binary three times, offline, each in a fresh temporary "
                "working directory, checking both the tool result and the filesystem "
                "(`drivers/ch06-narrowed.ts`).",
                "**Ran** `ch07-settings/settings.test.ts` and `ch32-headless/headless.test.ts`.",
                "**Read** `examples/evidence.json`: chapter 6 has **no rows**, which is "
                "consistent with the chapter delegating its evidence.",
            ],
            limits=[
                "**No MCP server exists in this notebook**, so `--tools` behaves as a "
                "built-in filter here. The 1.0.4 rule that `--tools` no longer removes MCP "
                "tools is therefore *not* exercised; chapter 21 is where it is.",
                "**The amendment/replace grammar shown in the exercise is the chapter's rule "
                "restated**, not an implementation. The authoritative check is the "
                "`SettingsManager` assertions in `settings.test.ts`, which ran above.",
                "**Tool metadata is reported, not trusted.** `annotations.readOnlyHint` is a "
                "hint the tool declares about itself; chapter 21's annotation experiment is "
                "the demonstration that a server can lie about it.",
            ],
        ),
    ),
]