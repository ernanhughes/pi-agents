// Behavioural claims from chapter 34, run against a real AgentSession.
import { test } from "node:test";
import assert from "node:assert/strict";
import { fauxAssistantMessage, fauxText } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";

const say = (t: string) => fauxAssistantMessage([fauxText(t)]);

test("streaming: subscribe before prompting, and text arrives as typed deltas", async () => {
	const h = await makeSession({ extensions: [] });
	h.faux.setResponses([say("the repository has three packages")]);

	const deltas: string[] = [];
	const unsubscribe = h.session.subscribe((event) => {
		if (event.type === "message_update" && event.assistantMessageEvent.type === "text_delta") {
			deltas.push(event.assistantMessageEvent.delta);
		}
	});
	try {
		await h.session.prompt("Explain this repository");
	} finally {
		unsubscribe();
	}
	assert.equal(deltas.join(""), "the repository has three packages");
	assert.ok(deltas.length > 1, "more than one delta");
	assert.equal(h.session.getLastAssistantText(), "the repository has three packages");
	h.dispose();
});

test("a prompt sent while the session is streaming must say steer or follow-up, or it rejects", async () => {
	const h = await makeSession({ extensions: [], fauxOptions: { tokensPerSecond: 20 } });
	h.faux.setResponses([say("a fairly long answer that takes a little while to stream out"), say("second"), say("third")]);

	const running = h.session.prompt("first");
	await new Promise((r) => setTimeout(r, 30));
	assert.equal(h.session.isStreaming, true);

	await assert.rejects(h.session.prompt("second, no behaviour given"), /./, "no streamingBehavior: rejected rather than guessed");

	const steered = await h.session.steer("change direction");
	const followed = await h.session.followUp("then also this");
	assert.equal(steered, "queued");
	assert.equal(followed, "queued");
	await running;
	await h.session.waitForIdle();
	h.dispose();
});

test("SessionManager is authoritative: assigning agent.state.messages does not change what is sent", async () => {
	const h = await makeSession({ extensions: [] });
	h.faux.setResponses([say("one")]);
	await h.session.prompt("first question");

	// Overwrite the in-memory transcript with something else entirely.
	h.session.agent.state.messages = [{ role: "user", content: "FORGED HISTORY", timestamp: Date.now() }];

	let sent = "";
	h.faux.setResponses([(ctx) => ((sent = JSON.stringify(ctx.messages)), say("two"))]);
	await h.session.prompt("second question");
	assert.doesNotMatch(sent, /FORGED HISTORY/, "the forged transcript never reached the provider");
	assert.match(sent, /first question/, "the real history, from the session manager, did");
	h.dispose();
});

test("an in-memory SessionManager writes no file", async () => {
	const h = await makeSession({ extensions: [] });
	assert.equal(h.session.sessionManager.getSessionFile(), undefined);
	h.dispose();
});

test("dispose() stops event delivery", async () => {
	const h = await makeSession({ extensions: [] });
	let events = 0;
	h.session.subscribe(() => void events++);
	h.dispose();
	const before = events;
	h.faux.setResponses([say("x")]);
	await h.session.prompt("after dispose").catch(() => {});
	assert.equal(events, before, "a disposed session delivers nothing to listeners");
});
