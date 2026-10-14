import { Type } from "@earendil-works/pi-ai";

const failingTests = defineTool({
	name: "failing_tests",
	label: "Failing Tests",
	description: "List the currently failing unit tests, grouped by file. Use when deciding what to fix.",
	parameters: Type.Object({}),
	outputSchema: Type.Object({
		files: Type.Array(
			Type.Object({ path: Type.String(), failed: Type.Integer(), names: Type.Array(Type.String()) }),
		),
	}),

	async execute() {
		const files = [
			{ path: "src/auth/refresh.ts", failed: 2, names: ["refreshes expired token", "retries once"] },
		];

		return {
			content: [{ type: "text", text: `${files.length} file(s) with failing tests.` }],
			structuredContent: { files },
			details: { count: files.length },
		};
	},
});
