// Chapter 38 - A Stochastic Step Is a Typed Function
// Does `maxTurns` still bound a run after a valid submission was stored in a mixed batch?
// The chapter's step() against the faux provider: valid submit, repair, attempt exhaustion, a never-submitting model, a mixed batch.

import { Type, createModels, fauxAssistantMessage, fauxProvider, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { step, StepFailed } from "../ch38-typed-step/step.ts";
import { lookupEvidence } from "../ch37-agent-core/research-agent.ts";

const Triage = Type.Object({ severity: Type.Union([Type.Literal("low"), Type.Literal("high")]), reason: Type.String() });
const submitCall = (args: unknown) => fauxAssistantMessage([fauxToolCall("submit", args as any)], { stopReason: "toolUse" });

function setup() {
	const faux = fauxProvider();
	const models = createModels();
	models.setProvider(faux.provider);
	return { faux, models, model: faux.getModel() };
}

async function valid() {
	const { faux, models, model } = setup();
	faux.setResponses([submitCall({ severity: "high", reason: "data loss" })]);
	const out = await step(models, model, "Triage.", "Backup deleted a table.", Triage);
	return { out, callCount: faux.state.callCount };
}

async function repair() {
	const { faux, models, model } = setup();
	faux.setResponses([submitCall({ severity: "catastrophic", reason: "x" }), submitCall({ severity: "high", reason: "x" })]);
	const out = await step(models, model, "Triage.", "input", Triage);
	return { severity: out.severity, callCount: faux.state.callCount };
}

async function attemptExhaustion() {
	const { faux, models, model } = setup();
	faux.setResponses([submitCall({ bad: 1 }), submitCall({ bad: 2 }), submitCall({ bad: 3 }), submitCall({ bad: 4 })]);
	let kind = "";
	try { await step(models, model, "Triage.", "input", Triage, { maxAttempts: 2 }); }
	catch (e: any) { kind = e.kind; }
	return { kind, callCount: faux.state.callCount };
}

async function neverSubmits() {
	const { faux, models, model } = setup();
	const corpus = { a1: "The release shipped on 4 October." };
	const lookup = () => fauxAssistantMessage([fauxToolCall("lookup_evidence", { query: "release" })], { stopReason: "toolUse" });
	faux.setResponses(Array.from({ length: 30 }, lookup));
	let kind = "";
	try { await step(models, model, "Triage.", "x", Triage, { extraTools: [lookupEvidence(corpus)], maxTurns: 4 }); }
	catch (e: any) { kind = e.kind; }
	return { kind, callCount: faux.state.callCount };
}

async function mixedBatchBound() {
	const { faux, models, model } = setup();
	const corpus = { a1: "The release shipped on 4 October." };
	const mixed = () =>
		fauxAssistantMessage([fauxToolCall("submit", { severity: "high", reason: "mixed batch" }), fauxToolCall("lookup_evidence", { query: "release" })], { stopReason: "toolUse" });
	faux.setResponses(Array.from({ length: 30 }, mixed));
	const out = await step(models, model, "Triage.", "x", Triage, { extraTools: [lookupEvidence(corpus)], maxTurns: 2 });
	return { out, callCount: faux.state.callCount };
}

async function firstValidWins() {
	const { faux, models, model } = setup();
	const corpus = { a1: "x" };
	faux.setResponses([
		fauxAssistantMessage([fauxToolCall("submit", { severity: "low", reason: "first" }), fauxToolCall("lookup_evidence", { query: "q" })], { stopReason: "toolUse" }),
		submitCall({ severity: "high", reason: "second" }),
	]);
	const out = await step(models, model, "Triage.", "x", Triage, { extraTools: [lookupEvidence(corpus)] });
	return { out };
}

async function invalidInMixedBatch() {
	const { faux, models, model } = setup();
	const corpus = { a1: "x" };
	const bad = (n: number) => fauxAssistantMessage([fauxToolCall("submit", { bad: n }), fauxToolCall("lookup_evidence", { query: "q" })], { stopReason: "toolUse" });
	faux.setResponses([bad(1), bad(2), submitCall({ severity: "high", reason: "repaired" })]);
	const out = await step(models, model, "Triage.", "x", Triage, { extraTools: [lookupEvidence(corpus)], maxAttempts: 3 });
	return { severity: out.severity, callCount: faux.state.callCount };
}

const [v, r, a, n, m, fv, ib] = await Promise.all([
	valid(), repair(), attemptExhaustion(), neverSubmits(), mixedBatchBound(), firstValidWins(), invalidInMixedBatch(),
]);

console.log(JSON.stringify({
	valid: v,
	repair: r,
	attemptExhaustion: a,
	neverSubmits: n,
	mixedBatchBound: m,
	firstValidWins: fv,
	invalidInMixedBatch: ib,
}));