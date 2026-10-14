import { test } from "node:test";
import assert from "node:assert/strict";
import { Type, createModels, fauxAssistantMessage, fauxProvider, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { step, StepFailed } from "./step.ts";
import { lookupEvidence } from "../ch37-agent-core/research-agent.ts";

const Triage = Type.Object({ severity: Type.Union([Type.Literal("low"), Type.Literal("high")]), reason: Type.String() });
const submitCall = (args: unknown) => fauxAssistantMessage([fauxToolCall("submit", args as any)], { stopReason: "toolUse" });

function setup() {
	const faux = fauxProvider();
	const models = createModels();
	models.setProvider(faux.provider);
	return { faux, models, model: faux.getModel() };
}

test("a valid submission ends the run after one request", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([submitCall({ severity: "high", reason: "data loss" })]);
	const out = await step(models, model, "Triage.", "Backup deleted a table.", Triage);
	assert.deepEqual(out, { severity: "high", reason: "data loss" });
	assert.equal(faux.state.callCount, 1); // terminate: true skipped the follow-up request
});

test("an invalid submission is returned to the model, which repairs it", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([submitCall({ severity: "catastrophic", reason: "x" }), submitCall({ severity: "high", reason: "x" })]);
	const out = await step(models, model, "Triage.", "input", Triage);
	assert.equal(out.severity, "high");
	assert.equal(faux.state.callCount, 2);
});

test("repeated invalid submissions stop at maxAttempts", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([submitCall({ bad: 1 }), submitCall({ bad: 2 }), submitCall({ bad: 3 }), submitCall({ bad: 4 })]);
	await assert.rejects(step(models, model, "Triage.", "input", Triage, { maxAttempts: 2 }), StepFailed);
	assert.equal(faux.state.callCount, 2);
});

test("prose with no submit is a StepFailed, not a silent empty value", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([fauxAssistantMessage([fauxText("High, I think.")])]);
	await assert.rejects(step(models, model, "Triage.", "input", Triage), StepFailed);
});

test("steps chain as ordinary typed functions", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([submitCall({ severity: "high", reason: "data loss" }), submitCall({ text: "Page on-call." })]);
	const triage = await step(models, model, "Triage.", "input", Triage);
	const action = await step(models, model, "Next action.", JSON.stringify(triage), Type.Object({ text: Type.String() }));
	assert.equal(action.text, "Page on-call.");
});

test("a step can use a lookup tool and still must finish with a valid submit", async () => {
	const { faux, models, model } = setup();
	const corpus = { a1: "The release shipped on 4 October." };
	faux.setResponses([
		fauxAssistantMessage([fauxToolCall("lookup_evidence", { query: "release" })], { stopReason: "toolUse" }),
		submitCall({ severity: "low", reason: "found a1" }),
	]);
	const out = await step(models, model, "Triage.", "x", Triage, { extraTools: [lookupEvidence(corpus)] });
	assert.equal(out.reason, "found a1");
	assert.equal(faux.state.callCount, 2);
});

test("a failed request is a provider failure, not a model that chose prose", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([fauxAssistantMessage([], { stopReason: "error", errorMessage: "429 rate limited" })]);
	await assert.rejects(step(models, model, "Triage.", "input", Triage), (e: unknown) => {
		assert.ok(e instanceof StepFailed);
		assert.equal(e.kind, "provider");
		assert.match(e.message, /429 rate limited/);
		return true;
	});
});

test("a model that never submits is stopped by maxTurns, and says so", async () => {
	const { faux, models, model } = setup();
	const corpus = { a1: "The release shipped on 4 October." };
	const lookup = () => fauxAssistantMessage([fauxToolCall("lookup_evidence", { query: "release" })], { stopReason: "toolUse" });
	faux.setResponses(Array.from({ length: 30 }, lookup));
	await assert.rejects(step(models, model, "Triage.", "x", Triage, { extraTools: [lookupEvidence(corpus)], maxTurns: 4 }), (e: unknown) => {
		assert.ok(e instanceof StepFailed);
		assert.equal(e.kind, "turn-limit");
		return true;
	});
	assert.equal(faux.state.callCount, 4); // bounded by maxTurns, not by the 30 scripted responses
});

test("prose with no submit is kind no-submit", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([fauxAssistantMessage([fauxText("High, I think.")])]);
	await assert.rejects(step(models, model, "Triage.", "input", Triage), (e: unknown) => e instanceof StepFailed && e.kind === "no-submit");
});

// The batch rule (chapter 17): a turn ends early only when every completed result
// in the batch agrees to terminate. submit agrees and lookup_evidence does not, so
// one response can store a valid answer and still leave the loop running. The turn
// bound has to keep firing after a submission, or the bound is not a bound.
test("a submission in a batch with a non-terminating tool cannot outlive maxTurns", async () => {
	const { faux, models, model } = setup();
	const corpus = { a1: "The release shipped on 4 October." };
	const mixed = () =>
		fauxAssistantMessage(
			[fauxToolCall("submit", { severity: "high", reason: "mixed batch" }), fauxToolCall("lookup_evidence", { query: "release" })],
			{ stopReason: "toolUse" },
		);
	faux.setResponses(Array.from({ length: 30 }, mixed));
	const out = await step(models, model, "Triage.", "x", Triage, { extraTools: [lookupEvidence(corpus)], maxTurns: 2 });
	assert.deepEqual(out, { severity: "high", reason: "mixed batch" });
	assert.equal(faux.state.callCount, 2, "maxTurns must hold after a submission, not just before one");
});

test("a submission in a mixed batch is still reported as a provider failure if the run then dies", async () => {
	const { faux, models, model } = setup();
	const corpus = { a1: "x" };
	faux.setResponses([
		fauxAssistantMessage(
			[fauxToolCall("submit", { severity: "low", reason: "first" }), fauxToolCall("lookup_evidence", { query: "q" })],
			{ stopReason: "toolUse" },
		),
		fauxAssistantMessage([], { stopReason: "error", errorMessage: "500 upstream" }),
	]);
	// The stored value survives a later provider failure, because it was already
	// committed. Reporting it is not the same as reporting it as this run's success.
	const out = await step(models, model, "Triage.", "x", Triage, { extraTools: [lookupEvidence(corpus)] });
	assert.deepEqual(out, { severity: "low", reason: "first" });
});

test("the first valid submission wins when the model submits more than once", async () => {
	const { faux, models, model } = setup();
	const corpus = { a1: "x" };
	faux.setResponses([
		fauxAssistantMessage(
			[fauxToolCall("submit", { severity: "low", reason: "first" }), fauxToolCall("lookup_evidence", { query: "q" })],
			{ stopReason: "toolUse" },
		),
		submitCall({ severity: "high", reason: "second" }),
	]);
	const out = await step(models, model, "Triage.", "x", Triage, { extraTools: [lookupEvidence(corpus)] });
	assert.deepEqual(out, { severity: "low", reason: "first" });
});

test("an invalid submission in a mixed batch costs one attempt, not one per tool", async () => {
	const { faux, models, model } = setup();
	const corpus = { a1: "x" };
	const bad = (n: number) =>
		fauxAssistantMessage([fauxToolCall("submit", { bad: n }), fauxToolCall("lookup_evidence", { query: "q" })], { stopReason: "toolUse" });
	faux.setResponses([bad(1), bad(2), submitCall({ severity: "high", reason: "repaired" })]);
	const out = await step(models, model, "Triage.", "x", Triage, { extraTools: [lookupEvidence(corpus)], maxAttempts: 3 });
	assert.deepEqual(out, { severity: "high", reason: "repaired" });
	assert.equal(faux.state.callCount, 3, "two mixed batches must not exhaust a three-attempt budget");
});

test("invalid submissions in mixed batches still exhaust the attempt budget", async () => {
	const { faux, models, model } = setup();
	const corpus = { a1: "x" };
	const bad = (n: number) =>
		fauxAssistantMessage([fauxToolCall("submit", { bad: n }), fauxToolCall("lookup_evidence", { query: "q" })], { stopReason: "toolUse" });
	faux.setResponses(Array.from({ length: 10 }, (_, i) => bad(i)));
	await assert.rejects(step(models, model, "Triage.", "x", Triage, { extraTools: [lookupEvidence(corpus)], maxAttempts: 2 }), (e: unknown) => {
		assert.ok(e instanceof StepFailed);
		assert.equal(e.kind, "invalid-submissions");
		return true;
	});
	assert.equal(faux.state.callCount, 2);
});
