import { test } from "node:test";
import assert from "node:assert/strict";
import { createModels, fauxAssistantMessage, fauxProvider, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { assess } from "./assess.ts";

function setup() {
	const faux = fauxProvider();
	const models = createModels();
	models.setProvider(faux.provider);
	return { faux, models, model: faux.getModel() };
}

test("a valid submission comes back as a typed value", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([
		fauxAssistantMessage(
			[fauxToolCall("submit_assessment", { verdict: "supported", confidence: 0.9, citations: ["a"], reason: "ok" })],
			{ stopReason: "toolUse" },
		),
	]);
	const r = await assess(models, model, "claim", ["a"]);
	assert.equal(r.verdict, "supported");
	assert.equal(faux.state.callCount, 1);
});

test("arguments that break the schema are rejected, not passed on", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([
		fauxAssistantMessage(
			[fauxToolCall("submit_assessment", { verdict: "maybe", confidence: 7, citations: [], reason: "" })],
			{ stopReason: "toolUse" },
		),
	]);
	await assert.rejects(assess(models, model, "claim", []), /./);
});

test("prose instead of a tool call is an error the caller can see", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([fauxAssistantMessage([fauxText("I think it is probably true.")])]);
	await assert.rejects(assess(models, model, "claim", []), /prose instead of calling/);
});

test("a failed request is an exception with the provider's message, not a silent value", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([fauxAssistantMessage([], { stopReason: "error", errorMessage: "429 rate limited" })]);
	await assert.rejects(assess(models, model, "claim", []), /model call failed: 429 rate limited/);
	assert.equal(faux.state.callCount, 1);
});
