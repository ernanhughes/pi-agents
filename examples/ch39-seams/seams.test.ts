// Probes for the seam matrix in chapter 39. Each test asks one question of one
// hook: can it observe, transform, refuse, and is the effect already done?
import { test } from "node:test";
import assert from "node:assert/strict";
import { Agent, type AgentMessage, type AgentTool } from "@earendil-works/pi-agent-core";
import { Type, createModels, fauxAssistantMessage, fauxProvider, fauxText, fauxToolCall } from "@earendil-works/pi-ai";

function setup() {
	const faux = fauxProvider();
	const models = createModels();
	models.setProvider(faux.provider);
	return { faux, models, model: faux.getModel() };
}

// A tool with a visible side effect, so "was it run?" is a counter, not a guess.
const WriteParams = Type.Object({ path: Type.String() });

function effectTool(counter: { runs: number }): AgentTool<typeof WriteParams> {
	return {
		name: "write_file",
		label: "write_file",
		description: "pretend to write a file",
		parameters: WriteParams,
		async execute(_id, params) {
			counter.runs++;
			return { content: [{ type: "text", text: `wrote ${params.path}` }], details: { path: params.path } };
		},
	};
}

const callTool = (path: string) => fauxAssistantMessage([fauxToolCall("write_file", { path })], { stopReason: "toolUse" });
const say = (t: string) => fauxAssistantMessage([fauxText(t)]);

test("order: where each hook sits in one tool-using run", async () => {
	const { faux, models, model } = setup();
	const counter = { runs: 0 };
	const order: string[] = [];
	faux.setResponses([callTool("a.txt"), say("done")]);

	const agent = new Agent({
		initialState: { systemPrompt: "x", model, tools: [effectTool(counter)] },
		streamFn: models.streamSimple.bind(models),
		transformContext: async (m) => (order.push("transformContext"), m),
		convertToLlm: (m) => (order.push("convertToLlm"), m.filter((x) => ["user", "assistant", "toolResult", "system"].includes(x.role)) as any),
		prepareRequest: () => void order.push("prepareRequest"),
		beforeToolCall: async () => (order.push("beforeToolCall"), undefined),
		afterToolCall: async () => (order.push("afterToolCall"), undefined),
		finishTurn: () => void order.push("finishTurn"),
	});
	agent.subscribe((e) => {
		if (e.type === "tool_execution_start") order.push("tool.execute starts");
		if (e.type === "turn_end") order.push("turn_end");
	});
	await agent.prompt("go");

	// Observed on 1.0.2. Two turns: the tool turn, then the answer turn.
	assert.deepEqual(order, [
		// turn 1: request preparation, then the provider call
		"prepareRequest",
		"transformContext",
		"convertToLlm",
		// the model asked for a tool; execution is announced before the gate runs
		"tool.execute starts",
		"beforeToolCall",
		"afterToolCall",
		"finishTurn",
		"turn_end",
		// turn 2: the same preparation, then the final answer
		"prepareRequest",
		"transformContext",
		"convertToLlm",
		"finishTurn",
		"turn_end",
	]);
});

test("beforeToolCall can refuse, and then the effect never happens", async () => {
	const { faux, models, model } = setup();
	const counter = { runs: 0 };
	faux.setResponses([callTool(".env"), say("ok")]);
	const agent = new Agent({
		initialState: { systemPrompt: "x", model, tools: [effectTool(counter)] },
		streamFn: models.streamSimple.bind(models),
		beforeToolCall: async ({ args }) => ((args as any).path === ".env" ? { block: true, reason: "protected path" } : undefined),
	});
	await agent.prompt("go");
	assert.equal(counter.runs, 0);
	const r = agent.state.messages.find((m) => m.role === "toolResult") as any;
	assert.equal(r.isError, true);
	assert.match(r.content[0].text, /protected path/);
});

test("afterToolCall can rewrite the result but cannot undo the effect", async () => {
	const { faux, models, model } = setup();
	const counter = { runs: 0 };
	faux.setResponses([callTool("a.txt"), say("ok")]);
	const agent = new Agent({
		initialState: { systemPrompt: "x", model, tools: [effectTool(counter)] },
		streamFn: models.streamSimple.bind(models),
		afterToolCall: async () => ({ content: [{ type: "text", text: "[redacted]" }], isError: true }),
	});
	await agent.prompt("go");
	assert.equal(counter.runs, 1, "the write already happened");
	const r = agent.state.messages.find((m) => m.role === "toolResult") as any;
	assert.equal(r.content[0].text, "[redacted]");
	assert.equal(r.isError, true);
});

test("transformContext changes what the provider receives, not what the agent stored", async () => {
	const { faux, models, model } = setup();
	let received: unknown[] = [];
	faux.setResponses([(ctx) => ((received = ctx.messages.map((m: any) => m.role)), say("ok"))]);
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
	assert.equal(sentUsers, 1);
	assert.equal(storedUsers, 2);
});

test("finishTurn can end the run early", async () => {
	const { faux, models, model } = setup();
	const counter = { runs: 0 };
	faux.setResponses([callTool("a.txt"), say("this second request should never be made")]);
	const agent = new Agent({
		initialState: { systemPrompt: "x", model, tools: [effectTool(counter)] },
		streamFn: models.streamSimple.bind(models),
		finishTurn: async () => ({ action: "end" }),
	});
	await agent.prompt("go");
	assert.equal(faux.state.callCount, 1);
	assert.equal(counter.runs, 1, "the tool in the finished turn still ran: finishTurn is after the effect");
});

test("finishTurn can ask for one more request when nothing else would", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([say("first"), say("second")]);
	let asked = 0;
	const agent = new Agent({
		initialState: { systemPrompt: "x", model },
		streamFn: models.streamSimple.bind(models),
		finishTurn: async () => (asked++ === 0 ? { action: "continue" } : undefined),
	});
	await agent.prompt("go");
	assert.equal(faux.state.callCount, 2);
});

test("prepareRequest can swap the model for one request", async () => {
	const faux = fauxProvider({ models: [{ id: "cheap" }, { id: "strong" }] });
	const models = createModels();
	models.setProvider(faux.provider);
	let used = "";
	faux.setResponses([(_ctx, _opts, _state, m) => ((used = m.id), say("ok"))]);
	const agent = new Agent({
		initialState: { systemPrompt: "x", model: faux.getModel("cheap")! },
		streamFn: models.streamSimple.bind(models),
		prepareRequest: () => ({ model: faux.getModel("strong")! }),
	});
	await agent.prompt("go");
	assert.equal(used, "strong");
});

// A tool that calls another tool must go through the same gate. runToolCall is the
// core's function for that. This runs it directly: no model, no credential.
test("runToolCall passes a nested call through beforeToolCall, and a blocked one never executes", async () => {
	const { runToolCall } = await import("@earendil-works/pi-agent-core");
	const counter = { runs: 0 };
	const tools = [effectTool(counter)];
	const call = (path: string) => ({ type: "toolCall" as const, id: `c-${path}`, name: "write_file", arguments: { path } });
	const seen: string[] = [];
	const options = {
		tools,
		assistantMessage: fauxAssistantMessage([]),
		context: { messages: [], tools },
		beforeToolCall: async ({ args }: { args: unknown }) => {
			seen.push((args as { path: string }).path);
			return (args as { path: string }).path === ".env" ? { block: true, reason: "protected path" } : undefined;
		},
	};

	const blocked = await runToolCall(call(".env"), options);
	assert.equal(blocked.isError, true);
	assert.equal(counter.runs, 0); // the gate saw the nested call and execute() never ran

	const allowed = await runToolCall(call("notes.txt"), options);
	assert.equal(allowed.isError, false);
	assert.equal(counter.runs, 1);
	assert.deepEqual(seen, [".env", "notes.txt"]);

	const unknown = await runToolCall({ ...call("x"), name: "no_such_tool" }, options);
	assert.equal(unknown.isError, true); // never rejects for tool failures
});
