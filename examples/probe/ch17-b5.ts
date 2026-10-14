const reviewDiff = defineTool({
	name: "review_diff",
	label: "Review Diff",
	description: "Run the project's checks and list failing tests for the changed files, then summarise both.",
	parameters: Type.Object({}),

	// ctx is the fifth argument: an ExtensionToolContext, which is the extension
	// context plus executeTool().
	async execute(_id, _params, signal, onUpdate, ctx) {
		const checks = await ctx.executeTool("run_checks", {}, { signal, onUpdate });
		const tests = await ctx.executeTool("failing_tests", {}, { signal, onUpdate });

		// executeTool() never rejects for a tool failure. It resolves to an outcome,
		// { toolCall, result, isError }, and the tool's own content and
		// structuredContent are on outcome.result.
		const checksText = checks.result.content.find((c) => c.type === "text")?.text ?? "none";

		return {
			content: [
				{ type: "text", text: `checks${checks.isError ? " (failed)" : ""}: ${checksText}` },
				{ type: "text", text: `tests: ${tests.result.structuredContent ? JSON.stringify(tests.result.structuredContent) : "none"}` },
			],
			details: { nested: ["run_checks", "failing_tests"] },
		};
	},
});
