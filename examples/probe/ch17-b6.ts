pi.on("tool_call", async (event) => {
	if (event.toolName !== "review_diff") return;

	const current = pi.getActiveTools();
	if (!current.includes("failing_tests")) {
		pi.setActiveTools([...current, "failing_tests"]);
	}
});
