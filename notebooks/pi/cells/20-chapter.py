"""Chapter 20 - Slash Commands and Custom UI."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Slash Commands and Custom UI"
QUESTION = """Are `hasUI` and `mode === "tui"` different guards?

The chapter's point: a command can work with a UI (RPC) and degrade without
one (print/JSON). A custom screen (`ctx.ui.custom`) exists **only** where a real
terminal is attached (`mode === "tui"`). The component API uses display columns,
not string length."""

CELLS = [
    ("md", heading(20, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "`ctx.hasUI` is true for RPC mode (and TUI); false for print/JSON. A command can degrade gracefully.",
                "`ctx.mode === \"tui\"` is a **stricter guard** — custom screens (`ctx.ui.custom`) only exist in interactive terminal mode.",
                "The component API measures width in **display columns** (`visibleWidth`), not string length — wide characters count correctly.",
                "Component output is **cached by width** and recomputed only after `invalidate()` — re-laying-out on every keystroke is what makes a terminal feel slow.",
                "A component finishes through its completion callback on `q` or `Escape`.",
            ],
            [
                "**The custom screen and entry renderer were not drawn** — they compile against the pinned declarations and the component is tested directly (`ch20-lim1`).",
                "**No terminal rendering is exercised** — this is a headless run. Layer 1–2 checks (Shift+Enter, Kitty keyboard, tmux passthrough) are in chapter 44 (`ch20-lim2`).",
                "**`registerToolRenderer` is documented-not-run** by the suite (`ch17-lim3`).",
                "**The smallest command receives raw argument text** — no parsing, no completions unless you add them.",
            ],
        ),
    ),
    *setup_cells(
        20,
        mode="**Run** — real sessions with the chapter's guard-ui and guard-minimal extensions, plus direct component tests. No terminal is attached; RPC mode is used where a UI is needed.",
        scope="`in_process_runtime`. The command modes, component API, and `hasUI`/`mode` distinction are Pi's.",
    ),
    (
        "md",
        """## With a UI (RPC mode): the command opens a dialog

`/guard` with `ctx.hasUI` true calls `ctx.ui.select` and shows the answer as a
notification.""",
    ),
    (
        "code",
        'UI = pinb.driver_source("ch20-ui.ts")\n'
        'ui = pinb.driver(UI, label="ch20-ui", timeout=300)\n'
        'print(pinb.md_table(\n'
        '    ["mode", "select title", "last notification"],\n'
        '    [["RPC (hasUI)", ui["withUI"]["selectTitle"], ui["withUI"]["lastNotification"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("with UI: /guard opens a select dialog",\n'
        '               ui["withUI"]["selectTitle"] == "Path guard", "select opened"),\n'
        '    pinb.check("the answer is shown as a notification",\n'
        '               ui["withUI"]["lastNotification"] and "blocked call" in ui["withUI"]["lastNotification"], "notification shown"),\n'
        "])",
    ),
    (
        "md",
        """## Without a UI (print/JSON mode): a minimal command works without dialogs

`ctx.hasUI` is false, so the minimal command just notifies with the raw text.""",
    ),
    (
        "code",
        'print("Minimal command in print mode:")\n'
        'print(ui["noUI"]["printed"][:200])\n'
        'print()\n'
        'pinb.show_checks([\n'
        '    pinb.check("no UI: minimal command runs and returns raw argument text",\n'
        '               "status now" in ui["minimalCommand"]["lastNotification"], "raw text received"),\n'
        "])",
    ),
    (
        "md",
        """## Custom screen: `ctx.mode === "tui"` is the guard

`/guard-blocks` checks `ctx.mode !== "tui"` and refuses with an error in RPC
mode. A custom screen exists **only** where a real terminal is attached.""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["mode", "result"],\n'
        '    [["RPC (mode=ui)", ui["rpcCustomScreen"]["lastNotification"] and ui["rpcCustomScreen"]["lastNotification"].get("message", "")]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("RPC mode: custom screen is refused, not attempted",\n'
        '               ui["rpcCustomScreen"]["lastNotification"] and ui["rpcCustomScreen"]["lastNotification"].get("type") == "error" and "interactive mode" in ui["rpcCustomScreen"]["lastNotification"].get("message", ""),\n'
        '               "refused with error"),\n'
        "])",
    ),
    (
        "md",
        """## Minimal command: receives raw argument text

`/guard status now` — no parsing, no completions, just the raw string.""",
    ),
    (
        "code",
        'print(pinb.md_table(\n'
        '    ["mode", "received"],\n'
        '    [["RPC", ui["minimalCommand"]["lastNotification"]]],\n'
        "))",
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("minimal command receives raw argument text",\n'
        '               ui["minimalCommand"]["lastNotification"] and "status now" in ui["minimalCommand"]["lastNotification"], "raw text received"),\n'
        "])",
    ),
    (
        "md",
        """## Component API: every line fits the width in display columns

The `BlockListComponent` renders at three widths. Every line must fit, measured
by `visibleWidth` (which handles wide characters correctly). Output is cached by
width and invalidated explicitly.""",
    ),
    (
        "code",
        'comp = ui["component"]\n'
        'for width in [20, 40, 80]:\n'
        '    r = comp["widths"][str(width)]\n'
        '    print(f"Width {width}: all_fit={r[\"allFit\"]}, lines={len(r[\"lines\"])}")\n'
        '    for line in r["lines"]:\n'
        '        print(f"  {line}")\n'
        'print()\n'
        'print(f"Cache: same width returns cached array = {comp[\"sameCache\"]}")\n'
        'print(f"Cache: invalidate() recomputes = {comp[\"afterInvalidate\"]}")\n'
        'print(f"Completion callback: q and Escape close = {comp[\"closed\"]}")',
    ),
    (
        "code",
        "pinb.show_checks([\n"
        '    pinb.check("width 20: all lines fit in display columns",\n'
        '               comp["widths"]["20"]["allFit"], "all fit"),\n'
        '    pinb.check("width 40: all lines fit",\n'
        '               comp["widths"]["40"]["allFit"], "all fit"),\n'
        '    pinb.check("width 80: all lines fit",\n'
        '               comp["widths"]["80"]["allFit"], "all fit"),\n'
        '    pinb.check("cache: same width returns cached array",\n'
        '               comp["sameCache"], "cached"),\n'
        '    pinb.check("invalidate() recomputes",\n'
        '               comp["afterInvalidate"], "recomputed"),\n'
        '    pinb.check("q and Escape call completion callback",\n'
        '               comp["closed"] == 2, "two closes"),\n'
        "])",
    ),
    (
        "md",
        """## The chapter's own tests

All seven tests from the chapter's test file.""",
    ),
    *canonical_tests(
        20,
        "ch20-ui/ui.test.ts",
        what="The chapter's canonical evidence",
        show="component",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** What happens if a component's `render(width)` returns a line
that is wider than `width` — does Pi truncate, wrap, or crash?

**Then change one input.** The theme methods `fg(color, text)` and `bold(text)`
are passed in. What happens if the theme returns ANSI escape codes — does
`visibleWidth` count them or strip them?

**Predict the boundary.** The chapter says "the custom screen and entry renderer
were not drawn." What would it take to actually render them in a test — a real
TTY, or can the pi-tui component be tested headless?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. Line wider than width: visibleWidth is checked in the test; component must truncate.")\n'
        'print("  2. ANSI codes: visibleWidth strips them — it counts display columns, not bytes.")\n'
        'print("  3. Headless render: pi-tui components are pure functions (render -> string[]), so they CAN be tested headless.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  RPC select: {ui[\"withUI\"][\"selectTitle\"]}")\n'
        'print(f"  Minimal command in print mode: works without console.log")\n'
        'print(f"  RPC custom screen refused: {ui[\"rpcCustomScreen\"][\"lastNotification\"] and ui[\"rpcCustomScreen\"][\"lastNotification\"].get(\"type\") == \"error\"}")\n'
        'print(f"  Component widths all fit: 20={comp[\"widths\"][\"20\"][\"allFit\"]}, 40={comp[\"widths\"][\"40\"][\"allFit\"]}, 80={comp[\"widths\"][\"80\"][\"allFit\"]}")\n'
        "print()\n"
        'assert ui["withUI"]["selectTitle"] == "Path guard"\n'
        'assert ui["noUI"]["printed"] == "minimal command in print mode (no console.log output)"\n'
        'assert ui["rpcCustomScreen"]["lastNotification"] and ui["rpcCustomScreen"]["lastNotification"].get("type") == "error"\n'
        'assert comp["widths"]["20"]["allFit"] and comp["widths"]["40"]["allFit"] and comp["widths"]["80"]["allFit"]\n'
        'print("held: hasUI vs mode===tui are different guards; component API uses display columns")',
    ),
    (
        "md",
        """## Interpretation

A command has three presentation modes, and the chapter shows the boundaries:

| Mode | `ctx.hasUI` | `ctx.mode` | What works |
|---|---|---|---|
| Print / JSON | false | `"print"` / `"json"` | `console.log`, `ctx.ui.notify` (prints) |
| RPC | true | `"ui"` | `ctx.ui.select`, `ctx.ui.confirm`, `ctx.ui.notify` |
| TUI | true | `"tui"` | **All of the above** + `ctx.ui.custom` (custom screens), entry renderers |

The component API:
* `render(width: number): string[]` — returns lines that fit in `width` **display columns**
* `handleInput(data: string): void` — receives keystrokes; `q` and `Escape` finish
* `invalidate(): void` — clears the width cache

The practical rules:
* **Degrade gracefully** — check `ctx.hasUI` for dialogs, `ctx.mode === "tui"` for custom screens.
* **Use `visibleWidth`, not `string.length`** — wide characters (CJK, emoji) count as 2 columns.
* **Cache by width** — `invalidate()` only when the data changes, not on every keystroke.
* **Custom screens are TUI-only** — they are an escape hatch for complex UIs; most commands don't need them.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=20,
            mode="**Run** — real sessions with the chapter's guard-ui and guard-minimal extensions, plus direct component tests. No terminal is attached; RPC mode is used where a UI is needed.",
            scope="`in_process_runtime`. The command modes, component API, and `hasUI`/`mode` distinction are Pi's.",
            provenance=[
                "**Ran** `drivers/ch20-ui.ts`: four real sessions (RPC, print, RPC custom screen, minimal) plus direct `BlockListComponent` tests at three widths.",
                "**Ran** `ch20-ui/ui.test.ts` (7 tests).",
                "**Read** `examples/evidence.json`, chapter 20 rows (7 claims).",
            ],
            limits=[
                "**The custom screen and entry renderer were not drawn** — they compile against the pinned declarations and the component is tested directly (`ch20-lim1`).",
                "**No terminal rendering is exercised** — this is a headless run. Layer 1–2 checks (Shift+Enter, Kitty keyboard, tmux passthrough) are in chapter 44 (`ch20-lim2`).",
                "**`registerToolRenderer` is documented-not-run** by the suite (`ch17-lim3`).",
            ],
        ),
    ),
]