import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
	// Registrations are not saved: register again on every load.
	pi.registerMcpServer("jira", {
		url: "https://mcp.example.com/jira",
		exposure: "codemode",
	});

	pi.registerCommand("jira-off", {
		description: "Remove the jira MCP server for this session",
		handler: async () => {
			pi.unregisterMcpServer("jira");
		},
	});
}
