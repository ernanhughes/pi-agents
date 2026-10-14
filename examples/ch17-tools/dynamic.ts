import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { failingTests, reviewDiff, runChecks } from "./tools.ts";

// Register every tool first. Keep the optional one inactive. Activate it when
// the tool that needs it is called.
export default function (pi: ExtensionAPI) {
	pi.registerTool(runChecks);
	pi.registerTool({ ...failingTests, exposure: "deferred" });
	pi.registerTool(reviewDiff);

	pi.on("tool_call", async (event) => {
		if (event.toolName !== "review_diff") return;

		const current = pi.getActiveTools();
		if (!current.includes("failing_tests")) {
			pi.setActiveTools([...current, "failing_tests"]);
		}
	});
}
