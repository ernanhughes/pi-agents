import { Agent, type AgentTool } from "@earendil-works/pi-agent-core";
import { Type, createModels, fauxAssistantMessage, fauxProvider, fauxText, fauxToolCall } from "@earendil-works/pi-ai";

const Params = Type.Object({ text: Type.String() });
const wordCount: AgentTool<typeof Params> = {
	name: "word_count", label: "Word Count", description: "Count the words in a string.",
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
		if (e.type === "message_end") { row.role = e.message.role; row.stopReason = e.message.stopReason; }
		if (e.type === "tool_execution_start") row.tool = e.toolName;
		if (e.type === "tool_execution_end") { row.tool = e.toolName; row.details = e.result.details; }
		events.push(row);
	});
	await agent.prompt(userText);
	return {
		requests: faux.state.callCount,
		stopReasons: events.filter((e) => e.type === "message_end" && e.role === "assistant").map((e) => e.stopReason),
		toolRuns: events.filter((e) => e.type === "tool_execution_end").map((e) => e.details),
		firstEvent: events[0]?.type,
		lastEvent: events[events.length - 1]?.type,
		hasSettled: events.some((e) => e.type === "agent_settled"),
	};
}

const ask = (t: string) => fauxAssistantMessage([fauxToolCall("word_count", { text: t })], { stopReason: "toolUse" });
const say = (t: string) => fauxAssistantMessage([fauxText(t)]);

console.log(
	JSON.stringify(
		{
			oneToolThenAnswer: await run([ask("the quick brown fox"), say("Four words.")], "How many words?"),
			keepsAsking: await run([ask("one"), ask("two"), say("Done.")], "count repeatedly"),
			providerError: await run([fauxAssistantMessage([], { stopReason: "error", errorMessage: "429 rate limited" })], "go"),
		},
		null,
		2,
	),
);