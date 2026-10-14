// Chapter 32, against the SHIPPED pi binary run as a child process, with a scripted model
// injected through an extension. Nothing here imports Pi internals.
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, mkdirSync, mkdtempSync, readdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { runPi } from "../harness/cli.ts";

const events = (stdout: string) => stdout.trim().split("\n").filter(Boolean).map((l) => JSON.parse(l));

test("print mode: the whole interface is the final text on stdout, and a successful run exits 0", () => {
	const r = runPi({ script: [{ text: "the final answer" }], args: ["--print", "hi"] });
	assert.equal(r.status, 0);
	assert.equal(r.stdout, "the final answer\n");
	assert.equal(r.stderr, "");
});

test("print mode: a failed final response exits non-zero, with the message on stderr and nothing on stdout", () => {
	const r = runPi({ script: [{ error: "provider exploded" }], args: ["--print", "hi"] });
	assert.notEqual(r.status, 0);
	assert.equal(r.stdout, "");
	assert.match(r.stderr, /provider exploded/);
});

test("JSON mode: the same failure is in the event stream and the exit status is 0", () => {
	const r = runPi({ script: [{ error: "provider exploded" }], args: ["--mode", "json", "hi"] });
	assert.equal(r.status, 0, "a script that checks only $? would call this a success");
	const failed = events(r.stdout).find((e) => e.type === "message_end" && e.message.role === "assistant");
	assert.equal(failed.message.stopReason, "error");
	assert.match(failed.message.errorMessage, /provider exploded/);
});

test("with stdin and stdout redirected and no mode given, Pi chooses print mode", () => {
	const r = runPi({ script: [{ text: "implicit" }], args: ["hi"] });
	assert.equal(r.status, 0);
	assert.equal(r.stdout, "implicit\n");
});

test("piped stdin is prepended to the first prompt", () => {
	const r = runPi({ script: [{ text: "ok" }], args: ["--mode", "json", "Review this change"], stdin: "diff --git a/x b/x\n+added line\n" });
	const user = events(r.stdout).find((e) => e.type === "message_end" && e.message.role === "user");
	const text = JSON.stringify(user.message.content);
	assert.ok(text.indexOf("+added line") < text.indexOf("Review this change"), "the piped text comes first");
});

test("@path includes a text file in the first prompt", () => {
	const cwd = mkdtempSync(join(tmpdir(), "pi-at-"));
	writeFileSync(join(cwd, "notes.md"), "MEETING-NOTES-MARKER");
	const r = runPi({ script: [{ text: "ok" }], args: ["--mode", "json", "@notes.md", "summarise"], cwd });
	const user = events(r.stdout).find((e) => e.type === "message_end" && e.message.role === "user");
	assert.match(JSON.stringify(user.message.content), /MEETING-NOTES-MARKER/);
});

test("`--` lets a prompt begin with a dash instead of being parsed as an option", () => {
	const r = runPi({ script: [{ text: "ok" }], args: ["--mode", "json", "--", "-5 degrees is cold"] });
	assert.equal(r.status, 0, r.stderr);
	const user = events(r.stdout).find((e) => e.type === "message_end" && e.message.role === "user");
	assert.match(JSON.stringify(user.message.content), /-5 degrees is cold/);
});

test("--tools narrows the agent: a model that asks for bash gets a failed result, and nothing runs", () => {
	const cwd = mkdtempSync(join(tmpdir(), "pi-tools-"));
	const r = runPi({
		script: [{ tool: "bash", args: { command: "touch ran.flag" } }, { text: "done" }],
		args: ["--mode", "json", "--tools", "read,grep,find,ls", "go"],
		cwd,
	});
	const result = events(r.stdout).find((e) => e.type === "tool_execution_end");
	assert.equal(result.isError, true);
	assert.equal(existsSync(join(cwd, "ran.flag")), false);
});

test("the default tool set can run bash", () => {
	const cwd = mkdtempSync(join(tmpdir(), "pi-tools-"));
	runPi({ script: [{ tool: "bash", args: { command: "touch ran.flag" } }, { text: "done" }], args: ["--print", "go"], cwd });
	assert.equal(existsSync(join(cwd, "ran.flag")), true);
});

test("--no-session writes no session file; without it a run against a real directory does", () => {
	const none = runPi({ script: [{ text: "x" }], args: ["--print", "hi"] });
	assert.equal(existsSync(join(none.agentDir, "sessions")), false);
	const kept = runPi({ script: [{ text: "x" }], args: ["--print", "hi"], session: true });
	const dir = join(kept.agentDir, "sessions");
	assert.ok(existsSync(dir));
	const files = readdirSync(dir, { recursive: true }).map(String).filter((f) => f.endsWith(".jsonl"));
	assert.equal(files.length, 1);
});
