// Chapter 39 - Seams, Hooks, and Irreversible Decisions
// In what order do the hooks fire, and does a block mean the body never ran, while a rewrite cannot undo the effect?
// The chapter's own order/block/rewrite/transformContext cases against a real Agent.

import { Agent, type AgentMessage, type AgentTool } from "@earendil-works/pi-agent-core";
import { Type, createModels, fauxAssistantMessage, fauxProvider, fauxText, fauxToolCall } from "@earendil-works/pi-ai";

function setup() {
	const faux = fauxProvider();
	const models = createModels();
	models.setProvider(faux.provider);
	return { faux, models, model: faux.getModel() };
}

const WriteParams = Type.Object({ path: Type.String() });

function effectTool(counter: { runs: number }): AgentTool<typeof WriteParams> {
	return {
		name: "write_file",
		label: "write_file",
		description: "pretend to write a file",
		parameters: WriteParams,
		async execute(_id, params) {
			counter.runs++;
			return { content: [{ type: "text", text: `wrote ${params?.path}` }], details: { path: params?.path } };
		},
	};
}

const callTool = (path: string) => fauxAssistantMessage([fauxToolCall("write_file", { path })], { stopReason: "toolUse" });
const say = (t: string) => fauxAssistantMessage([fauxText(t)]);

async function order() {
	const { faux, models, model } = setup();
	const counter = { runs: 0 };
	const orderNames: string[] = [];
	faux.setResponses([callTool("a.txt"), say("done")]);
	const agent = new Agent({
		initialState: { systemPrompt: "x", model, tools: [effectTool(counter)] },
		streamFn: models.streamSimple.bind(models),
		transformContext: async (m) => (orderNames.push("transformContext"), m),
		convertToLlm: (m) => (orderNames.push("convertToLlm"), m.filter((x) => ["user", "assistant", "toolResult", "system"].includes(x.role)) as any),
		prepareRequest: () => void orderNames.push("prepareRequest"),
		beforeToolCall: async () => (orderNames.push("beforeToolCall"), undefined),
		afterToolCall: async () => (orderNames.push("afterToolCall"), undefined),
		finishTurn: () => void orderNames.push("finishTurn"),
	});
	agent.subscribe((e) => {
		if (e.type === "tool_execution_start") orderNames.push("tool.execute starts");
		if (e.type === "turn_end") orderNames.push("turn_end");
	});
	await agent.prompt("go");
	return { orderNames, calls: faux.state.callCount };
}

async function block() {
	const { faux, models, model } = setup();
	const counter = { runs: 0 };
	faux.setResponses([callTool(".env"), say("ok")]);
	const agent = new Agent({
		initialState: { systemPrompt: "x", model, tools: [effectTool(counter)] },
		streamFn: models.streamSimple.bind(models),
		beforeToolCall: async ({ args }: any) => (args.path === ".env" ? { block: true, reason: "protected path" } : undefined),
	});
	await agent.prompt("go");
	const r = agent.state.messages.find((m) => m.role === "toolResult") as any;
	return { runs: counter.runs, isError: r.isError, text: r.content?.[0]?.text ?? "" };
}

async function rewrite() {
	const { faux, models, model } = setup();
	const counter = { runs: 0 };
	faux.setResponses([callTool("a.txt"), say("ok")]);
	const agent = new Agent({
		initialState: { systemPrompt: "x", model, tools: [effectTool(counter)] },
		streamFn: models.streamSimple.bind(models),
		afterToolCall: async () => ({ content: [{ type: "text", text: "[redacted]" }], isError: true }),
	});
	await agent.prompt("go");
	const r = agent.state.messages.find((m) => m.role === "toolResult") as any;
	return { runs: counter.runs, text: r.content?.[0]?.text ?? "", isError: r.isError };
}

async function transformContext() {
	const { faux, models, model } = setup();
	let received: unknown[] = [];
	faux.setResponses([(ctx: any) => ((received = ctx.messages.map((m: any) => m.role)), say("ok"))]);
	const agent = new Agent({
		initialState: { systemPrompt: "x", model },
		streamFn: models.streamSimple.bind(models),
		transformContext: async (messages: AgentMessage[]) => messages.filter((m) => !(m.role === "user" && String(m.content).startsWith("NOISE"))),
	});
	await agent.prompt([
		{ role: "user", content: "NOISE: old chatter", timestamp: Date.now() },
		{ role: "user", content: "the real question", timestamp: Date.now() },
	]);
	const sentUsers = received.filter((r) => r === "user").length;
	const storedUsers = agent.state.messages.filter((m) => m.role === "user").length;
	return { sentUsers, storedUsers };
}

async function finishTurnEarly() {
	const { faux, models, model } = setup();
	const counter = { runs: 0 };
	faux.setResponses([callTool("a.txt"), say("this second request should never be made")]);
	const agent = new Agent({
		initialState: { systemPrompt: "x", model, tools: [effectTool(counter)] },
		streamFn: models.streamSimple.bind(models),
		finishTurn: async () => ({ action: "end" }),
	});
	await agent.prompt("go");
	return { callCount: faux.state.callCount, runs: counter.runs };
}

const [o, b, rw, tc, fe] = await Promise.all([order(), block(), rewrite(), transformContext(), finishTurnEarly()]);

console.log(JSON.stringify({
	order: o,
	block: b,
	rewrite: rw,
	transformContext: tc,
	finishTurnEarly: fe,
}));