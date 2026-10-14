// Chapter 29 - Failures, Retries, and Recovery
// Does a normalised overflow error produce a compact-and-retry, and does it leave a context_edit rather than deleting anything?
// Real sessions with the chapter's message_end handler; the recorded event sequence; the stored-vs-sent entry types; two failure arms.

import { fauxAssistantMessage, fauxText } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";
import customSummary from "../ch23-compaction/custom-summary.ts";
import overflow from "../ch29-failures/overflow.ts";

const say = (t: string) => fauxAssistantMessage([fauxText(t)]);
const fail = (errorMessage: string) => fauxAssistantMessage([], { stopReason: "error", errorMessage });

async function session(extensions: any[]) {
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

async function normalisedOverflow() {
	const { h, events } = await session([overflow]);
	h.faux.setResponses([fail("model is too long for this context"), say("recovered after compaction")]);
	await h.session.prompt("one more question");
	const types = h.session.sessionManager.getEntries().map((e: any) => e.type);
	const lastMessage = JSON.stringify(h.session.messages.at(-1));
	h.dispose();
	return { events, types, lastMessage };
}

async function withoutHandler() {
	const { h, events } = await session([]);
	h.faux.setResponses([fail("model is too long for this context"), say("never requested")]);
	await h.session.prompt("one more question");
	const types = h.session.sessionManager.getEntries().map((e: any) => e.type);
	h.dispose();
	return { events, types };
}

async function rateLimitWithLength() {
	const { h, events } = await session([overflow]);
	h.faux.setResponses([fail("429 rate limit: request length quota exceeded"), say("never requested")]);
	await h.session.prompt("one more question");
	h.dispose();
	return { events };
}

const [normalised, noHandler, rateLimit] = await Promise.all([
	normalisedOverflow(),
	withoutHandler(),
	rateLimitWithLength(),
]);

console.log(JSON.stringify({
	normalisedOverflow: {
		events: normalised.events,
		compactionStartOverflow: normalised.events.includes("compaction_start:overflow"),
		compactionEndBeforeAgentEnd: normalised.events.indexOf("compaction_end:overflow") < normalised.events.lastIndexOf("agent_end"),
		hasContextEdit: normalised.types.includes("context_edit"),
		hasCompaction: normalised.types.includes("compaction"),
		recovered: /recovered after compaction/.test(normalised.lastMessage),
	},
	withoutHandler: {
		events: noHandler.events,
		compactionStarted: noHandler.events.some((e) => e.startsWith("compaction_start")),
	},
	rateLimit: {
		events: rateLimit.events,
		compactionStarted: rateLimit.events.some((e) => e.startsWith("compaction_start")),
	},
}));