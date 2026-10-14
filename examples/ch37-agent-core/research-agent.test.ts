import { test } from "node:test";
import assert from "node:assert/strict";
import { createModels, fauxAssistantMessage, fauxProvider, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeResearchAgent } from "./research-agent.ts";

const corpus = { a1: "The release shipped on 4 October.", a2: "Nothing else is recorded." };

function setup() {
	const faux = fauxProvider();
	const models = createModels();
	models.setProvider(faux.provider);
	return { faux, models, model: faux.getModel() };
}

test("the loop runs tool then answer, and the transcript records both", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([
		fauxAssistantMessage([fauxToolCall("lookup_evidence", { query: "release" })], { stopReason: "toolUse" }),
		fauxAssistantMessage([fauxText("It shipped on 4 October [a1].")]),
	]);

	const agent = makeResearchAgent(models, model, corpus);
	const seen: string[] = [];
	agent.subscribe((e) => {
		seen.push(e.type);
	});
	await agent.prompt("Did the release ship?");

	const roles = agent.state.messages.map((m) => m.role).filter((r) => r !== "system");
	assert.deepEqual(roles, ["user", "assistant", "toolResult", "assistant"]);
	assert.equal(faux.state.callCount, 2); // one request per turn
	assert.ok(seen.indexOf("tool_execution_end") > seen.indexOf("tool_execution_start"));
	assert.equal(seen.at(-1), "agent_end");
});

test("a tool that finds nothing returns data, not a failure", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([
		fauxAssistantMessage([fauxToolCall("lookup_evidence", { query: "zzz" })], { stopReason: "toolUse" }),
		fauxAssistantMessage([fauxText("No evidence.")]),
	]);
	const agent = makeResearchAgent(models, model, corpus);
	await agent.prompt("anything about zzz?");
	const result = agent.state.messages.find((m) => m.role === "toolResult") as any;
	assert.equal(result.isError, false);
	assert.deepEqual(result.content, [{ type: "text", text: "no matches" }]);
});
