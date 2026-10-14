// Evidence for chapter 21's claim that an allowlist of tool names is not an
// allowlist of MCP tools.
//
// The rules under test arrived in 1.0.4 and are documented in cli.md#mcp-tools:
// `--tools` keeps MCP tools unless an entry starts with `mcp__`, and both flags
// accept `*` patterns. The SDK option `tools` is the same allowlist `--tools`
// sets, so this runs it against a real AgentSession with Pi's own MCP client and
// a faked far end. Nothing here re-implements a Pi rule: the allowlist, the
// naming, the exposure decisions and the codemode sandbox are Pi's. Only the
// model is substituted.
import { test } from "node:test";
import assert from "node:assert/strict";
import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { createCodemodeExtension } from "@earendil-works/pi-coding-agent";
import { makeSession, type HarnessOptions } from "../harness/session.ts";
import { fakeMcpServer, type FakeTool } from "../harness/fake-mcp.ts";

const MCP_TOOL = "mcp__jira__transition_issue";
const TOOLS = [{ name: "transition_issue" }];

/** Run a codemode script that calls the MCP tool, and report what happened. */
async function scriptCallsMcp(
	exposure: "direct" | "codemode" | "deferred" | "hidden",
	options: Omit<HarnessOptions, "extensions">,
): Promise<{ serverHeard: string[]; output: string; isError: boolean; declared: string[]; registered: string[] }> {
	const jira = fakeMcpServer("jira", TOOLS satisfies FakeTool[], exposure);
	const h = await makeSession({
		...options,
		extensions: [jira.extension, createCodemodeExtension()],
	});
	// One prompt so the MCP server has connected and its tools are registered.
	h.faux.setResponses([fauxAssistantMessage([fauxText("ready")], { stopReason: "stop" })]);
	await h.session.prompt("go");

	const code = `const r = await tools.${MCP_TOOL}({}); text("ran");`;
	h.faux.setResponses([
		fauxAssistantMessage([fauxToolCall("codemode", { code })], { stopReason: "toolUse" }),
		fauxAssistantMessage([fauxText("done")], { stopReason: "stop" }),
	]);
	await h.session.prompt("go");

	const result = h.session.messages.filter((m) => m.role === "toolResult").at(-1) as any;
	const seen = {
		serverHeard: jira.calls.map((c) => c.name),
		output: String(result.content.map((c: any) => c.text).join("\n")),
		isError: result.isError,
		declared: h.session.getActiveToolNames(),
		registered: h.session.getAllTools().map((t: { name: string }) => t.name),
	};
	h.dispose();
	return seen;
}

test("an allowlist naming only built-in tools leaves a codemode-exposure MCP tool callable from a script", async () => {
	// The allowlist is the one `--tools read,codemode` sets: no entry names or matches an MCP tool.
	const r = await scriptCallsMcp("codemode", { tools: ["read", "codemode"] });
	assert.ok(r.registered.includes(MCP_TOOL), "the tool is still registered");
	assert.deepEqual(r.serverHeard, ["transition_issue"], "and the script called it: the server heard");
	assert.ok(!r.declared.includes(MCP_TOOL), "it is not declared to the model");
});

test("the same hold for a deferred-exposure tool", async () => {
	const r = await scriptCallsMcp("deferred", { tools: ["read", "codemode"] });
	assert.deepEqual(r.serverHeard, ["transition_issue"], "deferred, like codemode, keeps script reach");
});

test("but a direct-exposure tool kept without being named is inert: neither declared nor callable", async () => {
	const r = await scriptCallsMcp("direct", { tools: ["read", "codemode"] });
	assert.ok(r.registered.includes(MCP_TOOL), "still registered");
	assert.deepEqual(r.serverHeard, [], "the script cannot reach it");
	assert.ok(!r.declared.includes(MCP_TOOL), "and it is not declared either");
	assert.match(r.output, /does not exist\. Available: read/, "the script is told what it may call");
});

test("an mcp__ pattern makes a direct-exposure tool declared, where an unnamed one was not", async () => {
	const named = await scriptCallsMcp("direct", { tools: ["read", "codemode", "mcp__jira__*"] });
	assert.ok(named.declared.includes(MCP_TOOL), "a matching entry declares it to the model");
	assert.deepEqual(named.serverHeard, ["transition_issue"], "and it stays callable from a script");

	const stillCodemode = await scriptCallsMcp("codemode", { tools: ["read", "codemode", "mcp__jira__*"] });
	assert.ok(
		!stillCodemode.declared.includes(MCP_TOOL),
		"but the pattern does not override exposure: a codemode-exposure tool stays undeclared",
	);
});

test("a hidden tool stays unreachable even when a pattern names it", async () => {
	const r = await scriptCallsMcp("hidden", { tools: ["read", "codemode", "mcp__jira__*"] });
	assert.ok(r.registered.includes(MCP_TOOL), "it is registered, as hidden always is");
	assert.deepEqual(r.serverHeard, [], "but nothing can call it");
	assert.ok(!r.declared.includes(MCP_TOOL), "and it is not declared");
});

test("excludeTools takes MCP tools too, and needs no mcp__ prefix", async () => {
	const r = await scriptCallsMcp("codemode", { tools: ["read", "codemode"], excludeTools: ["mcp__*"] });
	assert.deepEqual(r.serverHeard, [], "nothing can call it");
	assert.ok(!r.registered.includes(MCP_TOOL), "and it is not even registered");
});

test("disabledBuiltinExtensions gates built-in extensions, not an injected one", async () => {
	// This session loads the MCP extension as an explicit factory, which is the shape
	// cli.md describes as "an extension that replaces the built-in MCP support".
	const r = await scriptCallsMcp("codemode", {
		tools: ["read", "codemode"],
		resourceOptions: { disabledBuiltinExtensions: ["mcp"] },
	});
	assert.ok(r.registered.includes(MCP_TOOL), "the injected extension is unaffected, as documented");
	assert.deepEqual(r.serverHeard, ["transition_issue"], "and still callable");
});
