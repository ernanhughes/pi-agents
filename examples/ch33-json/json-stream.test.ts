// Chapter 33, against the SHIPPED pi binary in --mode json.
import { test } from "node:test";
import assert from "node:assert/strict";
import { runPi } from "../harness/cli.ts";

const LS = String.fromCharCode(0x2028);
const PS = String.fromCharCode(0x2029);
const run = (script: Parameters<typeof runPi>[0]["script"], extra: string[] = []) => runPi({ script, args: ["--mode", "json", ...extra, "go"] });
const parse = (stdout: string) => stdout.split("\n").filter(Boolean).map((l) => JSON.parse(l));

test("the first record is the session header, version 3, and it is not part of the tree", () => {
	const [header] = parse(run([{ text: "hi" }]).stdout);
	assert.equal(header.type, "session");
	assert.equal(header.version, 3);
	assert.ok(!("parentId" in header));
});

test("every record is one JSON object terminated by LF, and stdout carries nothing else", () => {
	const r = run([{ text: "hi" }]);
	assert.ok(r.stdout.endsWith("\n"));
	for (const line of r.stdout.split("\n").filter(Boolean)) assert.doesNotThrow(() => JSON.parse(line));
	assert.equal(r.stderr, "", "diagnostics go to stderr, and there were none");
});

test("U+2028 inside a string is legal JSON and is not a record boundary: a line reader would split it", () => {
	const r = run([{ text: `before${LS}after` }]);
	assert.ok(r.stdout.includes(LS), "the separator is emitted raw, which is exactly why readline is unsafe for this stream");
	const records = r.stdout.split("\n").filter(Boolean);
	for (const line of records) assert.doesNotThrow(() => JSON.parse(line), "splitting on LF only keeps every record whole");
	const naive = r.stdout.split(new RegExp("\r\n|\r|\n|" + LS + "|" + PS)).filter(Boolean);
	assert.ok(naive.length > records.length, "splitting on Unicode separators too produces more, broken, records");
	assert.ok(naive.some((l) => { try { JSON.parse(l); return false; } catch { return true; } }));
});

test("the run lifecycle: agent_start first, agent_end then agent_settled last", () => {
	const types = parse(run([{ text: "hi" }]).stdout).map((e) => e.type);
	assert.ok(types.indexOf("agent_start") < types.indexOf("turn_start"));
	assert.equal(types.at(-1), "agent_settled");
	assert.equal(types.at(-2), "agent_end");
});

test("message_update is delta-only on the wire: no cumulative message and no partial snapshots", () => {
	const updates = parse(run([{ text: "a reasonably long answer for several deltas" }]).stdout).filter((e) => e.type === "message_update");
	assert.ok(updates.length > 1);
	for (const u of updates) {
		assert.ok(!("message" in u), "the cumulative message is omitted");
		assert.ok(!("partial" in u.assistantMessageEvent), "and so is every partial snapshot");
		assert.ok("usage" in u);
	}
});

test("reconstruction: buffered deltas, then text_end content, then message_end, all agree", () => {
	const ev = parse(run([{ text: "the quick brown fox jumps" }]).stdout);
	const deltas = ev.filter((e) => e.type === "message_update" && e.assistantMessageEvent.type === "text_delta").map((e) => e.assistantMessageEvent.delta).join("");
	const end = ev.find((e) => e.type === "message_update" && e.assistantMessageEvent.type === "text_end");
	const final = ev.filter((e) => e.type === "message_end" && e.message.role === "assistant").at(-1);
	assert.equal(deltas, "the quick brown fox jumps");
	assert.equal(end.assistantMessageEvent.content, deltas);
	assert.equal(final.message.content.find((b: any) => b.type === "text").text, deltas);
});

test("the inner assistantMessageEvent vocabulary uses contentIndex, and provider-level start/done/error are not emitted as message_update", () => {
	const inner = parse(run([{ text: "hello" }]).stdout).filter((e) => e.type === "message_update").map((e) => e.assistantMessageEvent);
	const kinds = new Set(inner.map((i) => i.type));
	assert.ok(kinds.has("text_start") && kinds.has("text_delta") && kinds.has("text_end"));
	for (const k of ["start", "done", "error"]) assert.ok(!kinds.has(k), `${k} becomes message_start / message_end`);
	for (const i of inner) assert.equal(typeof i.contentIndex, "number");
});

test("tool execution events carry the call id, name, args and the result", () => {
	const ev = parse(run([{ tool: "bash", args: { command: "echo hi" } }, { text: "done" }]).stdout);
	const start = ev.find((e) => e.type === "tool_execution_start");
	const end = ev.find((e) => e.type === "tool_execution_end");
	assert.equal(start.toolName, "bash");
	assert.deepEqual(start.args, { command: "echo hi" });
	assert.equal(end.toolCallId, start.toolCallId);
	assert.equal(end.isError, false);
	assert.match(JSON.stringify(end.result), /hi/);
});

test("turn_end carries the assistant message and its tool results", () => {
	const ev = parse(run([{ tool: "bash", args: { command: "echo hi" } }, { text: "done" }]).stdout);
	const first = ev.find((e) => e.type === "turn_end");
	assert.equal(first.message.role, "assistant");
	assert.equal(first.toolResults.length, 1);
});

test("a failed response is in the stream as a message_end with stopReason error, and the run still settles", () => {
	const ev = parse(run([{ error: "provider exploded" }]).stdout);
	assert.equal(ev.find((e) => e.type === "message_end" && e.message.role === "assistant").message.stopReason, "error");
	assert.equal(ev.at(-1).type, "agent_settled");
});

test("extension_error is not a JSON-mode record (it is RPC-only)", () => {
	const types = new Set(parse(run([{ text: "hi" }]).stdout).map((e) => e.type));
	assert.ok(!types.has("extension_error"));
	assert.ok(!types.has("bash_execution_update"));
});
