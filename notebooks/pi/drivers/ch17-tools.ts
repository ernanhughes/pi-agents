// Chapter 17 - Tools in Depth
// Do nested calls pass the same gate, and does `deferred` exposure keep a tool registered but inactive?
// Real sessions with the tools, approval and dynamic-activation extensions; the order in which the gate saw each call; active vs registered across the activation.

import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";
import tools from "../ch17-tools/tools.ts";
import approval from "../ch17-tools/approval.ts";
import dynamic from "../ch17-tools/dynamic.ts";

const call = (name: string, args: unknown = {}) =>
	fauxAssistantMessage([fauxToolCall(name, args as any)], { stopReason: "toolUse" });
const done = () => fauxAssistantMessage([fauxText("done")]);

async function basic() {
	const h = await makeSession({ extensions: [tools] });
	h.faux.setResponses([call("run_checks", { skipTests: true }), done()]);
	await h.session.prompt("go");
	const r = h.session.messages.filter((m) => m.role === "toolResult") as any[];
	h.dispose();
	return { runChecks: r[0] };
}

async function structuredContent() {
	const h = await makeSession({ extensions: [tools] });
	h.faux.setResponses([call("failing_tests"), done()]);
	await h.session.prompt("go");
	const r = h.session.messages.filter((m) => m.role === "toolResult") as any[];
	h.dispose();
	return { failingTests: r[0] };
}

async function nested() {
	const h = await makeSession({ extensions: [tools] });
	h.faux.setResponses([call("review_diff"), done()]);
	await h.session.prompt("go");
	const r = h.session.messages.filter((m) => m.role === "toolResult") as any[];
	h.dispose();
	return { reviewDiff: r[0], content: r[0].content };
}

async function nestedGate() {
	const seen: string[] = [];
	const spy = (pi: any) => pi.on("tool_call", async (e: any) => void seen.push(e.toolName));
	const h = await makeSession({ extensions: [tools, spy] });
	h.faux.setResponses([call("review_diff"), done()]);
	await h.session.prompt("go");
	h.dispose();
	return { seen };
}

async function approvalGate() {
	const h = await makeSession({ extensions: [tools, approval] });
	h.faux.setResponses([call("run_checks", { skipTests: true }), call("failing_tests"), done()]);
	await h.session.prompt("go");
	const [checks, failing] = h.session.messages.filter((m) => m.role === "toolResult") as any[];
	h.dispose();
	return { checks, failing };
}

async function dynamicActivation() {
	const h = await makeSession({ extensions: [dynamic] });
	const initiallyActive = h.session.getActiveToolNames();
	const initiallyRegistered = h.session.getAllTools().map((t: any) => t.name);
	h.faux.setResponses([call("review_diff"), done()]);
	await h.session.prompt("go");
	const afterActive = h.session.getActiveToolNames();
	const r = h.session.messages.filter((m) => m.role === "toolResult") as any[];
	h.dispose();
	return {
		initiallyActive,
		initiallyRegistered,
		afterActive,
		reviewDiff: r[0],
	};
}

const [
	basicResult,
	structuredResult,
	nestedResult,
	nestedGateResult,
	approvalResult,
	dynamicResult,
] = await Promise.all([
	basic(),
	structuredContent(),
	nested(),
	nestedGate(),
	approvalGate(),
	dynamicActivation(),
]);

console.log(JSON.stringify({
	basic: { isError: basicResult.runChecks.isError, details: basicResult.runChecks.details },
	structured: { hasStructuredContent: !!structuredResult.failingTests.result?.structuredContent ?? false, content: structuredResult.failingTests.content?.[0]?.text ?? "" },
	nested: { isError: nestedResult.reviewDiff.isError, content: nestedResult.content, nested: nestedResult.reviewDiff.details?.nested ?? [] },
	nestedGate: { seen: nestedGateResult.seen },
	approval: { checksIsError: approvalResult.checks.isError, failingIsError: approvalResult.failing.isError, failingText: approvalResult.failing.content?.[0]?.text ?? "" },
	dynamic: { initiallyActive: dynamicResult.initiallyActive, initiallyRegistered: dynamicResult.initiallyRegistered, afterActive: dynamicResult.afterActive, reviewDiffIsError: dynamicResult.reviewDiff.isError },
}));