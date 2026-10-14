import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
	pi.on("before_agent_start", (event) => {
		// getActiveTools(), not getAllTools(). getAllTools() reports every
		// *registered* tool, so a tool the session disabled would still be
		// described here — and the model would be told to use something it
		// cannot call. The active set is what is declared to the model.
		const active = pi.getActiveTools();
		if (!active.includes("run_checks")) {
			// Delete rather than leave stale: a section written for a previous
			// turn outlives the condition that produced it.
			delete event.systemPromptOptions.sections.review_guard;
			return;
		}

		event.systemPromptOptions.sections.review_guard =
			"- `run_checks` runs this repository's type check and unit tests. " +
			"Use it instead of running a command yourself before reporting on a change. " +
			"- Force pushes are blocked by an extension. If a push is refused, do not retry with a different form.";
	});
}
