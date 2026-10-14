// Chapter 1 - the loop with no binary, no terminal and no credential.
//
// The same agent core the chapter builds: one tool, a scripted provider, and a
// subscriber that records the ordered event stream plus each assistant message's
// stopReason. The only substitution is the model.

import { Agent, type AgentTool } from "@earendil-works/pi-agent-core";
import { Type, createModels, fauxAssistantMessage, fauxProvider, fauxText, fauxToolCall } from "@earendil-works/pi-ai";

const Params = Type.Object({ text: Type.String() });
const wordCount: AgentTool<typeof Params> = {
	name: "word_count",
	label: "Word Count",
	description: "Count the words in a string.",
	parameters: Params,
	async execute(_id, p) {
		const n = p.text.trim().split(/\s+/).filter(Boolean).length;
		return { content: [{ type: "text", text: String(n) }], details: { words: n } };
	},
};

async function run(script: any[], userText: string) {
	const faux = fauxProvider();
	const models = createModels();
	models.setProvider(faux.provider);
	faux.setResponses(script);

	const events: any[] = [];
	const agent = new Agent({
		initialState: { systemPrompt: "You count words.", model: faux.getModel(), tools: [wordCount] },
		streamFn: models.streamSimple.bind(models),
	});
	agent.subscribe((e: any) => {
		const row: any = { type: e.type };
		if (e.type === "message_end") {
			row.role = e.message.role;
			row.stopReason = e.message.stopReason;
		}
		if (e.type === "tool_execution_start") row.tool = e.toolName;
		if (e.type === "tool_execution_end") {
			row.tool = e.toolName;
			row.details = e.result.details;
		}
		events.push(row);
	});
	await agent.prompt(userText);

	return {
		requests: faux.state.callCount,
		stopReasons: events.filter((e) => e.type === "message_end" && e.role === "assistant").map((e) => e.stopReason),
		toolRuns: events.filter((e) => e.type === "tool_execution_end").map((e) => e.details),
		stream: events.map((e) => (e.tool ? `${e.type}:${e.tool}` : e.stopReason ? `${e.type}:${e.stopReason}` : e.type)),
	};
}

const ask = (t: string) => fauxAssistantMessage([fauxToolCall("word_count", { text: t })], { stopReason: "toolUse" });
const say = (t: string) => fauxAssistantMessage([fauxText(t)]);

// NB_TEXTS lets the notebook's exercise change what the tool counts, without
// editing this file.
const TEXTS: string[] = process.env.NB_TEXTS ? JSON.parse(process.env.NB_TEXTS) : ["one", "two"];

console.log(
	JSON.stringify({
		oneToolThenAnswer: await run([ask("the quick brown fox"), say("Four words.")], "How many words?"),
		keepsAsking: await run([...TEXTS.map((t) => ask(t)), say("Done.")], "count repeatedly"),
		providerError: await run([fauxAssistantMessage([], { stopReason: "error", errorMessage: "429 rate limited" })], "go"),
	}),
);