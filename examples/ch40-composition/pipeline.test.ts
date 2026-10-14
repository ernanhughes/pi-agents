import { test } from "node:test";
import assert from "node:assert/strict";
import { createModels, fauxAssistantMessage, fauxProvider, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { checkClaim, citationsAreReal, retrieve, ESCALATION_TURNS } from "./pipeline.ts";

const corpus = { a1: "The release shipped on 4 October.", a2: "The migration finished the same week." };

const assessCall = (v: string, citations: string[]) =>
	fauxAssistantMessage([fauxToolCall("submit_assessment", { verdict: v, confidence: 0.8, citations, reason: "r" })], { stopReason: "toolUse" });
const submit = (args: unknown) => fauxAssistantMessage([fauxToolCall("submit", args as any)], { stopReason: "toolUse" });

function setup() {
	const faux = fauxProvider();
	const models = createModels();
	models.setProvider(faux.provider);
	return { faux, models, model: faux.getModel() };
}

test("the deterministic parts need no model at all", () => {
	assert.deepEqual(retrieve(corpus, "Did the release ship?"), ["The release shipped on 4 October."]);
	assert.equal(citationsAreReal({ verdict: "supported", confidence: 1, citations: ["invented"], reason: "" }, ["real"]), false);
});

test("cheap path: one assessment call and one summary step, no agent", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([assessCall("supported", ["The release shipped on 4 October."]), submit({ text: "Yes, it shipped." })]);
	const r = await checkClaim(models, model, corpus, "The release shipped");
	assert.equal(r.route, "single call");
	assert.equal(faux.state.callCount, 2);
});

test("an invented citation stops the pipeline before anything downstream runs", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([assessCall("supported", ["a sentence the model made up"])]);
	await assert.rejects(checkClaim(models, model, corpus, "The release shipped"), /not provided/);
	assert.equal(faux.state.callCount, 1);
});

test("an invented citation on the escalation path is caught too", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([
		assessCall("insufficient", []),
		fauxAssistantMessage([fauxToolCall("lookup_evidence", { query: "migration" })], { stopReason: "toolUse" }),
		fauxAssistantMessage([fauxText("Found it.")]),
		assessCall("supported", ["a quotation that exists in no evidence at all"]),
		submit({ text: "never reached" }),
	]);
	await assert.rejects(checkClaim(models, model, corpus, "The release shipped"), /not provided/);
	assert.equal(faux.state.callCount, 4); // the summary step never ran
});

test("a truthful citation of evidence the agent found passes the second check", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([
		assessCall("insufficient", []),
		fauxAssistantMessage([fauxToolCall("lookup_evidence", { query: "migration" })], { stopReason: "toolUse" }),
		fauxAssistantMessage([fauxText("Found it.")]),
		assessCall("supported", ["The migration finished the same week."]),
		submit({ text: "Supported." }),
	]);
	const r = await checkClaim(models, model, corpus, "The release shipped");
	assert.equal(r.route, "agent escalation");
	assert.deepEqual(r.assessment.citations, ["The migration finished the same week."]);
});

test("escalation: only an insufficient verdict pays for the agent", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([
		assessCall("insufficient", []),
		// the agent: look something up, then answer
		fauxAssistantMessage([fauxToolCall("lookup_evidence", { query: "migration" })], { stopReason: "toolUse" }),
		fauxAssistantMessage([fauxText("Found it.")]),
		assessCall("supported", []),
		submit({ text: "Supported after a second look." }),
	]);
	const r = await checkClaim(models, model, corpus, "The release shipped");
	assert.equal(r.route, "agent escalation");
	assert.equal(r.assessment.verdict, "supported");
	assert.equal(faux.state.callCount, 5);
});

test("the escalation agent is bounded, so a model that keeps searching cannot run away", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([
		assessCall("insufficient", []),
		// A research agent that never stops looking up. Nothing else in the
		// pipeline is unbounded, and this used to be the one hole in it.
		...Array.from({ length: ESCALATION_TURNS }, () => fauxAssistantMessage([fauxToolCall("lookup_evidence", { query: "migration" })], { stopReason: "toolUse" })),
		assessCall("supported", ["The migration finished the same week."]),
		submit({ text: "Supported." }),
	]);
	const r = await checkClaim(models, model, corpus, "The release shipped");
	assert.equal(r.route, "agent escalation");
	// 1 assess + ESCALATION_TURNS agent turns + 1 assess + 1 summary submit
	assert.equal(faux.state.callCount, ESCALATION_TURNS + 3);
	assert.ok(faux.state.callCount < 10, "the agent was cut off rather than allowed to keep spending requests");
});

test("an escalation cut off before it found anything fails loudly instead of re-deciding on no new evidence", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([
		assessCall("insufficient", []),
		// Search for something the corpus does not contain, on every turn.
		...Array.from({ length: ESCALATION_TURNS }, () => fauxAssistantMessage([fauxToolCall("lookup_evidence", { query: "absent" })], { stopReason: "toolUse" })),
	]);
	await assert.rejects(checkClaim(models, model, corpus, "The release shipped"), /cut off before it found anything/);
});
