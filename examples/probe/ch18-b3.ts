pi.on("agent_before_settle", async (event) => {
	const ranChecks = event.context.contextMessages.some(
		(m) => m.role === "toolResult" && m.toolName === "run_checks",
	);
	if (ranChecks) return;

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
