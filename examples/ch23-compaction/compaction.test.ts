import { test } from "node:test";
import assert from "node:assert/strict";
import { fauxAssistantMessage, fauxText } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";
import customSummary from "./custom-summary.ts";
import cancelCompaction from "./cancel-compaction.ts";

const say = (t: string) => fauxAssistantMessage([fauxText(t)]);

// keepRecentTokens is small so that a short scripted conversation has something to summarise.
async function longSession(extensions: Parameters<typeof makeSession>[0]["extensions"]) {
	const h = await makeSession({ extensions, settings: { compaction: { enabled: false, keepRecentTokens: 800, reserveTokens: 1000 } } });
	for (let i = 0; i < 5; i++) {
		h.faux.setResponses([say(`answer ${i}: ${"the schema has a billing table. ".repeat(40)}`)]);
		await h.session.prompt(`question ${i} about the billing schema`);
	}
	return h;
}

const compactions = (h: Awaited<ReturnType<typeof longSession>>) =>
	h.session.sessionManager.getEntries().filter((e: any) => e.type === "compaction") as any[];

test("an extension can supply the summary, and Pi still chooses the cut point", async () => {
	const h = await longSession([customSummary]);
	await h.session.compact();
	const [entry] = compactions(h);
	assert.ok(entry, "a compaction entry was appended");
	assert.match(entry.summary, /^Custom summary of \d+ message\(s\)/);
	assert.ok(entry.firstKeptEntryId, "Pi's own cut point was kept");
	assert.equal(entry.fromHook, true, "marked as extension-provided");
	h.dispose();
});

test("the next request is built from the summary plus the kept messages, not the full history", async () => {
	const h = await longSession([customSummary]);
	await h.session.compact();
	let sent: any[] = [];
	h.faux.setResponses([(ctx) => ((sent = [...ctx.messages]), say("ok"))]);
	await h.session.prompt("and now?");

	assert.match(JSON.stringify(sent), /Custom summary of/);
	// The compaction summary is itself delivered as a user-role message, so leave it out.
	const userTexts = sent.filter((m) => m.role === "user").map((m) => JSON.stringify(m.content)).filter((t) => !t.includes("Custom summary of"));
	assert.ok(!userTexts.some((t) => t.includes("question 0")), "the oldest question is no longer sent as a message");
	assert.ok(userTexts.some((t) => t.includes("question 4")), "the most recent ones are kept");
	h.dispose();
});

test("compaction replaces what the model sees and deletes nothing from the file", async () => {
	const h = await longSession([customSummary]);
	const before = h.session.sessionManager.getEntries().filter((e: any) => e.type === "message").length;
	await h.session.compact();
	const after = h.session.sessionManager.getEntries().filter((e: any) => e.type === "message").length;
	assert.equal(after, before, "every message entry is still stored");
	h.dispose();
});

test("an extension can cancel a manual compaction", async () => {
	const h = await longSession([cancelCompaction]);
	await assert.rejects(h.session.compact(), /./);
	assert.equal(compactions(h).length, 0);
	h.dispose();
});
