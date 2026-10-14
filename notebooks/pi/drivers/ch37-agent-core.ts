// Chapter 37 - The Agent Core on Its Own
// Does one prompt produce a four-message transcript and exactly two provider requests - and is a lookup miss data or a failure?
// The chapter's research agent against the faux provider: role sequence, request count, event order; a miss returning `no matches`.

import { createModels, fauxAssistantMessage, fauxProvider, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeResearchAgent } from "../ch37-agent-core/research-agent.ts";

const corpus = { a1: "The release shipped on 4 October.", a2: "Nothing else is recorded." };

function setup() {
	const faux = fauxProvider();
	const models = createModels();
	models.setProvider(faux.provider);
	return { faux, models, model: faux.getModel() };
}

async function loop() {
	const { faux, models, model } = setup();
	faux.setResponses([
		fauxAssistantMessage([fauxToolCall("lookup_evidence", { query: "release" })], { stopReason: "toolUse" }),
		fauxAssistantMessage([fauxText("It shipped on 4 October [a1].")]),
	]);
	const agent = makeResearchAgent(models, model, corpus);
	const seen: string[] = [];
	agent.subscribe((e: any) => void seen.push(e.type));
	await agent.prompt("Did the release ship?");
	const roles = agent.state.messages.map((m: any) => m.role).filter((r: string) => r !== "system");
	const toolOrder = seen.indexOf("tool_execution_end") > seen.indexOf("tool_execution_start");
	return { roles, callCount: faux.state.callCount, toolOrder, lastEvent: seen.at(-1) };
}

async function miss() {
	const { faux, models, model } = setup();
	faux.setResponses([
		fauxAssistantMessage([fauxToolCall("lookup_evidence", { query: "zzz" })], { stopReason: "toolUse" }),
		fauxAssistantMessage([fauxText("No evidence.")]),
	]);
	const agent = makeResearchAgent(models, model, corpus);
	await agent.prompt("anything about zzz?");
	const result = agent.state.messages.find((m: any) => m.role === "toolResult") as any;
	return { isError: result.isError, content: JSON.stringify(result.content) };
}

const [loopResult, missResult] = await Promise.all([loop(), miss()]);

console.log(JSON.stringify({
	loop: loopResult,
	miss: missResult,
}));