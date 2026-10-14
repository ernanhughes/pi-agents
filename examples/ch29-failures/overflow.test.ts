import { test } from "node:test";
import assert from "node:assert/strict";
import { fauxAssistantMessage, fauxText } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";
import customSummary from "../ch23-compaction/custom-summary.ts";
import overflow from "./overflow.ts";

const say = (t: string) => fauxAssistantMessage([fauxText(t)]);
const fail = (errorMessage: string) => fauxAssistantMessage([], { stopReason: "error", errorMessage });

// customSummary supplies the compaction summary, so no second model is needed.
async function session(extensions: Parameters<typeof makeSession>[0]["extensions"]) {
	const h = await makeSession({
		extensions: [customSummary, ...extensions],
		settings: { compaction: { enabled: true, keepRecentTokens: 800, reserveTokens: 1000 }, retry: { enabled: false } },
	});
	for (let i = 0; i < 5; i++) {
		h.faux.setResponses([say(`answer ${i}: ${"the schema has a billing table. ".repeat(40)}`)]);
		await h.session.prompt(`question ${i}`);
	}
	const events: string[] = [];
	h.session.subscribe((e: any) => {
		if (/compaction|retry|settled|agent_end/.test(e.type)) events.push(e.type + (e.reason ? `:${e.reason}` : ""));
	});
	return { h, events };
}

test("a provider's own overflow message, normalised, triggers compact-and-retry as a fresh run", async () => {
	const { h, events } = await session([overflow]);
	h.faux.setResponses([fail("model is too long for this context"), say("recovered after compaction")]);
	await h.session.prompt("one more question");

	assert.ok(events.includes("compaction_start:overflow"), "recovery compacted, with reason overflow");
	assert.ok(events.indexOf("compaction_end:overflow") < events.lastIndexOf("agent_end"), "and then ran again");
	const types = h.session.sessionManager.getEntries().map((e: any) => e.type);
	assert.ok(types.includes("context_edit"), "the failed attempt was omitted from context with a context_edit, not deleted");
	assert.ok(types.includes("compaction"));
	assert.match(JSON.stringify(h.session.messages.at(-1)), /recovered after compaction/);
	h.dispose();
});

test("without the handler the same message is just a failure: no recovery is attempted", async () => {
	const { h, events } = await session([]);
	h.faux.setResponses([fail("model is too long for this context"), say("never requested")]);
	await h.session.prompt("one more question");
	assert.ok(!events.some((e) => e.startsWith("compaction_start")), "Pi did not recognise the message as an overflow");
	h.dispose();
});

test("a rate limit that happens to contain the word 'length' is left alone", async () => {
	const { h, events } = await session([overflow]);
	h.faux.setResponses([fail("429 rate limit: request length quota exceeded"), say("never requested")]);
	await h.session.prompt("one more question");
	assert.ok(!events.some((e) => e.startsWith("compaction_start")));
	h.dispose();
});
