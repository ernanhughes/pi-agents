// Chapter 36 - Model Access Without the Coding Agent
// Can one `models.complete()` become a typed value, and what happens when the arguments break the schema?
// The chapter's `assess` against the faux provider: valid submission, schema-breaking arguments, prose instead of a tool call, a failed request.

import { createModels, fauxAssistantMessage, fauxProvider, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { assess } from "../ch36-model-access/assess.ts";

function setup() {
	const faux = fauxProvider();
	const models = createModels();
	models.setProvider(faux.provider);
	return { faux, models, model: faux.getModel() };
}

async function valid() {
	const { faux, models, model } = setup();
	faux.setResponses([
		fauxAssistantMessage([fauxToolCall("submit_assessment", { verdict: "supported", confidence: 0.9, citations: ["a"], reason: "ok" })], { stopReason: "toolUse" }),
	]);
	const r = await assess(models, model, "claim", ["a"]);
	return { verdict: r.verdict, callCount: faux.state.callCount };
}

async function schemaBreaking() {
	const { faux, models, model } = setup();
	faux.setResponses([fauxAssistantMessage([fauxToolCall("submit_assessment", { verdict: "maybe", confidence: 7, citations: [], reason: "" })], { stopReason: "toolUse" })]);
	let error = "";
	try { await assess(models, model, "claim", []); } catch (e: any) { error = String(e.message); }
	return { rejected: error !== "", error: error.slice(0, 80) };
}

async function prose() {
	const { faux, models, model } = setup();
	faux.setResponses([fauxAssistantMessage([fauxText("I think it is probably true.")])]);
	let error = "";
	try { await assess(models, model, "claim", []); } catch (e: any) { error = String(e.message); }
	return { rejected: error !== "", error: error.slice(0, 80) };
}

async function failedRequest() {
	const { faux, models, model } = setup();
	faux.setResponses([fauxAssistantMessage([], { stopReason: "error", errorMessage: "429 rate limited" })]);
	let error = "";
	try { await assess(models, model, "claim", []); } catch (e: any) { error = String(e.message); }
	return { rejected: error !== "", hasProviderMessage: /429 rate limited/.test(error), callCount: faux.state.callCount };
}

const [v, s, p, f] = await Promise.all([valid(), schemaBreaking(), prose(), failedRequest()]);

console.log(JSON.stringify({
	valid: { verdict: v.verdict, callCount: v.callCount },
	schemaBreaking: s,
	prose: p,
	failedRequest: f,
}));