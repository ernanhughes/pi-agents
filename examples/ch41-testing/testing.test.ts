import { test } from "node:test";
import assert from "node:assert/strict";
import { Agent } from "@earendil-works/pi-agent-core";
import { Type, createModels, fauxAssistantMessage, fauxProvider, fauxToolCall } from "@earendil-works/pi-ai";
import { step } from "../ch38-typed-step/step.ts";
import { evaluate, seeded } from "./eval.ts";

const Triage = Type.Object({ severity: Type.Union([Type.Literal("low"), Type.Literal("high")]) });

function setup() {
	const faux = fauxProvider();
	const models = createModels();
	models.setProvider(faux.provider);
	return { faux, models, model: faux.getModel() };
}

// ---- Level 1: scripted. Does the code around the model do the right thing? ----
test("level 1: a scripted response drives the code deterministically", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([fauxAssistantMessage([fauxToolCall("submit", { severity: "high" })], { stopReason: "toolUse" })]);
	assert.deepEqual(await step(models, model, "Triage.", "x", Triage), { severity: "high" });
});

// ---- Level 2: structural. Assert on what happened, not on what was said. ----
test("level 2: assert on the event stream, not on the wording", async () => {
	const { faux, models, model } = setup();
	faux.setResponses([fauxAssistantMessage([fauxToolCall("submit", { severity: "low" })], { stopReason: "toolUse" })]);
	const agent = new Agent({
		initialState: {
			systemPrompt: "Triage.",
			model,
			tools: [
				{
					name: "submit",
					label: "submit",
					description: "submit",
					parameters: Triage,
					async execute() {
						return { content: [{ type: "text", text: "ok" }], details: undefined, terminate: true };
					},
				},
			],
		},
		streamFn: models.streamSimple.bind(models),
	});
	const events: string[] = [];
	agent.subscribe((e) => {
		events.push(e.type === "tool_execution_end" ? `tool:${e.toolName}:${e.isError ? "error" : "ok"}` : e.type);
	});
	await agent.prompt("x");

	assert.ok(events.includes("tool:submit:ok"));
	assert.equal(faux.state.callCount, 1, "terminate must save the follow-up request");
	assert.equal(events.filter((e) => e === "turn_start").length, 1);
});

// ---- Level 3: evaluation. How often does it work, over repeated runs? ----
test("level 3: pass^k exposes what the average hides", async () => {
	const rand = seeded(42);
	const { faux, models, model } = setup();

	// A simulated model that is right 85% of the time on every task. This stands
	// in for a real model, which you would call here instead. Each scripted
	// response is consumed by one request, so queue a fresh one per run.
	const run = async () => {
		faux.appendResponses([
			() => fauxAssistantMessage([fauxToolCall("submit", { severity: rand() < 0.85 ? "high" : "low" })], { stopReason: "toolUse" }),
		]);
		return (await step(models, model, "Triage.", "x", Triage)).severity;
	};

	const tasks = Array.from({ length: 40 }, (_, i) => ({ id: `t${i}`, run, passes: (s: string) => s === "high" }));
	const r = await evaluate(tasks, 5);

	console.log(`pass@1=${r.passAt1.toFixed(2)}  pass^5=${r.passPowK.toFixed(2)}`);
	assert.ok(r.passAt1 > 0.75 && r.passAt1 < 0.95, "the average looks healthy");
	assert.ok(r.passPowK < r.passAt1 - 0.2, "reliability across 5 runs is much lower than the average suggests");
	// The chapter quotes these two numbers, so pin them. A change to the seed or the arithmetic fails here.
	assert.equal(r.passAt1.toFixed(2), "0.86");
	assert.equal(r.passPowK.toFixed(2), "0.45");
});

// The branch the chapter tells you to rely on: a step that throws is a failed run.
test("level 3: a thrown step counts as a failed run and does not crash the evaluation", async () => {
	let calls = 0;
	const flaky = {
		id: "flaky",
		// two successes, a throw, then two more successes: 4 of 5 pass
		run: async () => {
			calls++;
			if (calls === 3) throw new Error("model call failed: 429");
			return "high";
		},
		passes: (s: string) => s === "high",
	};
	const alwaysThrows = { id: "broken", run: async (): Promise<string> => { throw new Error("nope"); }, passes: () => true };
	const r = await evaluate([flaky, alwaysThrows], 5);
	assert.equal(calls, 5); // the evaluation kept going after the throw
	assert.equal(r.passAt1, (4 / 5 + 0) / 2);
	assert.equal(r.passPowK, 0); // a throw means the task did not succeed on all k runs
});
