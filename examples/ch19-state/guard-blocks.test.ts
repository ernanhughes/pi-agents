import { test } from "node:test";
import assert from "node:assert/strict";
import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession, UiRecorder } from "../harness/session.ts";
import guardBlocks from "./guard-blocks.ts";

const write = (path: string) =>
	fauxAssistantMessage([fauxToolCall("write", { path, content: "x" })], { stopReason: "toolUse" });
const done = () => fauxAssistantMessage([fauxText("done")]);

async function blockOnce() {
	const ui = new UiRecorder();
	const h = await makeSession({ extensions: [guardBlocks], ui });
	h.faux.setResponses([write(".env"), done()]);
	await h.session.prompt("write the token");
	return { h, ui };
}

test("a protected write is blocked, the user is told, and the block is a session entry", async () => {
	const { h, ui } = await blockOnce();
	const result = h.session.messages.find((m) => m.role === "toolResult") as any;
	assert.equal(result.isError, true);
	assert.match(result.content[0].text, /protected/);
	assert.ok(ui.notifications.some((n) => n.type === "warning" && /Blocked write on \.env/.test(n.message)));

	const entry = h.session.sessionManager.getEntries().find((e: any) => e.type === "custom" && e.customType === "guard.block") as any;
	assert.equal(entry.data.tool, "write");
	h.dispose();
});

test("the entry is invisible to the model: it is never in what the provider receives", async () => {
	const { h } = await blockOnce();
	let seen = "";
	h.faux.setResponses([(ctx) => ((seen = JSON.stringify(ctx.messages)), done())]);
	await h.session.prompt("anything else?");
	assert.doesNotMatch(seen, /guard\.block/);
	assert.doesNotMatch(seen, /path matches/);
	h.dispose();
});

test("/guard-blocks reads the state back", async () => {
	const { h, ui } = await blockOnce();
	await h.session.prompt("/guard-blocks");
	assert.equal(ui.notifications.at(-1)?.message, "path matches .env");
	h.dispose();
});

test("state follows the branch: navigating to before the block makes the count drop", async () => {
	const { h, ui } = await blockOnce();
	const firstUser = h.session.sessionManager.getEntries().find((e: any) => e.type === "message" && e.message.role === "user") as any;
	await h.session.navigateTree(firstUser.parentId ?? firstUser.id, { summarize: false } as any);
	await h.session.prompt("/guard-blocks");
	console.log("after navigating:", ui.notifications.at(-1)?.message);
	assert.equal(ui.notifications.at(-1)?.message, "No blocked calls in this session");
	h.dispose();
});
