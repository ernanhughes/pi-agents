import { test } from "node:test";
import assert from "node:assert/strict";
import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession } from "./session.ts";

test("harness: a real session runs a scripted turn and an inline extension sees the tool call", async () => {
	const seen: string[] = [];
	const h = await makeSession({
		extensions: [
			(pi) => {
				pi.on("tool_call", async (event) => {
					seen.push(event.toolName);
					return { block: true, reason: "probe" };
				});
			},
		],
	});
	h.faux.setResponses([
		fauxAssistantMessage([fauxToolCall("bash", { command: "echo hi" })], { stopReason: "toolUse" }),
		fauxAssistantMessage([fauxText("done")]),
	]);
	await h.session.prompt("go");
	assert.deepEqual(seen, ["bash"]);
	h.dispose();
});
