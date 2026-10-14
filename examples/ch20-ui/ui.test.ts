import { test, mock } from "node:test";
import assert from "node:assert/strict";
import { visibleWidth } from "@earendil-works/pi-tui";
import { makeSession, UiRecorder } from "../harness/session.ts";
import { BlockListComponent, type BlockListTheme } from "./block-list.ts";
import guardUi from "./guard-ui.ts";

const plainTheme: BlockListTheme = { fg: (_c, t) => t, bold: (t) => t };

test("with a UI (RPC): the command opens a dialog and shows the answer as a notification", async () => {
	const ui = new UiRecorder();
	ui.selectAnswers = ["Show blocked calls"];
	const h = await makeSession({ extensions: [guardUi], ui });
	await h.session.prompt("/guard");
	assert.equal(ui.selects[0].title, "Path guard");
	assert.equal(ui.notifications.at(-1)?.message, "0 blocked call(s) this session");
	h.dispose();
});

test("with no UI (print or JSON): the same command prints instead of opening a dialog", async () => {
	const log = mock.method(console, "log", () => {});
	const h = await makeSession({ extensions: [guardUi] });
	await h.session.prompt("/guard");
	const printed = log.mock.calls.map((c) => String(c.arguments[0])).join("\n");
	log.mock.restore();
	assert.match(printed, /\[guard\] 0 blocked call\(s\); run this in interactive mode/);
	h.dispose();
});

test("hasUI is not the same as a terminal: under RPC the custom screen is refused, not attempted", async () => {
	const ui = new UiRecorder();
	const h = await makeSession({ extensions: [guardUi], ui });
	await h.session.prompt("/guard-blocks");
	assert.deepEqual(ui.notifications.at(-1), { message: "/guard-blocks requires interactive mode", type: "error" });
	h.dispose();
});

test("component: every line fits the width, measured in columns, including wide characters", () => {
	const blocks = [
		{ tool: "write", reason: "path matches a very long path that will not fit in twenty columns", at: 0 },
		{ tool: "edit", reason: "路径匹配 .env 受保护的文件 and more", at: 0 },
	];
	const c = new BlockListComponent(blocks, plainTheme, () => {});
	for (const width of [20, 40, 80]) {
		for (const line of c.render(width)) {
			assert.ok(visibleWidth(line) <= width, `"${line}" is ${visibleWidth(line)} columns, wider than ${width}`);
		}
	}
});

test("component: output is cached by width and recomputed after invalidate()", () => {
	const blocks = [{ tool: "write", reason: "r", at: 0 }];
	const c = new BlockListComponent(blocks, plainTheme, () => {});
	assert.strictEqual(c.render(40), c.render(40), "same width returns the cached array");
	assert.notStrictEqual(c.render(40), c.render(30), "a new width recomputes");
	const before = c.render(40);
	c.invalidate();
	assert.notStrictEqual(c.render(40), before);
});

test("component: it finishes through the completion callback on q or Escape", () => {
	let closed = 0;
	const c = new BlockListComponent([], plainTheme, () => closed++);
	c.handleInput("x");
	assert.equal(closed, 0);
	c.handleInput("q");
	c.handleInput("\x1b");
	assert.equal(closed, 2);
});

test("the smallest command receives its raw argument text", async () => {
	const ui = new UiRecorder();
	const h = await makeSession({ extensions: [(await import("./guard-minimal.ts")).default], ui });
	await h.session.prompt("/guard status now");
	assert.equal(ui.notifications.at(-1)?.message, 'guard received: "status now"');
	h.dispose();
});
