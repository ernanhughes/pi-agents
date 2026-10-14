// Chapter 40 - Composing Agent Operations
// What is the exact request cost of each route, and does a check placed *after* the model stop an invented citation before the next call is paid for?
// The chapter's checkClaim across the cheap path, an invented citation, a truthful one, escalation, and the bounds.

import { createModels, fauxAssistantMessage, fauxProvider, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { checkClaim, citationsAreReal, retrieve } from "../ch40-composition/pipeline.ts";

const corpus = { a1: "The release shipped on 4 October.", a2: "The migration finished the same week." };
const assessCall = (v: string, citations: string[]) =>
	fauxAssistantMessage([fauxToolCall("submit_assessment", { verdict: v, confidence: 0.8, citations, reason: "r" })], { stopReason: "toolUse" });
const submit = (args: unknown) => fauxAssistantMessage([fauxToolCall("submit", args as any)], { stopReason: "toolUse" });
const lookup = (q: string) => fauxAssistantMessage([fauxToolCall("lookup_evidence", { query: q })], { stopReason: "toolUse" });

function setup() {
	const faux = fauxProvider();
	const models = createModels();
	models.setProvider(faux.provider);
	return { faux, models, model: faux.getModel() };
}

async function deterministic() {
	return { retrieved: retrieve(corpus, "Did the release ship?"), citationOk: citationsAreReal({ verdict: "supported", confidence: 1, citations: ["invented"], reason: "" }, ["real"]) };
}

async function cheapPath() {
	const { faux, models, model } = setup();
	faux.setResponses([assessCall("supported", ["The release shipped on 4 October."]), submit({ text: "Yes, it shipped." })]);
	const r = await checkClaim(models, model, corpus, "The release shipped");
	return { route: r.route, callCount: faux.state.callCount };
}

async function inventedCitation() {
	const { faux, models, model } = setup();
	faux.setResponses([assessCall("supported", ["a sentence the model made up"])]);
	let error = "";
	try { await checkClaim(models, model, corpus, "The release shipped"); } catch (e: any) { error = String(e.message); }
	return { rejected: error.includes("not provided"), callCount: faux.state.callCount };
}

async function escalationTruthful() {
	const { faux, models, model } = setup();
	faux.setResponses([
		assessCall("insufficient", []),
		lookup("migration"),
		fauxAssistantMessage([fauxText("Found it.")]),
		assessCall("supported", ["The migration finished the same week."]),
		submit({ text: "Supported." }),
	]);
	const r = await checkClaim(models, model, corpus, "The release shipped");
	return { route: r.route, callCount: faux.state.callCount };
}

async function escalationCost() {
	const { faux, models, model } = setup();
	faux.setResponses([
		assessCall("insufficient", []),
		lookup("migration"),
		fauxAssistantMessage([fauxText("Found it.")]),
		assessCall("supported", []),
		submit({ text: "Supported after a second look." }),
	]);
	const r = await checkClaim(models, model, corpus, "The release shipped");
	return { route: r.route, verdict: r.assessment.verdict, callCount: faux.state.callCount };
}

const [d, c, i, et, ec] = await Promise.all([deterministic(), cheapPath(), inventedCitation(), escalationTruthful(), escalationCost()]);

console.log(JSON.stringify({
	deterministic: d,
	cheapPath: c,
	inventedCitation: i,
	escalationTruthful: et,
	escalationCost: ec,
}));