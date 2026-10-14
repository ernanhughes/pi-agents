import { Type } from "@earendil-works/pi-ai";
import { defineTool, type ExtensionAPI } from "@earendil-works/pi-coding-agent";

const runChecks = defineTool({
	name: "run_checks",
	label: "Run Checks",
	description:
		"Run this repository's own type check and unit tests and return the results. " +
		"Use before reviewing a diff or claiming a change is verified.",
	annotations: { readOnlyHint: true, openWorldHint: false },
	exposure: "direct",

	parameters: Type.Object({
		skipTests: Type.Boolean({ description: "Run only the type check.", default: false }),
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

export default function (pi: ExtensionAPI) {
	pi.registerTool(runChecks);
}
