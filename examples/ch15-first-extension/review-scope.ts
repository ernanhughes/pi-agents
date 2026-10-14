import { Type } from "@earendil-works/pi-ai";
import { defineTool, type ExtensionAPI } from "@earendil-works/pi-coding-agent";

const reviewScopeTool = defineTool({
	name: "review_scope",
	label: "Review Scope",
	description:
		"List the files changed in this repository and the checks this project defines. " +
		"Use before reviewing a diff so findings cover the files that actually changed.",
	parameters: Type.Object({
		base: Type.Optional(
			Type.String({
				description: "Optional git ref to compare against. Defaults to the working tree.",
			}),
		),
	}),

	async execute(_toolCallId, params, _signal, _onUpdate, _ctx) {
		const base = params.base?.trim() || "";
		const diffCmd = base ? `git diff --name-only ${base}` : "git status --short";
		return {
			content: [
				{ type: "text", text: `Run \`${diffCmd}\` and report the changed files.` },
			],
			// details is for rendering or state reconstruction; keep it small.
			details: { base: base || null, diffCmd },
		};
	},
});

export default function (pi: ExtensionAPI) {
	pi.registerTool(reviewScopeTool);
}
