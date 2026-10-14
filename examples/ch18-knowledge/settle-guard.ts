import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
	pi.on("agent_before_settle", async (event) => {
		const ranChecks = event.context.contextMessages.some(
			(m) => m.role === "toolResult" && m.toolName === "run_checks",
		);
		if (ranChecks) return;

		// Nudge once. Without this, a model that never runs the checks is asked
		// again after every answer, forever.
		const alreadyNudged = event.context.contextMessages.some(
			(m) => m.role === "custom" && m.customType === "review-guard",
		);
		if (alreadyNudged) return;

		return {
			entries: [
				{
					type: "custom_message",
					customType: "review-guard",
					content: "You reported on a change without running `run_checks`. Run it now and revise.",
					display: false,
				},
			],
			continue: true,
		};
	});
}
