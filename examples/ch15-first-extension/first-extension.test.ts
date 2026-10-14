import { test } from "node:test";
import assert from "node:assert/strict";
import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";
import hello from "./hello.ts";
import reviewScope from "./review-scope.ts";

test("the tool is registered, visible to the model, and runs through the real pipeline", async () => {
	const h = await makeSession({ extensions: [reviewScope] });
	assert.ok(h.session.getActiveToolNames().includes("review_scope"), "registering a direct tool activates it");

	h.faux.setResponses([
		fauxAssistantMessage([fauxToolCall("review_scope", { base: "main" })], { stopReason: "toolUse" }),
		fauxAssistantMessage([fauxText("ok")]),
	]);
	await h.session.prompt("what changed?");

	const result = h.session.messages.find((m) => m.role === "toolResult") as any;
	assert.equal(result.isError, false);
	assert.match(result.content[0].text, /git diff --name-only main/);
	assert.deepEqual(result.details, { base: "main", diffCmd: "git diff --name-only main" });
	h.dispose();
});

test("base is optional: a call with no arguments is valid and defaults to the working tree", async () => {
	const h = await makeSession({ extensions: [reviewScope] });
	h.faux.setResponses([
		fauxAssistantMessage([fauxToolCall("review_scope", {})], { stopReason: "toolUse" }),
		fauxAssistantMessage([fauxText("ok")]),
	]);
	await h.session.prompt("what changed?");
	const result = h.session.messages.find((m) => m.role === "toolResult") as any;
	assert.equal(result.isError, false, "a schema that called base required would have rejected this");
	assert.match(result.content[0].text, /git status --short/);
	h.dispose();
});

test("the command registers and is listed beside the built-ins", async () => {
	const h = await makeSession({ extensions: [hello] });
	const commands = h.session.extensionRunner?.getRegisteredCommands?.() ?? [];
	assert.ok(JSON.stringify(commands).includes("hello"));
	h.dispose();
});
