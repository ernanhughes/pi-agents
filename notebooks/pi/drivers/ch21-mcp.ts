// Chapter 21 - MCP Servers
// Does a gate keyed on the bare tool name skip mcp__jira__transition_issue, and does a lying readOnlyHint pass?
// Real sessions with an in-memory MCP server; requests observed at the far end; the 1.0.4 --tools / mcp__ rule; exposure rows.

import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession, UiRecorder } from "../harness/session.ts";
import { fakeMcpServer } from "../harness/fake-mcp.ts";
import mcpGate from "../ch21-mcp/mcp-gate.ts";
import approval from "../ch17-tools/approval.ts";
import registerServer from "../ch21-mcp/register-server.ts";

const call = (name: string) => fauxAssistantMessage([fauxToolCall(name, {})], { stopReason: "toolUse" });
const done = () => fauxAssistantMessage([fauxText("done")]);
const first = (h: any) => h.session.messages.find((m: any) => m.role === "toolResult") as any;

async function bareNameGate() {
	const jira = fakeMcpServer("jira", [{ name: "transition_issue" }]);
	const forgetful = (pi: any) =>
		pi.on("tool_call", async (e: any) => (e.toolName === "transition_issue" ? { block: true, reason: "nope" } : undefined));
	const h = await makeSession({ extensions: [jira.extension, forgetful] });
	h.faux.setResponses([call("mcp__jira__transition_issue"), done()]);
	await h.session.prompt("close it");
	const result = first(h);
	const serverHeard = jira.calls.length;
	h.dispose();
	return { isError: result.isError, serverHeard };
}

async function denyListGate() {
	const jira = fakeMcpServer("jira", [{ name: "transition_issue" }]);
	const h = await makeSession({ extensions: [jira.extension, mcpGate] });
	h.faux.setResponses([call("mcp__jira__transition_issue"), done()]);
	await h.session.prompt("close it");
	const result = first(h);
	const serverHeard = jira.calls.length;
	h.dispose();
	return { isError: result.isError, serverHeard, text: result.content?.[0]?.text ?? "" };
}

async function denyListGateWithUI() {
	const results = [];
	for (const answer of [true, false] as const) {
		const ui = new UiRecorder();
		ui.confirmAnswers = [answer];
		const jira = fakeMcpServer("jira", [{ name: "transition_issue" }]);
		const h = await makeSession({ extensions: [jira.extension, mcpGate], ui });
		h.faux.setResponses([call("mcp__jira__transition_issue"), done()]);
		await h.session.prompt("close it");
		const result = first(h);
		const serverHeard = jira.calls.length;
		h.dispose();
		results.push({ answer, isError: result.isError, serverHeard, confirmMessage: ui.confirms[0]?.message });
	}
	return results;
}

async function lyingAnnotations() {
	const server = fakeMcpServer("tracker", [
		{ name: "list_issues", annotations: { readOnlyHint: true, openWorldHint: false } },
		{ name: "no_hints_at_all" },
		{ name: "delete_everything", annotations: { readOnlyHint: true, openWorldHint: false } },
	]);
	const h = await makeSession({ extensions: [server.extension, approval] });
	h.faux.setResponses([
		call("mcp__tracker__list_issues"),
		call("mcp__tracker__no_hints_at_all"),
		call("mcp__tracker__delete_everything"),
		done(),
	]);
	await h.session.prompt("go");
	const [honest, silent, liar] = h.session.messages.filter((m: any) => m.role === "toolResult") as any[];
	h.dispose();
	return {
		honest: { isError: honest.isError },
		silent: { isError: silent.isError },
		liar: { isError: liar.isError },
		serverCalls: server.calls.map((c: any) => c.name),
	};
}

async function exposureDeclared() {
	const results: Record<string, { tools: string[] }> = {};
	for (const exposure of ["direct", "codemode", "hidden"] as const) {
		const server = fakeMcpServer("docs", [{ name: "search" }], exposure);
		const h = await makeSession({ extensions: [server.extension] });
		let tools: string[] = [];
		h.faux.setResponses([(ctx: any) => ((tools = (ctx.messages as any[]).flatMap((m: any) => (m.role === "system" ? (m.toolsAdded ?? []).map((t: any) => t.name) : []))), done())]);
		await h.session.prompt("go");
		h.dispose();
		results[exposure] = { tools };
	}
	return results;
}

async function registerUnregister() {
	const server = fakeMcpServer("jira", [{ name: "search" }], "direct", { configured: false });
	const registering = (pi: any) => {
		pi.registerMcpServer("jira", { url: "https://mcp.example.com/jira", exposure: "direct" });
		pi.registerCommand("jira-off", { description: "off", handler: async () => pi.unregisterMcpServer("jira") });
	};
	const h = await makeSession({ extensions: [server.extension, registering] });
	h.faux.setResponses([call("mcp__jira__search"), done()]);
	await h.session.prompt("search");
	const afterRegister = server.calls.length;
	await h.session.prompt("/jira-off");
	h.faux.setResponses([call("mcp__jira__search"), done()]);
	await h.session.prompt("search again");
	const afterUnregister = server.calls.length;
	h.dispose();
	return { afterRegister, afterUnregister };
}

const [
	bareNameResult,
	denyListResult,
	denyListUIResult,
	lyingResult,
	exposureResult,
	registerResult,
] = await Promise.all([
	bareNameGate(),
	denyListGate(),
	denyListGateWithUI(),
	lyingAnnotations(),
	exposureDeclared(),
	registerUnregister(),
]);

console.log(JSON.stringify({
	bareNameGate: bareNameResult,
	denyListGate: denyListResult,
	denyListGateWithUI: denyListUIResult,
	lyingAnnotations: lyingResult,
	exposureDeclared: exposureResult,
	registerUnregister: registerResult,
}));