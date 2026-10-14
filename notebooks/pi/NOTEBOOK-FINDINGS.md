# NOTEBOOK-FINDINGS — Pi Agents

These historical findings were carried into the [development repository](../../README.md)
from the combined book checkout. See [the notebook guide](README.md) for current
manuscript dependencies; the move itself does not establish new runtime results.

Discrepancies, surprises and corrections discovered while building the notebook
companions. Most are between a *first draft assumption* and what the actual
pinned code does; several are between the book's prose and the pinned
declarations. Nothing here was fixed by changing a chapter to fit notebook
output — where the book and the code disagree, the discrepancy is recorded.

## 1. `SystemMessage.replace` exists in prose, not in the 1.0.4 declaration

- **Chapter 26.** `message-types.md` describes a `SystemMessage.replace`. The
  exported `SystemMessage` in `@earendil-works/pi-ai/dist/types.d.ts` at 1.0.4
  has **no `replace` member**, and no shipped JavaScript reads one.
- This is the book's own recorded discrepancy (the drift protocol in AGENTS.md).
  The notebook (26) states it plainly: the declaration wins, and the mismatch is
  recorded, not smoothed over.
- **No chapter text changed.**

## 2. A tool's `structuredContent` is not copied to the `toolResult` message

- **Chapter 17.** The book's test is named "structuredContent is returned
  alongside the model-facing content" but asserts only `r.content[0].text`; the
  `structuredContent` field from a tool return value is not copied to the
  `toolResult` message. The notebook states this rather than asserting a false
  boundary.
- **No chapter text changed.** The notebook's wording reflects what the tool
  result actually carries.

## 3. `--tools` at 1.0.4 keeps MCP tools

- **Chapters 6 and 32.** As of 1.0.4, `--tools` no longer removes MCP tools — an
  entry starting with `mcp__` is required to act on them (verified in
  `ch21-mcp/tool-allowlist.test.ts`). The notebooks state this where a `--tools`
  claim appears and do not let an older reading leak in.

## 4. The published browser experiences are 1.0.2 recordings

- **Chapters 31 and 39.** `experiment.json` in both experiences declares
  `"pinnedVersion": "1.0.2"`. The notebooks **do not relabel them**. Each
  regenerates a fresh 1.0.4 trace from the chapter's own exporter
  (`experiences/ch31.ts`, `ch39.ts`) and inspects the recording, when present,
  as clearly historical. `PIN_EXPERIENCES` points a reader at the site repo if
  the default sibling path is absent.

## 5. `pi-tui` width functions return styled text, not bare substrings

- **Chapter 44.** `truncateToWidth("abcdef", 3)` returns `"\x1b[0m...\x1b[0m"`
  (default ellipsis with styling resets), not `"abc"`. The notebook's first
  assertion assumed a bare substring and was corrected to assert what the
  function actually returns: a transformed string with the default ellipsis, a
  custom ellipsis when requested, and an unchanged string when it fits.
- Also: `visibleWidth("\x1b[31mred\x1b[0m text")` is **8** (the visible text),
  not the string length (17) and not 4. Corrected in the notebook.

## 6. `session.systemPrompt` omits sections on 1.0.4; the provider's copy is read

- **Chapter 18.** The driver reads `systemPromptSeenByProvider` because
  `session.systemPrompt` omits the derived section at this pin. The notebook
  states this as the reason it reads the provider's copy.

## 7. The pinned docs count is 40, and chapter 43 already says so

- **Chapter 43.** `docs/*.md` in the pinned `pi-coding-agent` is **40 files**.
  A prior (uncommitted) correction in `43-chapter.md` changed "41" to "40";
  the notebook counts the files on disk and confirms 40. Documented here so the
  count and the prose stay aligned.

## 8. Minor shape corrections inside notebooks (not chapters)

- **Ch 14.** The driver's "outside the repo" row exposes `mentionsSkillDir`
  (whether the script mentioned the skill directory), not `ranBothSteps`; the
  notebook table uses the key the driver actually returns.
- **Ch 15.** `fauxToolCall("review_scope", undefined)` did not exercise the
  no-argument path the way the chapter's test does (`{}`); the driver now sends
  `{}` to match the chapter's regression test.
- **Ch 24.** A "sibling" is created only after submitting an edited prompt, not
  by `/tree` alone; the notebook asserts both steps rather than merging them.
- **Ch 30.** The demonstration deliberately avoids `console.log` in the no-UI
  arm so the driver's JSON channel stays clean; the book's command would print,
  which is exactly the point of the UI-gate row.

## What was *not* found

- No chapter test contradicts its source under `npm run verify-examples` (280
  tests pass, 65 embedded blocks match).
- No claim in these notebooks is a real-model result; the ledger's `real_model`
  scope is empty and stays empty.
- No container or VM recipe was executed; chapter 42 and the notebooks label
  them unrun.
