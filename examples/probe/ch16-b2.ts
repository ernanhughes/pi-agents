import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
	let blockedThisRun = 0;

	pi.registerCommand("guard-status", {
		description: "Show how many calls review-guard has blocked this run",
		handler: async (_args, ctx) => {
			ctx.ui.notify(`review-guard blocked ${blockedThisRun} call(s)`, "info");
		},
	});

	pi.on("session_start", async () => {
		blockedThisRun = 0;
	});

	pi.on("tool_call", async (event, ctx) => {
		if (event.toolName !== "bash") return;
		const raw = JSON.stringify(event.input);
		if (!/\bgit\s+push\b[^\n]*(--force|-f)\b/.test(raw)) return;

		const ok = ctx.hasUI
			? await ctx.ui.confirm("Allow a force push?", raw.slice(0, 200))
			: false;

		if (ok) return;
		blockedThisRun += 1;
		return { block: true, reason: "Blocked by review-guard: force push requires --force-with-lease" };
	});
}
