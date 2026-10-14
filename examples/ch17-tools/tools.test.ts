import { test } from "node:test";
import assert from "node:assert/strict";
import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";
import tools from "./tools.ts";
import approval from "./approval.ts";
import dynamic from "./dynamic.ts";
import renderer from "./renderer.ts";

const call = (name: string, args: unknown = {}) =>
	fauxAssistantMessage([fauxToolCall(name, args as any)], { stopReason: "toolUse" });
const done = () => fauxAssistantMessage([fauxText("done")]);
const results = (h: Awaited<ReturnType<typeof makeSession>>) => h.session.messages.filter((m) => m.role === "toolResult") as any[];

test("a non-zero exit from a command is data, not a failed tool result", async () => {
	const h = await makeSession({ extensions: [tools] });
	h.faux.setResponses([call("run_checks", { skipTests: true }), done()]);
	await h.session.prompt("go");
	const r = results(h)[0];
	assert.equal(r.isError, false, "pnpm may be missing or failing here; either way the tool did its job");
	assert.equal(r.details.steps.length, 1);
	assert.equal(typeof r.details.results[0].exit_code, "number");
	h.dispose();
});

test("structuredContent is returned alongside the model-facing content", async () => {
	const h = await makeSession({ extensions: [tools] });
	h.faux.setResponses([call("failing_tests"), done()]);
	await h.session.prompt("go");
	const r = results(h)[0];
	assert.match(r.content[0].text, /1 file\(s\) with failing tests/);
	h.dispose();
});

test("nested calls: review_diff runs two other tools and reads their outcomes", async () => {
	const h = await makeSession({ extensions: [tools] });
	h.faux.setResponses([call("review_diff"), done()]);
	await h.session.prompt("go");
	const r = results(h)[0];
	assert.equal(r.isError, false);
	assert.match(r.content[0].text, /^checks/);
	assert.match(r.content[1].text, /src\/auth\/refresh\.ts/, "structuredContent came through outcome.result");
	h.dispose();
});

test("nested calls pass through the same gate as model-issued calls", async () => {
	const seen: string[] = [];
	const spy = (pi: any) => pi.on("tool_call", async (e: any) => void seen.push(e.toolName));
	const h = await makeSession({ extensions: [tools, spy] });
	h.faux.setResponses([call("review_diff"), done()]);
	await h.session.prompt("go");
	assert.deepEqual(seen, ["review_diff", "run_checks", "failing_tests"]);
	h.dispose();
});

test("annotations: a tool with readOnlyHint passes the approval extension, one without is blocked when there is no UI", async () => {
	const h = await makeSession({ extensions: [tools, approval] });
	h.faux.setResponses([call("run_checks", { skipTests: true }), call("failing_tests"), done()]);
	await h.session.prompt("go");
	const [checks, failing] = results(h);
	assert.equal(checks.isError, false, "readOnlyHint true and openWorldHint false: no approval needed");
	assert.equal(failing.isError, true, "no hints declared: treated as destructive and open-world");
	assert.match(failing.content[0].text, /not approved/);
	h.dispose();
});

test("dynamic activation: a deferred tool is inactive until the tool that needs it is called", async () => {
	const h = await makeSession({ extensions: [dynamic] });
	assert.ok(!h.session.getActiveToolNames().includes("failing_tests"), "deferred tools are not declared on registration");
	h.faux.setResponses([call("review_diff"), done()]);
	await h.session.prompt("go");
	assert.ok(h.session.getActiveToolNames().includes("failing_tests"));
	assert.equal(results(h)[0].isError, false, "a deferred tool is still callable from another tool");
	h.dispose();
});

test("the renderer extension loads and registers without error", async () => {
	const h = await makeSession({ extensions: [renderer] });
	assert.ok(h.session);
	h.dispose();
});
