// Chapter 35 - RPC
// Does a successful `prompt` response mean finished, and does the UI subprotocol block on the client?
// Real line-framed JSONL against the shipped binary: two ids matched by id, disposition started, agent_end before agent_settled, the UI request/answer pair, a throwing handler.

import { fileURLToPath } from "node:url";
import { RpcClient } from "../harness/cli.ts";

const EXT = fileURLToPath(new URL("../harness/rpc-extensions.ts", import.meta.url));
const client = (script: any[], more: Record<string, unknown> = {}) => new RpcClient({ script, extraExtensions: [EXT], ...more } as any);

async function idMatching() {
	const c = client([{ text: "x" }]);
	c.send({ id: "a", type: "get_state" });
	c.send({ id: "b", type: "get_available_models" });
	const [a, b] = await Promise.all([c.waitFor((r: any) => r.id === "a"), c.waitFor((r: any) => r.id === "b")]);
	await c.close();
	return { aCommand: a.command, bCommand: b.command, bothSucceeded: a.success && b.success };
}

async function promptMeansAccepted() {
	const c = client([{ text: "the answer" }]);
	c.send({ id: "p1", type: "prompt", message: "hi" });
	const resp = await c.waitFor((r: any) => r.id === "p1");
	const disposition = resp.data?.disposition;
	await c.waitFor((r: any) => r.type === "agent_settled");
	const at = (pred: (r: any) => boolean) => c.records.findIndex(pred);
	const responseBeforeRun = at((r: any) => r.id === "p1") < at((r: any) => r.type === "agent_start");
	await c.close();
	return { disposition, responseBeforeRun };
}

async function agentEndIsNotTheEnd() {
	const c = client([{ text: "x" }]);
	c.send({ type: "prompt", message: "hi" });
	await c.waitFor((r: any) => r.type === "agent_settled");
	const types = c.records.map((r: any) => r.type);
	await c.close();
	return { agentEndBeforeSettled: types.indexOf("agent_end") < types.indexOf("agent_settled"), last: types.at(-1) };
}

async function malformedJson() {
	const c = client([]);
	c.sendRaw("{not json\n");
	const r = await c.waitFor((r: any) => r.command === "parse");
	await c.close();
	return { success: r.success, hasId: "id" in r };
}

async function unknownCommand() {
	const c = client([]);
	c.send({ id: "u", type: "no_such_command" });
	const r = await c.waitFor((r: any) => r.id === "u");
	c.send({ id: "after", type: "get_state" });
	const after = await c.waitFor((r: any) => r.id === "after");
	await c.close();
	return { unknownSuccess: r.success, stillServing: after.success };
}

async function uiSubprotocol() {
	const c = client([]);
	c.send({ id: "ask", type: "prompt", message: "/ask" });
	const req = await c.waitFor((r: any) => r.type === "extension_ui_request" && r.method === "confirm");
	const blockedBeforeAnswer = !c.records.some((r: any) => r.type === "extension_ui_request" && r.method === "notify");
	c.send({ type: "extension_ui_response", id: req.id, confirmed: true });
	const note = await c.waitFor((r: any) => r.type === "extension_ui_request" && r.method === "notify");
	const noNormalResponse = !c.records.some((r: any) => r.id === req.id && r.type === "response");
	await c.close();
	return { title: req.title, blockedBeforeAnswer, noteMessage: note.message, noNormalResponse };
}

async function entriesCursor() {
	const c = client([{ text: "one" }, { text: "two" }]);
	c.send({ type: "prompt", message: "first" });
	await c.waitFor((r: any) => r.type === "agent_settled");
	c.send({ id: "e1", type: "get_entries" });
	const all = await c.waitFor((r: any) => r.id === "e1");
	const cursor = all.data.entries.at(-1).id;
	const leafMatchesCursor = all.data.leafId === cursor;
	c.records.length = 0;
	c.send({ type: "prompt", message: "second" });
	await c.waitFor((r: any) => r.type === "agent_settled");
	c.send({ id: "e2", type: "get_entries", since: cursor });
	const newer = await c.waitFor((r: any) => r.id === "e2");
	c.send({ id: "e3", type: "get_entries", since: "no-such-id" });
	const bad = await c.waitFor((r: any) => r.id === "e3");
	await c.close();
	return { leafMatchesCursor, newerHasEntries: newer.data.entries.length > 0, invalidCursorFails: bad.success === false };
}

async function extensionError() {
	const c = client([{ text: "still answered" }], { env: { PI_TEST_THROW: "1" } });
	c.send({ type: "prompt", message: "hi" });
	const err = await c.waitFor((r: any) => r.type === "extension_error");
	await c.waitFor((r: any) => r.type === "agent_settled");
	await c.close();
	return { event: err.event, errorMatches: /handler bug/.test(err.error) };
}

const [ids, accepted, end, malformed, unknown, ui, cursor, err] = await Promise.all([
	idMatching(),
	promptMeansAccepted(),
	agentEndIsNotTheEnd(),
	malformedJson(),
	unknownCommand(),
	uiSubprotocol(),
	entriesCursor(),
	extensionError(),
]);

console.log(JSON.stringify({
	idMatching: ids,
	promptAccepted: accepted,
	agentEnd: end,
	malformed,
	unknown,
	ui,
	cursor,
	extensionError: err,
}));