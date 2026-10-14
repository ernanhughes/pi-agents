// Chapter 35, against the SHIPPED pi binary in --mode rpc, driven by a hand-written JSONL client.
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { RpcClient, PI_BIN, baseArgs, cliEnv } from "../harness/cli.ts";

const EXT = fileURLToPath(new URL("../harness/rpc-extensions.ts", import.meta.url));
const client = (script: any[], more: Record<string, unknown> = {}) => new RpcClient({ script, extraExtensions: [EXT], ...more } as any);

test("responses repeat the command id, and two outstanding commands are matched by id, not by order", async () => {
	const c = client([{ text: "x" }]);
	c.send({ id: "a", type: "get_state" });
	c.send({ id: "b", type: "get_available_models" });
	const [a, b] = await Promise.all([c.waitFor((r) => r.id === "a"), c.waitFor((r) => r.id === "b")]);
	assert.equal(a.command, "get_state");
	assert.equal(b.command, "get_available_models");
	assert.equal(a.success && b.success, true);
	await c.close();
});

test("a successful prompt response means accepted, not finished: disposition is started, and the run follows", async () => {
	const c = client([{ text: "the answer" }]);
	c.send({ id: "p1", type: "prompt", message: "hi" });
	const resp = await c.waitFor((r) => r.id === "p1");
	assert.deepEqual(resp.data, { disposition: "started" });
	await c.waitFor((r) => r.type === "agent_settled");
	const at = (pred: (r: any) => boolean) => c.records.findIndex(pred);
	assert.ok(at((r) => r.id === "p1") < at((r) => r.type === "agent_start"), "the response comes before the run's first event");
	await c.close();
});

test("session events carry no command id", async () => {
	const c = client([{ text: "x" }]);
	c.send({ id: "p1", type: "prompt", message: "hi" });
	await c.waitFor((r) => r.type === "agent_settled");
	for (const r of c.records.filter((r) => r.type !== "response")) assert.ok(!("id" in r), `${r.type} has no id`);
	await c.close();
});

test("agent_end is not the end: agent_settled follows it, and is what a client waits for", async () => {
	const c = client([{ text: "x" }]);
	c.send({ type: "prompt", message: "hi" });
	await c.waitFor((r) => r.type === "agent_settled");
	const types = c.records.map((r) => r.type);
	assert.ok(types.indexOf("agent_end") < types.indexOf("agent_settled"));
	await c.close();
});

test("prompt while streaming without streamingBehavior is an error response; with steer it is queued", async () => {
	const c = client([{ tool: "bash", args: { command: "sleep 1" } }, { text: "a" }, { text: "b" }]);
	c.send({ id: "p1", type: "prompt", message: "start" });
	await c.waitFor((r) => r.type === "tool_execution_start");
	c.send({ id: "p2", type: "prompt", message: "second, no behaviour" });
	const bad = await c.waitFor((r) => r.id === "p2");
	assert.equal(bad.success, false);
	c.send({ id: "p3", type: "prompt", message: "third", streamingBehavior: "steer" });
	const ok = await c.waitFor((r) => r.id === "p3");
	assert.equal(ok.success, true);
	assert.equal(ok.data.disposition, "queued");
	await c.waitFor((r) => r.type === "agent_settled");
	await c.close();
});

test("malformed JSON produces a parse response with no request id", async () => {
	const c = client([]);
	c.sendRaw("{not json\n");
	const r = await c.waitFor((r) => r.command === "parse");
	assert.equal(r.success, false);
	assert.ok(!("id" in r));
	await c.close();
});

test("an unknown command is an error response, not a crash", async () => {
	const c = client([]);
	c.send({ id: "u", type: "no_such_command" });
	const r = await c.waitFor((r) => r.id === "u");
	assert.equal(r.success, false);
	c.send({ id: "after", type: "get_state" });
	assert.equal((await c.waitFor((r) => r.id === "after")).success, true, "the process is still serving");
	await c.close();
});

test("closing stdin is an orderly shutdown", async () => {
	const c = client([]);
	c.send({ id: "s", type: "get_state" });
	await c.waitFor((r) => r.id === "s");
	assert.equal(await c.close(), 0);
});

test("RPC mode rejects @file prompt arguments", () => {
	const dir = mkdtempSync(join(tmpdir(), "pi-rpc-at-"));
	writeFileSync(join(dir, "x.md"), "x");
	const r = spawnSync(process.execPath, [PI_BIN, ...baseArgs({ approve: "yes" }), "--mode", "rpc", "@x.md"], {
		cwd: dir,
		env: cliEnv({ script: [] }, mkdtempSync(join(tmpdir(), "a-"))),
		encoding: "utf8",
		input: "",
		timeout: 30000,
	});
	assert.notEqual(r.status, 0);
	assert.match(r.stderr + r.stdout, /@file|RPC/i);
});

test("get_commands lists extension commands, and not the built-in terminal commands", async () => {
	const c = client([]);
	c.send({ id: "c", type: "get_commands" });
	const r = await c.waitFor((r) => r.id === "c");
	const names = r.data.commands.map((x: any) => x.name);
	assert.ok(names.includes("ask"));
	assert.ok(!names.includes("settings") && !names.includes("hotkeys"));
	await c.close();
});

test("extension UI subprotocol: a dialog blocks on the client, and the response uses the request id", async () => {
	const c = client([]);
	c.send({ id: "ask", type: "prompt", message: "/ask" });
	const req = await c.waitFor((r) => r.type === "extension_ui_request" && r.method === "confirm");
	assert.equal(req.title, "Clear session?");
	assert.ok(typeof req.id === "string");
	assert.ok(!c.records.some((r) => r.type === "extension_ui_request" && r.method === "notify"), "still waiting: the extension has no answer yet");

	c.send({ type: "extension_ui_response", id: req.id, confirmed: true });
	const note = await c.waitFor((r) => r.type === "extension_ui_request" && r.method === "notify");
	assert.equal(note.message, "confirmed");
	assert.ok(!c.records.some((r) => r.id === req.id && r.type === "response"), "a UI response does not produce a normal command response");
	await c.close();
});

test("extension UI subprotocol: cancelling delivers false to a confirm", async () => {
	const c = client([]);
	c.send({ type: "prompt", message: "/ask" });
	const req = await c.waitFor((r) => r.type === "extension_ui_request" && r.method === "confirm");
	c.send({ type: "extension_ui_response", id: req.id, cancelled: true });
	const note = await c.waitFor((r) => r.type === "extension_ui_request" && r.method === "notify");
	assert.equal(note.message, "declined");
	await c.close();
});

test("extension_error is an RPC record: a handler that throws is reported, and the run continues", async () => {
	const c = client([{ text: "still answered" }], { env: { PI_TEST_THROW: "1" } });
	c.send({ type: "prompt", message: "hi" });
	const err = await c.waitFor((r) => r.type === "extension_error");
	assert.equal(err.event, "agent_start");
	assert.match(err.error, /handler bug/);
	await c.waitFor((r) => r.type === "agent_settled");
	await c.close();
});

test("get_entries uses an entry id as a durable cursor and reports the leaf", async () => {
	const c = client([{ text: "one" }, { text: "two" }]);
	c.send({ type: "prompt", message: "first" });
	await c.waitFor((r) => r.type === "agent_settled");
	c.send({ id: "e1", type: "get_entries" });
	const all = await c.waitFor((r) => r.id === "e1");
	const cursor = all.data.entries.at(-1).id;
	assert.equal(all.data.leafId, cursor);

	c.records.length = 0;
	c.send({ type: "prompt", message: "second" });
	await c.waitFor((r) => r.type === "agent_settled");
	c.send({ id: "e2", type: "get_entries", since: cursor });
	const newer = await c.waitFor((r) => r.id === "e2");
	assert.ok(newer.data.entries.length > 0);
	assert.ok(!newer.data.entries.some((e: any) => e.id === cursor), "strictly after the cursor");
	c.send({ id: "e3", type: "get_entries", since: "no-such-id" });
	assert.equal((await c.waitFor((r) => r.id === "e3")).success, false);
	await c.close();
});
