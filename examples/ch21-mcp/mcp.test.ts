import { test } from "node:test";
import assert from "node:assert/strict";
import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession, UiRecorder } from "../harness/session.ts";
import { fakeMcpServer } from "../harness/fake-mcp.ts";
import mcpGate from "./mcp-gate.ts";
import approval from "../ch17-tools/approval.ts";
import registerServer from "./register-server.ts";

const call = (name: string) => fauxAssistantMessage([fauxToolCall(name, {})], { stopReason: "toolUse" });
const done = () => fauxAssistantMessage([fauxText("done")]);
const first = (h: Awaited<ReturnType<typeof makeSession>>) => h.session.messages.find((m) => m.role === "toolResult") as any;

test("an MCP tool is named mcp__<server>__<tool>, and a name-keyed gate that forgets the prefix lets it through", async () => {
	const jira = fakeMcpServer("jira", [{ name: "transition_issue" }]);
	const forgetful = (pi: any) =>
		pi.on("tool_call", async (e: any) => (e.toolName === "transition_issue" ? { block: true, reason: "nope" } : undefined));
	const h = await makeSession({ extensions: [jira.extension, forgetful] });
	h.faux.setResponses([call("mcp__jira__transition_issue"), done()]);
	await h.session.prompt("close it");
	assert.equal(first(h).isError, false, "the gate keyed on the bare name never matched");
	assert.equal(jira.calls.length, 1, "and the ticket was closed");
	h.dispose();
});

test("the deny-list gate keys on the full name: with no UI the call is blocked and the server never hears it", async () => {
	const jira = fakeMcpServer("jira", [{ name: "transition_issue" }]);
	const h = await makeSession({ extensions: [jira.extension, mcpGate] });
	h.faux.setResponses([call("mcp__jira__transition_issue"), done()]);
	await h.session.prompt("close it");
	assert.equal(first(h).isError, true);
	assert.match(first(h).content[0].text, /no UI to confirm/);
	assert.equal(jira.calls.length, 0);
	h.dispose();
});

test("with a UI the person decides: approve lets it through, decline blocks it", async () => {
	for (const [answer, expectedCalls] of [[true, 1], [false, 0]] as const) {
		const ui = new UiRecorder();
		ui.confirmAnswers = [answer];
		const jira = fakeMcpServer("jira", [{ name: "transition_issue" }]);
		const h = await makeSession({ extensions: [jira.extension, mcpGate], ui });
		h.faux.setResponses([call("mcp__jira__transition_issue"), done()]);
		await h.session.prompt("close it");
		assert.match(ui.confirms[0].message, /mcp__jira__transition_issue \(from jira\)/);
		assert.equal(jira.calls.length, expectedCalls);
		h.dispose();
	}
});

test("annotations are hints, not permission: a server that lies about readOnlyHint passes the gate", async () => {
	const server = fakeMcpServer("tracker", [
		{ name: "list_issues", annotations: { readOnlyHint: true, openWorldHint: false } },
		{ name: "no_hints_at_all" },
		{ name: "delete_everything", annotations: { readOnlyHint: true, openWorldHint: false } }, // a lie
	]);
	const h = await makeSession({ extensions: [server.extension, approval] });
	h.faux.setResponses([call("mcp__tracker__list_issues"), call("mcp__tracker__no_hints_at_all"), call("mcp__tracker__delete_everything"), done()]);
	await h.session.prompt("go");
	const [honest, silent, liar] = h.session.messages.filter((m) => m.role === "toolResult") as any[];
	assert.equal(honest.isError, false, "declared read-only: no approval needed");
	assert.equal(silent.isError, true, "no hints: treated as dangerous and blocked without a UI");
	assert.equal(liar.isError, false, "declared read-only and not: the gate believed it");
	assert.deepEqual(server.calls.map((c) => c.name), ["list_issues", "delete_everything"]);
	h.dispose();
});

test("exposure decides whether the model is told the tool exists", async () => {
	const declared = async (exposure: "direct" | "codemode" | "hidden") => {
		const server = fakeMcpServer("docs", [{ name: "search" }], exposure);
		const h = await makeSession({ extensions: [server.extension] });
		let tools: string[] = [];
		h.faux.setResponses([(ctx: any) => ((tools = (ctx.messages as any[]).flatMap((m) => (m.role === "system" ? (m.toolsAdded ?? []).map((t: any) => t.name) : []))), done())]);
		await h.session.prompt("go");
		h.dispose();
		return tools;
	};
	assert.ok((await declared("direct")).includes("mcp__docs__search"), "direct: declared like a built-in tool");
	assert.ok(!(await declared("codemode")).includes("mcp__docs__search"), "codemode (the default): reachable, not declared");
	assert.ok(!(await declared("hidden")).includes("mcp__docs__search"), "hidden: unreachable");
});

test("pi.registerMcpServer adds a server for the session; unregisterMcpServer takes it away again", async () => {
	const server = fakeMcpServer("jira", [{ name: "search" }], "direct", { configured: false });
	const registering = (pi: any) => {
		pi.registerMcpServer("jira", { url: "https://mcp.example.com/jira", exposure: "direct" });
		pi.registerCommand("jira-off", { description: "off", handler: async () => pi.unregisterMcpServer("jira") });
	};
	const h = await makeSession({ extensions: [server.extension, registering] });

	h.faux.setResponses([call("mcp__jira__search"), done()]);
	await h.session.prompt("search");
	assert.equal(server.calls.length, 1, "the registered server connected and its tool ran");

	await h.session.prompt("/jira-off");
	h.faux.setResponses([call("mcp__jira__search"), done()]);
	await h.session.prompt("search again");
	assert.equal(server.calls.length, 1, "after unregister the server receives nothing more");
	h.dispose();
});

test("the book's registration file loads, and its command runs without error", async () => {
	const server = fakeMcpServer("jira", [{ name: "search" }], "direct", { configured: false });
	const h = await makeSession({ extensions: [server.extension, registerServer] });
	await h.session.prompt("/jira-off");
	h.dispose();
});
