import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const BLOCKED = [
	/\bgit\s+push\b[^\n]*(--force|-f)\b/,
	/\bgit\s+reset\s+--hard\b/,
	/\bgit\s+clean\b[^\n]*-[a-z]*f/,
];

export default function (pi: ExtensionAPI) {
	pi.on("tool_call", async (event, ctx) => {
		if (event.toolName !== "bash" && event.toolName !== "powershell") return;

		const raw = JSON.stringify(event.input);
		const hit = BLOCKED.find((re) => re.test(raw));
		if (!hit) return;

		if (!ctx.hasUI) {
			// No way to ask. Refuse rather than allow silently.
			return { block: true, reason: `Guard blocked: ${hit.source}` };
		}

		const ok = await ctx.ui.confirm(
			"This command rewrites history or destroys work. Allow?",
			raw.slice(0, 200),
		);
		if (ok) return;

		return { block: true, reason: "Blocked by review-guard extension" };
	});
}
