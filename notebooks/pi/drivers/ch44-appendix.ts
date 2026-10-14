// Chapter 44 (Appendix B) - The Terminal Interface, in Detail
// Which of the six layers can be checked without a terminal?
// (b) headless-capable: visibleWidth, truncateToWidth, wrapTextWithAnsi, sliceByColumn, CURSOR_MARKER, KeybindingsManager, theme parsing.

import { visibleWidth, truncateToWidth, wrapTextWithAnsi, sliceByColumn, CURSOR_MARKER, KeybindingsManager } from "@earendil-works/pi-tui";
import { parseColor } from "@earendil-works/pi-tui/dist/colors.js";

const plain = "hello";
const wide = "路径匹配";
const emoji = "a😀b";
const ansi = "\x1b[31mred\x1b[0m text";

const row = (label: string, v: number) => ({ label, v });

console.log(JSON.stringify({
	visibleWidth: {
		plain: visibleWidth(plain),
		wide: visibleWidth(wide),
		emoji: visibleWidth(emoji),
		ansi: visibleWidth(ansi),
		wideCountsDouble: visibleWidth(wide) === wide.length * 2 ? "2x" : visibleWidth(wide),
	},
	truncate: {
		at3: truncateToWidth("abcdef", 3),
		at3Ellipsis: truncateToWidth("abcdef", 3, "…"),
		noTrunc: truncateToWidth("abc", 5),
	},
	wrap: {
		lines: wrapTextWithAnsi("the quick brown fox jumps over the lazy dog", 10),
		count: wrapTextWithAnsi("the quick brown fox jumps over the lazy dog", 10).length,
	},
	slice: sliceByColumn("abcdef", 2, 3),
	cursorMarker: {
		exists: typeof CURSOR_MARKER === "string" && CURSOR_MARKER.length > 0,
		value: CURSOR_MARKER,
	},
	keybindings: {
		managerConstructible: (() => { try { new KeybindingsManager({} as any); return true; } catch { return false; } })(),
	},
	theme: {
		parsesHex: (() => { try { parseColor("#123456"); return true; } catch (e: any) { return String(e.message); } })(),
		rejectsInvalid: (() => { try { parseColor("not-a-color"); return "accepted"; } catch (e: any) { return String(e.message).slice(0, 60); } })(),
	},
}));