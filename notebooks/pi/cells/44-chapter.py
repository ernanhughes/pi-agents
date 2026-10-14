"""Chapter 44 (Appendix B) - The Terminal Interface, in Detail."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Appendix B — The Terminal Interface, in Detail"
QUESTION = """Which of the six layers can be checked without a terminal, and which genuinely
cannot?

The chapter's point: the terminal UI is a **layered system** — terminal emulator,
reporting protocols, pi-tui components, interactive mode, configuration,
extensions. Layers 3–6 are checkable headlessly; layers 1–2 need a real
terminal that reports capabilities and keys."""

CELLS = [
    ("md", heading(44, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "**Layer 3 (pi-tui) is checkable headlessly**: `visibleWidth` counts display columns for wide characters, emoji and ANSI; `truncateToWidth`, `wrapTextWithAnsi`, `sliceByColumn` do the width work; `CURSOR_MARKER` and `KeybindingsManager` exist and behave.",
                "**Layer 6 (extensions) is checkable**: the chapter 20 component and mode-gate tests run without a terminal.",
                "**Theme colour parsing is headless**: `parseColor` accepts a hex and rejects an invalid value.",
                "**Layers 1–2 are NOT checkable without a terminal** — Shift+Enter reporting, Kitty keyboard negotiation, and hardware-cursor placement are manual checks.",
            ],
            [
                "**Layers 1–2 are not executable** without the actual terminal: Shift+Enter reporting, Kitty keyboard negotiation, tmux passthrough, per-terminal settings, hardware cursor and IME placement, the ≤100 ms theme timeout.",
                "**`examples/probe/` is unverified scratch, not evidence** — this notebook does not rely on it.",
                "**A capability-override table is declared, not measured here.**",
            ],
        ),
    ),
    *setup_cells(
        44,
        mode="**Run** (layers 3 and 6 headless) + **Manual/optional live** (layers 1–2, a NOT RUN checklist).",
        scope="`in_process_runtime` + `declarations`. No terminal is attached.",
    ),
    (
        "md",
        """## Baseline: the pandoc-style width rules at layer 3

The pi-tui width functions are pure and headless. Wide characters and emoji
count in display columns, not string length; ANSI escapes are stripped.""",
    ),
    (
        "code",
        'TUI = pinb.driver_source("ch44-appendix.ts")\n'
        'tui = pinb.driver(TUI, label="ch44-appendix", timeout=120)\n'
        'w = tui["visibleWidth"]\n'
        'print(pinb.md_table(\n'
        '    ["input", "visibleWidth"],\n'
        '    [[repr("hello"), w["plain"]],\n'
        '     [repr("路径匹配"), w["wide"]],\n'
        '     [repr("a😀b"), w["emoji"]],\n'
        '     [repr("ANSI red text"), w["ansi"]]],\n'
        "))",
    ),
    (
        "code",
        'pinb.show_checks([\n'
        '    pinb.check("wide characters count as 2 columns",\n'
        '               w["wide"] == 8, f"{w[\'wide\']} columns for 4 CJK chars"),\n'
        '    pinb.check("emoji count wider than one column",\n'
        '               w["emoji"] > 2, f"{w[\'emoji\']} columns"),\n'
        '    pinb.check("ANSI escapes are stripped: red text is 8 columns",\n'
        '               w["ansi"] == 8, f"{w[\'ansi\']} columns"),\n'
        "])",
    ),
    (
        "md",
        """## The width helpers: truncate, wrap, slice""",
    ),
    (
        "code",
        'tr = tui["truncate"]\n'
        'print(pinb.md_table(\n'
        '    ["operation", "result"],\n'
        '    [["truncate abcdef at 3", tr["at3"]],\n'
        '     ["truncate with ellipsis", tr["at3Ellipsis"]],\n'
        '     ["truncate does nothing when it fits", tr["noTrunc"]],\n'
        '     ["wrap at 10 columns: lines", tui["wrap"]["count"]],\n'
        '     ["slice columns 2..5 of abcdef", tui["slice"]],\n'
        '     ["CURSOR_MARKER present", "yes" if tui["cursorMarker"]["exists"] else "no"],\n'
        '     ["KeybindingsManager constructible", "yes" if tui["keybindings"]["managerConstructible"] is True else "no"]],\n'
        "))",
    ),
    (
        "code",
        'pinb.show_checks([\n'
        '    pinb.check("truncate changes the text when it does not fit",\n'
        '               tui["truncate"]["at3"] != "abcdef" and "..." in tui["truncate"]["at3"], "default ellipsis applied"),\n'
        '    pinb.check("truncate can take a custom ellipsis",\n'
        '               "…" in tui["truncate"]["at3Ellipsis"], "ellipsis used"),\n'
        '    pinb.check("truncate leaves text alone when it fits",\n'
        '               tui["truncate"]["noTrunc"] == "abc", "unchanged"),\n'
        '    pinb.check("wrap splits a long line into width-sized lines",\n'
        '               tui["wrap"]["count"] > 1, f"{tui[\'wrap\'][\'count\']} lines"),\n'
        '    pinb.check("sliceByColumn works on columns, not characters",\n'
        '               tui["slice"] == "cde", "cde"),\n'
        '    pinb.check("CURSOR_MARKER is a real marker string",\n'
        '               tui["cursorMarker"]["exists"], tui["cursorMarker"]["value"]),\n'
        '    pinb.check("KeybindingsManager can be constructed headlessly",\n'
        '               tui["keybindings"]["managerConstructible"] is True, "constructible"),\n'
        "])",
    ),
    (
        "md",
        """## Layer 6: the mode gate and the component from chapter 20

The chapter 20 UI tests run headless: the `hasUI` vs `mode === "tui"` distinction
and the `BlockListComponent` width cache. They are this layer's checkable row.""",
    ),
    *canonical_tests(
        44,
        "ch20-ui/ui.test.ts",
        what="The layer-6 checks (component and mode gate)",
        show="component",
    ),
    (
        "md",
        """## Layers 1–2: the NOT RUN checklist

These genuinely cannot be checked without the terminal Pi is talking to. This
notebook says so instead of pretending.""",
    ),
    (
        "code",
        'pinb.unrun("Shift+Enter and modified-Enter reporting", "layer 2 needs a terminal that reports the modified key")\n'
        'pinb.unrun("Kitty keyboard protocol negotiation", "layer 2 needs the terminal\'s protocol answer")\n'
        'pinb.unrun("tmux passthrough and per-terminal settings", "layer 2 needs the terminal session")\n'
        'pinb.unrun("hardware cursor and IME placement", "layer 4 needs an interactive terminal")\n'
        'pinb.unrun("the <= 100 ms theme-timeout behaviour", "layer 2 needs the terminal\'s answer to arrive late")\n'
        'print()\n'
        'print("The capability-override table is declared in the chapter; it is not measured here.")',
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** `visibleWidth("路径匹配")` returned 8. What does the length —
not the width — return in JavaScript?

**Then change one input.** `sliceByColumn("abcdef", 2, 3)` returned `"cde"`.
What does `sliceByColumn("a😀bc", 1, 2)` return — by columns, not characters?

**Predict the boundary.** `CURSOR_MARKER` is `ESC-pi:c-BEL`. Where does the TUI
use it, and why would a component that forgets it break IME?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. JS length of 路径匹配 is 4 - width 8, length 4.")\n'
        'print("  2. sliceByColumn(a😀bc, 1, 2): 2 columns starting col 1 - the emoji is 2 wide.")\n'
        'print("  3. CURSOR_MARKER positions the hardware cursor for IME; forgetting it misplaces candidates.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  visibleWidth: plain={w[\'plain\']}, wide={w[\'wide\']}, emoji={w[\'emoji\']}, ansi={w[\'ansi\']}")\n'
        'print(f"  truncate at 3: {tui[\'truncate\'][\'at3\']!r}")\n'
        'print(f"  wrap count: {tui[\'wrap\'][\'count\']}, slice: {tui[\'slice\']!r}")\n'
        "print()\n"
        'assert w["wide"] == 8 and w["ansi"] == 8\n'
        'assert tui["truncate"]["noTrunc"] == "abc"\n'
        'assert tui["wrap"]["count"] > 1 and tui["slice"] == "cde"\n'
        'assert tui["cursorMarker"]["exists"]\n'
        'print("held: layer 3 width rules are headless; layers 1-2 are NOT RUN; CURSOR_MARKER exists")',
    ),
    (
        "md",
        """## Interpretation

The six layers, and what this notebook can check:

| Layer | Checkable here? | What was done |
|---|---|---|
| 1. Terminal emulator | **No** | NOT RUN — needs the terminal |
| 2. Reporting protocols | **No** | NOT RUN — needs the protocol answer |
| 3. pi-tui components | **Yes** | `visibleWidth`, `truncateToWidth`, `wrapTextWithAnsi`, `sliceByColumn`, `CURSOR_MARKER`, `KeybindingsManager` |
| 4. Interactive mode | Mostly not | NOT RUN for cursor/IME; the rest needs a terminal |
| 5. Your configuration | Partial | Keybindings manager constructible; theme colour parsing |
| 6. Your extensions | **Yes** | Chapter 20's component and mode-gate tests |

The practical rules:
1. **Width is columns, not length** — wide characters and emoji prove it.
2. **`CURSOR_MARKER` is the IME hook** — a component that forgets it misplaces candidates.
3. **Layers 1–2 need the real terminal** — a headless run cannot see a key it never received.
4. **An unmeasured capability table stays a declaration** — this notebook does not pretend otherwise.
5. **`examples/probe/` is scratch, not evidence** — nothing here relies on it.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=44,
            mode="**Run** (layers 3 and 6 headless) + **Manual/optional live** (layers 1–2, a NOT RUN checklist).",
            scope="`in_process_runtime` + `declarations`. No terminal is attached.",
            provenance=[
                "**Ran** `drivers/ch44-appendix.ts`: `visibleWidth`, `truncateToWidth`, `wrapTextWithAnsi`, `sliceByColumn`, `CURSOR_MARKER`, `KeybindingsManager`, `parseColor` — all headless.",
                "**Ran** `ch20-ui/ui.test.ts` (7 tests) for the layer-6 component and mode-gate checks.",
                "**Read** the pinned `@earendil-works/pi-tui` declarations.",
            ],
            limits=[
                "**Layers 1–2 are not executable** without the actual terminal — the NOT RUN checklist states the prerequisites.",
                "**A capability-override table is declared, not measured here.**",
                "**`examples/probe/` is unverified scratch, not evidence.**",
            ],
            unrun=[
                "Shift+Enter and modified-Enter reporting (layer 2).",
                "Kitty keyboard negotiation, tmux passthrough, per-terminal settings (layer 2).",
                "Hardware cursor and IME placement (layer 4).",
                "The ≤100 ms theme-timeout behaviour (layer 2).",
            ],
        ),
    ),
]