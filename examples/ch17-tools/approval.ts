import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

// The approval extension shown in extensions.md. A tool that declares no hints
// is treated as destructive and open-world, so it needs approval.
export default function (pi: ExtensionAPI) {
	pi.on("tool_call", async (event, ctx) => {
		const hints = pi.getAllTools().find((tool) => tool.name === event.toolName)?.annotations;
		const needsApproval =
			hints?.destructiveHint === true ||
			(!hints?.readOnlyHint && ((hints?.destructiveHint ?? true) || (hints?.openWorldHint ?? true)));
		if (needsApproval && !(await ctx.ui.confirm("Allow tool call?", event.toolName))) {
			return { block: true, reason: `${event.toolName} was not approved` };
		}
	});
}
