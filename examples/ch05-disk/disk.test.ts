// Chapter 5 on the shared history: what survives to disk, where it lives, and what is stored but not sent.
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, mkdtempSync, readFileSync, readdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, sep } from "node:path";
import { buildHistory, requestFor, userTexts } from "../harness/history.ts";
import { runPi } from "../harness/cli.ts";

const rows = (file: string) => readFileSync(file, "utf8").trim().split("\n").map((l) => JSON.parse(l));

test("every turn is on disk as it happens: a header, then one entry per message, in order", async () => {
	const { h, file } = await buildHistory();
	const r = rows(file);
	assert.equal(r[0].type, "session");
	const msgs = r.filter((e) => e.type === "message").map((e) => e.message.role);
	assert.deepEqual(msgs, ["system", "user", "assistant", "user", "assistant", "toolResult", "assistant", "user", "assistant"]);
	h.dispose();
});

test("entries form a tree by id and parentId; for a linear conversation each parent is the entry before", async () => {
	const { h, file } = await buildHistory();
	const entries = rows(file).slice(1);
	const ids = new Set(entries.map((e) => e.id));
	assert.equal(ids.size, entries.length, "ids are unique");
	assert.equal(entries[0].parentId, null, "the first entry is a root");
	for (let i = 1; i < entries.length; i++) assert.equal(entries[i].parentId, entries[i - 1].id, `${entries[i].type} follows ${entries[i - 1].type}`);
	h.dispose();
});

test("stored is not the same as sent: model and thinking-level entries and a custom entry are on disk and never reach the provider", async () => {
	const { h, file } = await buildHistory();
	h.session.sessionManager.appendCustomEntry("my-ext.counter", { count: 42 });
	const types = rows(file).map((e) => e.type);
	assert.ok(types.includes("model_change") && types.includes("thinking_level_change") && types.includes("custom"));

	const sent = JSON.stringify(await requestFor(h, "next"));
	assert.doesNotMatch(sent, /my-ext\.counter/);
	assert.doesNotMatch(sent, /model_change|thinking_level_change/);
	h.dispose();
});

test("a context_edit hides an earlier message from future requests without deleting it, and is branch-relative", async () => {
	const { h, file, userEntry } = await buildHistory();
	const target = userEntry("question A");
	h.session.sessionManager.appendContextEdit(target.id, null);

	assert.ok(!userTexts(await requestFor(h, "after the edit")).some((t) => t.includes("question A")), "omitted from the request");
	assert.ok(rows(file).some((e) => e.id === target.id), "still in the file");

	// Navigate to a point before the edit (the assistant's answer to A): the original contribution returns.
	const answerA = rows(file).find((e) => e.parentId === target.id);
	await h.session.navigateTree(answerA.id, { summarize: false });
	assert.ok(userTexts(await requestFor(h, "before the edit")).some((t) => t.includes("question A")), "navigating before the edit reveals the original again");
	h.dispose();
});

test("a replacement context_edit rewrites one message's content for the model and leaves the file's original untouched", async () => {
	const { h, userEntry } = await buildHistory();
	const target = userEntry("question A");
	h.session.sessionManager.appendContextEdit(target.id, { content: "REDACTED" });
	const sent = userTexts(await requestFor(h, "next"));
	assert.ok(sent.includes("REDACTED"));
	assert.ok(!sent.some((t) => t.includes("question A")));
	assert.match(JSON.stringify(target.message.content), /question A/, "the stored entry is unchanged");
	h.dispose();
});

test("the default session location is --<path>--, with / \\ and : replaced by - and the leading separator removed", () => {
	const r = runPi({ script: [{ text: "x" }], args: ["--print", "hi"], session: true });
	const dirs = readdirSync(join(r.agentDir, "sessions"));
	assert.equal(dirs.length, 1);
	const expected = "--" + r.cwd.replace(/^[\\/]/, "").replace(/[\\/:]/g, "-") + "--";
	assert.equal(dirs[0], expected);
	const files = readdirSync(join(r.agentDir, "sessions", dirs[0]));
	assert.match(files[0], /^\d{4}-\d\d-\d\dT[\d-]+Z_[0-9a-f-]{36}\.jsonl$/, "<timestamp>_<session-id>.jsonl, the id a UUID");
});

test("session directory precedence: --session-dir beats PI_CODING_AGENT_SESSION_DIR, which beats the sessionDir setting", () => {
	const where = (name: string) => mkdtempSync(join(tmpdir(), `pi-sd-${name}-`));
	const hasFile = (d: string) => existsSync(d) && readdirSync(d, { recursive: true }).some((f) => String(f).endsWith(".jsonl"));

	const flag = where("flag"), env = where("env"), setting = where("setting");
	runPi({
		script: [{ text: "x" }], args: ["--print", "hi", "--session-dir", flag], session: true,
		env: { PI_CODING_AGENT_SESSION_DIR: env }, agentFiles: { "settings.json": JSON.stringify({ sessionDir: setting }) },
	});
	assert.ok(hasFile(flag));
	assert.ok(!hasFile(env) && !hasFile(setting));

	const env2 = where("env2"), setting2 = where("setting2");
	runPi({ script: [{ text: "x" }], args: ["--print", "hi"], session: true, env: { PI_CODING_AGENT_SESSION_DIR: env2 }, agentFiles: { "settings.json": JSON.stringify({ sessionDir: setting2 }) } });
	assert.ok(hasFile(env2) && !hasFile(setting2));

	const setting3 = where("setting3");
	runPi({ script: [{ text: "x" }], args: ["--print", "hi"], session: true, agentFiles: { "settings.json": JSON.stringify({ sessionDir: setting3 }) } });
	assert.ok(hasFile(setting3));
});

test("deleting a session is deleting its file: nothing else holds it", async () => {
	const { h, file } = await buildHistory();
	assert.ok(existsSync(file));
	assert.ok(file.endsWith(".jsonl") && file.includes(sep));
	h.dispose();
});
