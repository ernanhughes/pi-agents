// Chapter 31 on the SHIPPED binary: one scripted run, three interfaces, one agent.
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { PI_BIN, PI_BIN_RELATIVE, RpcClient, runPi } from "../harness/cli.ts";

const SCRIPT = [{ tool: "bash", args: { command: "echo from-the-tool" } }, { text: "the answer is forty-two" }];

test("the harness spawns the entry the package publishes as `pi`, not a path into dist/", () => {
	// PI_BIN is resolved through the pinned package's own `bin` mapping, so this
	// test is what stops the claim "shipped binary" quietly becoming "some module
	// inside dist/". A path under dist/bundle is the bundled build; dist/cli.js is
	// an internal module that the bundle happens to contain.
	assert.match(PI_BIN_RELATIVE, /^dist[\\/]bundle[\\/]/, `the published entry moved: ${PI_BIN_RELATIVE}`);
	assert.ok(existsSync(PI_BIN), `${PI_BIN} does not exist`);
});

const jsonEvents = (stdout: string) => stdout.trim().split("\n").filter(Boolean).map((l) => JSON.parse(l));
const assistantTexts = (messages: any[]) =>
	messages.filter((m) => m.role === "assistant").map((m) => m.content.filter((b: any) => b.type === "text").map((b: any) => b.text).join(""));

test("the same scripted run through print, JSON and RPC gives the same final answer", async () => {
	const print = runPi({ script: SCRIPT, args: ["--print", "go"] });
	const json = runPi({ script: SCRIPT, args: ["--mode", "json", "go"] });

	const c = new RpcClient({ script: SCRIPT });
	c.send({ type: "prompt", message: "go" });
	await c.waitFor((r) => r.type === "agent_settled");
	await c.close();

	const fromJson = assistantTexts(jsonEvents(json.stdout).filter((e) => e.type === "message_end").map((e) => e.message)).at(-1);
	const fromRpc = assistantTexts(c.records.filter((e) => e.type === "message_end").map((e) => e.message)).at(-1);

	assert.equal(print.stdout.trim(), "the answer is forty-two");
	assert.equal(fromJson, "the answer is forty-two");
	assert.equal(fromRpc, "the answer is forty-two");
});

test("the agent did the same thing under each interface: the same events, in the same order", async () => {
	const kinds = (events: any[]) =>
		events.map((e) => e.type).filter((t) => ["agent_start", "turn_start", "tool_execution_start", "tool_execution_end", "turn_end", "agent_end", "agent_settled"].includes(t));

	const json = runPi({ script: SCRIPT, args: ["--mode", "json", "go"] });
	const c = new RpcClient({ script: SCRIPT });
	c.send({ type: "prompt", message: "go" });
	await c.waitFor((r) => r.type === "agent_settled");
	await c.close();

	const a = kinds(jsonEvents(json.stdout));
	const b = kinds(c.records.filter((r) => r.type !== "response"));
	assert.deepEqual(a, b);
	assert.ok(a.includes("tool_execution_end"), "the tool ran in both");
});

test("what differs is the observer: print has no events, JSON has no responses, RPC has both", async () => {
	const print = runPi({ script: SCRIPT, args: ["--print", "go"] });
	assert.equal(print.stdout.trim().split("\n").length, 1, "one string and nothing else");

	const json = runPi({ script: SCRIPT, args: ["--mode", "json", "go"] });
	assert.ok(!jsonEvents(json.stdout).some((e) => e.type === "response"));

	const c = new RpcClient({ script: SCRIPT });
	c.send({ id: "x", type: "prompt", message: "go" });
	await c.waitFor((r) => r.type === "agent_settled");
	assert.ok(c.records.some((r) => r.type === "response" && r.id === "x"));
	assert.ok(c.records.some((r) => r.type === "message_end"));
	await c.close();
});

test("the failure contract differs by interface, and nothing else about the run does", async () => {
	const fail = [{ error: "provider exploded" }];
	assert.notEqual(runPi({ script: fail, args: ["--print", "go"] }).status, 0, "print: the exit status");
	assert.equal(runPi({ script: fail, args: ["--mode", "json", "go"] }).status, 0, "JSON: the stream");

	const c = new RpcClient({ script: fail });
	c.send({ type: "prompt", message: "go" });
	await c.waitFor((r) => r.type === "agent_settled");
	const failed = c.records.find((r) => r.type === "message_end" && r.message.role === "assistant");
	assert.equal(failed.message.stopReason, "error", "RPC: the stream, and the command itself still succeeded");
	await c.close();
});
