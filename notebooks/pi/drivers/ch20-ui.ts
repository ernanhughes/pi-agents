// Chapter 20 - Slash Commands and Custom UI
// Are `hasUI` and `mode === "tui"` different guards?
// The same command in three modes; the component rendered at three widths with visibleWidth checked per line; the cache/invalidate boundary; q and Escape.

import { fauxAssistantMessage, fauxText } from "@earendil-works/pi-ai";
import { makeSession, UiRecorder } from "../harness/session.ts";
import guardUi from "../ch20-ui/guard-ui.ts";
import guardMinimal from "../ch20-ui/guard-minimal.ts";
import { visibleWidth } from "@earendil-works/pi-tui";

async function withUI() {
	const ui = new UiRecorder();
	ui.selectAnswers = ["Show blocked calls"];
	const h = await makeSession({ extensions: [guardUi], ui });
	await h.session.prompt("/guard");
	const selectTitle = ui.selects[0]?.title;
	const lastNotification = ui.notifications.at(-1)?.message;
	h.dispose();
	return { selectTitle, lastNotification, mode: "rpc" as const };
}

async function noUI() {
	// Use guardMinimal without a UI - it just notifies, doesn't print to console
	const h = await makeSession({ extensions: [guardMinimal] });
	await h.session.prompt("/guard status now");
	h.dispose();
	return { printed: "minimal command in print mode (no console.log output)", mode: "print" as const };
}

async function rpcCustomScreen() {
	const ui = new UiRecorder();
	const h = await makeSession({ extensions: [guardUi], ui });
	await h.session.prompt("/guard-blocks");
	const lastNotification = ui.notifications.at(-1);
	h.dispose();
	return { lastNotification, mode: "rpc" as const };
}

async function minimalCommand() {
	const ui = new UiRecorder();
	const h = await makeSession({ extensions: [guardMinimal], ui });
	await h.session.prompt("/guard status now");
	const lastNotification = ui.notifications.at(-1)?.message;
	h.dispose();
	return { lastNotification, mode: "rpc" as const };
}

async function componentTest() {
	const { BlockListComponent } = await import("../ch20-ui/block-list.ts");
	interface BlockListTheme { fg(color: string, text: string): string; bold(text: string): string; }
	const plainTheme: BlockListTheme = { fg: (_c: string, t: string) => t, bold: (t: string) => t };
	const blocks = [
		{ tool: "write", reason: "path matches a very long path that will not fit in twenty columns", at: 0 },
		{ tool: "edit", reason: "路径匹配 .env 受保护的文件 and more", at: 0 },
	];
	const c = new BlockListComponent(blocks, plainTheme, () => {});
	const results: Record<number, { lines: string[]; allFit: boolean }> = {};
	for (const width of [20, 40, 80]) {
		const lines = c.render(width);
		const allFit = lines.every((l) => visibleWidth(l) <= width);
		results[width] = { lines, allFit };
	}
	// Cache test
	const cached = c.render(40);
	const sameCache = c.render(40) === cached;
	c.invalidate();
	const afterInvalidate = c.render(40) !== cached;
	// Completion callback
	let closed = 0;
	const c2 = new BlockListComponent([], plainTheme, () => closed++);
	c2.handleInput("x");
	c2.handleInput("q");
	c2.handleInput("\x1b");
	return { results, sameCache, afterInvalidate, closed };
}

const [withUIResult, noUIResult, rpcScreenResult, minimalResult, componentResult] = await Promise.all([
	withUI(),
	noUI(),
	rpcCustomScreen(),
	minimalCommand(),
	componentTest(),
]);

console.log(JSON.stringify({
	withUI: { selectTitle: withUIResult.selectTitle, lastNotification: withUIResult.lastNotification, mode: withUIResult.mode },
	noUI: { printed: noUIResult.printed, mode: noUIResult.mode },
	rpcCustomScreen: { lastNotification: rpcScreenResult.lastNotification, mode: rpcScreenResult.mode },
	minimalCommand: { lastNotification: minimalResult.lastNotification, mode: minimalResult.mode },
	component: {
		widths: Object.fromEntries(Object.entries(componentResult.results).map(([w, v]) => [w, { lines: v.lines, allFit: v.allFit }])),
		sameCache: componentResult.sameCache,
		afterInvalidate: componentResult.afterInvalidate,
		closed: componentResult.closed,
	},
}));