import { test } from "node:test";
import assert from "node:assert/strict";
import { createModels, fauxAssistantMessage, fauxProvider, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeResearchAgent } from "../ch37-agent-core/research-agent.ts";
import { drive_oneshot, drive_streaming } from "./drivers.ts";

const corpus = { a1: "The release shipped on 4 October." };

function build() {
	const faux = fauxProvider();
	const models = createModels();
	models.setProvider(faux.provider);
	faux.setResponses([
		fauxAssistantMessage([fauxToolCall("lookup_evidence", { query: "release" })], { stopReason: "toolUse" }),
		fauxAssistantMessage([fauxText("It shipped on 4 October [a1].")]),
	]);
	return { faux, agent: makeResearchAgent(models, faux.getModel(), corpus) };
}

const shape = (agent: { state: { messages: any[] } }) =>
	agent.state.messages.filter((m) => m.role !== "system").map((m) => `${m.role}:${m.isError ?? ""}`);

test("two interfaces over one agent: same transcript, different observers", async () => {
	const a = build();
	const drawn: string[] = [];
	await drive_streaming(a.agent, "Did the release ship?", (c) => drawn.push(c));

	const b = build();
	const once = await drive_oneshot(b.agent, "Did the release ship?");

	// The agent did the same thing under both drivers...
	assert.deepEqual(shape(a.agent), shape(b.agent));
	assert.equal(a.faux.state.callCount, b.faux.state.callCount);
	// ...and the only difference is what each driver observed.
	assert.equal(drawn.join(""), once.text);
	assert.ok(drawn.length > 1, "the streaming driver saw the answer in pieces");
	assert.equal(once.ok, true);
});
