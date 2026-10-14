import { Agent, type AgentTool } from "@earendil-works/pi-agent-core";
import {
	Type,
	createModels,
	fauxAssistantMessage,
	fauxProvider,
	fauxText,
	fauxToolCall,
} from "@earendil-works/pi-ai";

// The provider layer: a scripted stand-in for a model.
const faux = fauxProvider();
const models = createModels();
models.setProvider(faux.provider);

// A tool is a name, a schema and an execute(). Nothing here knows about Pi.
const WordCountParams = Type.Object({ text: Type.String() });

const wordCount: AgentTool<typeof WordCountParams> = {
	name: "word_count",
	label: "Word Count",
	description: "Count the words in a string.",
	parameters: WordCountParams,
	async execute(_id, params) {
		const n = params.text.trim().split(/\s+/).filter(Boolean).length;
		return { content: [{ type: "text", text: String(n) }], details: { words: n } };
	},
};

// Turn 1 asks for the tool. Turn 2 answers from its result.
faux.setResponses([
	fauxAssistantMessage([fauxToolCall("word_count", { text: "the quick brown fox" })], { stopReason: "toolUse" }),
	fauxAssistantMessage([fauxText("Four words.")]),
]);

// The agent core: loop, messages, state, tool execution, events.
const agent = new Agent({
	initialState: { systemPrompt: "You count words.", model: faux.getModel(), tools: [wordCount] },
	streamFn: models.streamSimple.bind(models),
});

agent.subscribe((e) => {
	if (e.type === "tool_execution_end") console.log("tool:", e.toolName, JSON.stringify(e.result.details));
	if (e.type === "message_end" && e.message.role === "assistant") console.log("stop:", e.message.stopReason);
});

await agent.prompt("How many words in 'the quick brown fox'?");
