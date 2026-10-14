import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Text } from "@earendil-works/pi-tui";

// Added in 1.0.1. Chooses renderers for calls to any tool by name, including
// tools that are not registered yet. next() returns what the remaining
// resolvers would use, so returning next() defers rather than suppresses.
// A renderer returns a pi-tui Component, not a plain object.
export default function (pi: ExtensionAPI) {
	pi.registerToolRenderer((toolName, next) => {
		if (toolName.startsWith("mcp__")) {
			return { renderCall: () => new Text("call an MCP server", 0, 0) };
		}
		return next();
	});
}
