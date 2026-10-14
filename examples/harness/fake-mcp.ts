// A minimal in-memory MCP server, for testing how Pi treats MCP tools.
// It speaks just enough JSON-RPC to initialise, list tools, and answer calls.
// Nothing about Pi's behaviour is re-implemented here: the connection, tool
// naming, exposure and gating are Pi's own. Only the remote end is faked.
import { createInMemoryTransportPair } from "@earendil-works/pi-mcp/testing";
import { LATEST_PROTOCOL_VERSION, isJsonRpcRequest } from "@earendil-works/pi-mcp";
import { createMcpExtension, type ExtensionFactory } from "@earendil-works/pi-coding-agent";

export interface FakeTool {
	name: string;
	description?: string;
	annotations?: { readOnlyHint?: boolean; destructiveHint?: boolean; idempotentHint?: boolean; openWorldHint?: boolean };
}

export interface FakeServer {
	/** Calls the server actually received, in order. */
	calls: { name: string; arguments: unknown }[];
	extension: ExtensionFactory;
}

export function fakeMcpServer(
	serverName: string,
	tools: FakeTool[],
	exposure: "direct" | "codemode" | "deferred" | "hidden" = "direct",
	options: { configured?: boolean } = {},
): FakeServer {
	const configured = options.configured ?? true;
	const calls: FakeServer["calls"] = [];

	const extension = createMcpExtension({
		loadConfig: () => ({
			servers: configured
				? [{ name: serverName, config: { url: "http://mcp.invalid/mcp", exposure } as any, source: "test", scope: "global" }]
				: [],
			errors: [],
		}),
		createTransport: () => {
			const { client, server } = createInMemoryTransportPair();
			server.onMessage(async (msg) => {
				if (!isJsonRpcRequest(msg)) return;
				const reply = (result: unknown) => server.send({ jsonrpc: "2.0", id: msg.id, result } as any);
				if (msg.method === "initialize") {
					return reply({
						protocolVersion: LATEST_PROTOCOL_VERSION,
						capabilities: { tools: {} },
						serverInfo: { name: serverName, version: "0.0.0" },
					});
				}
				if (msg.method === "tools/list") {
					return reply({
						tools: tools.map((t) => ({
							name: t.name,
							description: t.description ?? t.name,
							inputSchema: { type: "object", properties: {} },
							annotations: t.annotations,
						})),
					});
				}
				if (msg.method === "tools/call") {
					const p = msg.params as { name: string; arguments: unknown };
					calls.push({ name: p.name, arguments: p.arguments });
					return reply({ content: [{ type: "text", text: `ran ${p.name}` }] });
				}
				return reply({});
			});
			void server.start();
			return client;
		},
	});

	return { calls, extension };
}
