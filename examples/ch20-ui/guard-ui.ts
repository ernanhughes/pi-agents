import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { Box, Text } from "@earendil-works/pi-tui";
import { BlockListComponent, type GuardBlock } from "./block-list.ts";

export default function (pi: ExtensionAPI) {
	let blocks: GuardBlock[] = [];

	const rebuild = (ctx: ExtensionContext) => {
		blocks = ctx.sessionManager
			.getBranch()
			.filter((e) => e.type === "custom" && e.customType === "guard.block")
			.map((e) => (e as { data: GuardBlock }).data);
	};
	pi.on("session_start", async (_e, ctx) => rebuild(ctx));
	pi.on("session_tree", async (_e, ctx) => rebuild(ctx));

	// A command that works with a UI and degrades without one. The behaviour of
	// the guard does not change; only the presentation does.
	pi.registerCommand("guard", {
		description: "Inspect and configure the path guard",
		getArgumentCompletions: (prefix) => {
			const modes = ["status", "pause", "resume", "reset"];
			const hit = modes.filter((m) => m.startsWith(prefix));
			return hit.length ? hit.map((m) => ({ value: m, label: m })) : null;
		},
		handler: async (_args, ctx) => {
			if (ctx.hasUI) {
				const choice = await ctx.ui.select("Path guard", ["Show blocked calls", "Pause the guard", "Resume the guard"]);
				if (choice === "Show blocked calls") {
					ctx.ui.notify(`${blocks.length} blocked call(s) this session`, "info");
				}
				return;
			}

			// JSON and print: no UI at all. Say something useful on the way out.
			console.log(`[guard] ${blocks.length} blocked call(s); run this in interactive mode to configure`);
		},
	});

	// A custom screen exists only where a real terminal is attached.
	pi.registerCommand("guard-blocks", {
		description: "Show blocked calls recorded on this branch",
		handler: async (_args, ctx) => {
			if (ctx.mode !== "tui") {
				ctx.ui.notify("/guard-blocks requires interactive mode", "error");
				return;
			}

			await ctx.ui.custom<void>((_tui, theme, _kb, done) => {
				return new BlockListComponent(blocks, theme, () => done());
			});
		},
	});

	// Draw stored entries in the transcript. Interactive mode only.
	pi.registerEntryRenderer<GuardBlock>("guard.block", (entry, { expanded }, theme) => {
		const box = new Box(1, 1, (text) => theme.bg("customMessageBg", text));
		box.addChild(new Text(`${theme.fg("accent", "[guard]")} ${entry.data?.reason ?? "blocked"}`, 0, 0));
		if (expanded) {
			box.addChild(new Text(theme.fg("dim", new Date(entry.data?.at ?? Date.now()).toLocaleString()), 0, 0));
		}
		return box;
	});
}
