import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
	pi.on("before_agent_start", (event) => {
		const tools = pi.getAllTools().map((t) => t.name);
		if (!tools.includes("run_checks")) return;

		event.systemPromptOptions.sections.review_guard =
			"- `run_checks` runs this repository's type check and unit tests. " +
			"Use it instead of running a command yourself before reporting on a change. " +
			"- Force pushes are blocked by an extension. If a push is refused, do not retry with a different form.";
	});
}
