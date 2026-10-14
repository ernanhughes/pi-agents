import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
	pi.on("tool_call", async (event, ctx) => {
		if (event.toolName !== "bash" && event.toolName !== "edit") return;
		const raw = JSON.stringify(event.input);
		// \b, not (^|\s): in the serialised input "git" follows a quote, not whitespace.
		const forcePush = /\bgit\s+push\b.*(?:\s--force\b|\s-f\b|--force-with-lease\b)/.test(raw);
		// An unconditional prohibition, not a question: no confirmation prompt, so
		// there is nothing for a person to approve.
		if (forcePush) return { block: true, reason: "Force pushes are not permitted by this repository's guard" };
		// A different kind of rule. Ask, then proceed on the answer.
		if (!/\bgit\s+push\b/.test(raw) && !/migrations\//.test(raw)) return;
		if (ctx.hasUI && (await ctx.ui.confirm("Allow this call?", raw.slice(0, 120)))) return;
		return { block: true, reason: "Blocked by guard extension" };
	});
}
