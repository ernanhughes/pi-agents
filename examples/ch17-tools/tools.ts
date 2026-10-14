import { exec } from "node:child_process";
import { promisify } from "node:util";
import { Type } from "@earendil-works/pi-ai";
import { defineTool, type ExtensionAPI } from "@earendil-works/pi-coding-agent";

const execAsync = promisify(exec);

export async function runCommand(command: string): Promise<{ output: string; exit_code: number }> {
	try {
		const { stdout, stderr } = await execAsync(command, { maxBuffer: 1024 * 1024 });
		return { output: stdout + stderr, exit_code: 0 };
	} catch (err: any) {
		// exec rejects on a non-zero exit. That is a result, not a tool failure.
		return { output: `${err.stdout ?? ""}${err.stderr ?? ""}`, exit_code: err.code ?? 1 };
	}
}

export const runChecks = defineTool({
	name: "run_checks",
	label: "Run Checks",
	description:
		"Run this repository's own type check and unit tests and return the results. " +
		"Use before reviewing a diff or claiming a change is verified.",
	annotations: { readOnlyHint: true, openWorldHint: false },
	exposure: "direct",

	parameters: Type.Object({
		skipTests: Type.Optional(Type.Boolean({ description: "Run only the type check.", default: false })),
	}),

	async execute(_id, params, _signal) {
		const steps = params.skipTests ? ["pnpm typecheck"] : ["pnpm typecheck", "pnpm test:unit"];
		const results = await Promise.all(steps.map((command) => runCommand(command)));
		return {
			content: [{ type: "text", text: results.map((r) => r.output.slice(0, 1000)).join("\n") }],
			details: { steps, results: results.map((r) => ({ exit_code: r.exit_code })) },
		};
	},
});

export const failingTests = defineTool({
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

export const reviewDiff = defineTool({
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

export default function (pi: ExtensionAPI) {
	pi.registerTool(runChecks);
	pi.registerTool(failingTests);
	pi.registerTool(reviewDiff);
}
