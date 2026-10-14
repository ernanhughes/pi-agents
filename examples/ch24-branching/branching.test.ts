// Chapter 24 on the shared history: what changes when history branches.
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { fauxAssistantMessage, fauxText } from "@earendil-works/pi-ai";
import { buildHistory, requestFor, userTexts } from "../harness/history.ts";
import { RpcClient } from "../harness/cli.ts";

const text = (e: any) => JSON.stringify(e.message.content);

test("/tree on a user message returns its text for editing and moves the leaf to its parent", async () => {
	const { h, userEntry } = await buildHistory();
	const b = userEntry("question B");
	const r = await h.session.navigateTree(b.id, { summarize: false });
	assert.equal(r.cancelled, false);
	assert.match(r.editorText ?? "", /question B/, "the text goes back in the editor");
	assert.equal(h.session.sessionManager.getLeafId(), b.parentId, "the new branch forks from the message's parent");
	h.dispose();
});

test("/tree on an assistant response continues after it, with an empty editor", async () => {
	const { h, entries, userEntry } = await buildHistory();
	const answerA = entries().find((e) => e.parentId === userEntry("question A").id);
	const r = await h.session.navigateTree(answerA.id, { summarize: false });
	assert.ok(!r.editorText);
	assert.equal(h.session.sessionManager.getLeafId(), answerA.id);
	h.dispose();
});

test("submitting an edited prompt makes a sibling: two children of the same parent, one session file", async () => {
	const { h, file, entries, userEntry } = await buildHistory();
	const b = userEntry("question B");
	await h.session.navigateTree(b.id, { summarize: false });
	h.faux.setResponses([fauxAssistantMessage([fauxText("answer to the edited B")])]);
	await h.session.prompt("question B, edited");

	const siblings = entries().filter((e) => e.parentId === b.parentId && e.type === "message");
	assert.equal(siblings.length, 2, "the original and the edit hang from the same parent");
	assert.ok(existsSync(file) && readFileSync(file, "utf8").includes("question B, edited"), "in the same file");
	h.dispose();
});

test("the abandoned branch is not sent, and is not gone", async () => {
	const { h, entries, userEntry } = await buildHistory();
	await h.session.navigateTree(userEntry("question B").id, { summarize: false });
	const sent = userTexts(await requestFor(h, "question B, edited"));
	assert.ok(!sent.some((t) => t.includes("question C")));
	assert.ok(entries().some((e) => e.type === "message" && text(e).includes("question C")));
	h.dispose();
});

test("leaving a branch can attach a summary of it: a branch_summary entry with parentId where you land and fromId where you left", async () => {
	const summarise = (pi: any) =>
		pi.on("session_before_tree", async () => ({ summary: { summary: "Summary of the abandoned path: asked B and C." } }));
	const { h, entries, userEntry } = await buildHistory({ extensions: [summarise] } as any);
	const leftFrom = h.session.sessionManager.getLeafId();
	const b = userEntry("question B");
	const r = await h.session.navigateTree(b.id, { summarize: true });

	const summary = entries().find((e) => e.type === "branch_summary");
	assert.ok(summary, "an entry was written");
	assert.equal(summary.fromId, leftFrom, "fromId is the previous leaf, the one you left");
	assert.equal(summary.parentId, b.parentId, "parentId is where the new branch continues from");
	assert.equal(r.summaryEntry?.id, summary.id);
	assert.ok(entries().some((e) => e.id === leftFrom), "the abandoned entries are still in the tree");
	h.dispose();
});

test("the summary reaches the model on the new branch, and the abandoned messages still do not", async () => {
	const summarise = (pi: any) => pi.on("session_before_tree", async () => ({ summary: { summary: "BRANCH-SUMMARY-MARKER" } }));
	const { h, userEntry } = await buildHistory({ extensions: [summarise] } as any);
	await h.session.navigateTree(userEntry("question B").id, { summarize: true });
	const sent = await requestFor(h, "edited B");
	assert.match(JSON.stringify(sent), /BRANCH-SUMMARY-MARKER/);
	assert.ok(!userTexts(sent).some((t) => t.includes("question C")));
	h.dispose();
});

test("the tree is real data: getTree() shows both branches under their shared parent", async () => {
	const { h, userEntry } = await buildHistory();
	const b = userEntry("question B");
	await h.session.navigateTree(b.id, { summarize: false });
	h.faux.setResponses([fauxAssistantMessage([fauxText("x")])]);
	await h.session.prompt("question B, edited");

	const find = (nodes: any[], id: string): any => {
		for (const n of nodes) { if (n.entry.id === id) return n; const f = find(n.children, id); if (f) return f; }
	};
	const parent = find(h.session.sessionManager.getTree(), b.parentId);
	assert.equal(parent.children.length, 2);
	h.dispose();
});

test("labels are bookmarks on entries and appear on the tree node", async () => {
	const { h, userEntry } = await buildHistory();
	const a = userEntry("question A");
	h.session.sessionManager.appendLabelChange(a.id, "the good start");
	const find = (nodes: any[]): any => { for (const n of nodes) { if (n.entry.id === a.id) return n; const f = find(n.children); if (f) return f; } };
	assert.equal(find(h.session.sessionManager.getTree()).label, "the good start");
	h.session.sessionManager.appendLabelChange(a.id, undefined);
	assert.equal(find(h.session.sessionManager.getTree()).label, undefined, "setting it to undefined clears it");
	h.dispose();
});

// ---- /fork and /clone, on the shipped binary over RPC ----

async function rpcWithHistory() {
	const c = new RpcClient({ script: [{ text: "answer one" }, { text: "answer two" }, { text: "answer three" }], session: true });
	for (const m of ["first prompt", "second prompt"]) {
		c.send({ type: "prompt", message: m });
		await c.waitFor((r) => r.type === "agent_settled" && c.records.filter((x) => x.type === "agent_settled").length === (m === "first prompt" ? 1 : 2));
	}
	return c;
}

test("RPC: get_fork_messages lists the user prompts, and fork starts a NEW session file whose header names its parent", async () => {
	const c = await rpcWithHistory();
	c.send({ id: "s1", type: "get_state" });
	const before = (await c.waitFor((r) => r.id === "s1")).data.sessionFile;

	c.send({ id: "f1", type: "get_fork_messages" });
	const msgs = (await c.waitFor((r) => r.id === "f1")).data.messages;
	assert.deepEqual(msgs.map((m: any) => m.text), ["first prompt", "second prompt"]);

	c.send({ id: "f2", type: "fork", entryId: msgs[1].entryId });
	const fork = await c.waitFor((r) => r.id === "f2");
	assert.equal(fork.success, true);
	assert.equal(fork.data.cancelled, false);
	assert.equal(fork.data.text, "second prompt", "the original prompt text comes back to be edited");

	c.send({ id: "s2", type: "get_state" });
	const after = (await c.waitFor((r) => r.id === "s2")).data.sessionFile;
	assert.notEqual(after, before, "a separate file");
	const header = JSON.parse(readFileSync(after, "utf8").split("\n")[0]);
	assert.equal(header.type, "session");
	assert.equal(header.parentSession, before, "the header is the only durable record of where it came from");
	await c.close();
});

test("RPC: clone copies the active branch into a new session", async () => {
	const c = await rpcWithHistory();
	c.send({ id: "s1", type: "get_state" });
	const before = (await c.waitFor((r) => r.id === "s1")).data.sessionFile;
	c.send({ id: "c1", type: "clone" });
	assert.equal((await c.waitFor((r) => r.id === "c1")).success, true);
	c.send({ id: "s2", type: "get_state" });
	const after = (await c.waitFor((r) => r.id === "s2")).data.sessionFile;
	assert.notEqual(after, before);
	const text = readFileSync(after, "utf8");
	assert.match(text, /first prompt/);
	assert.match(text, /second prompt/);
	await c.close();
});
