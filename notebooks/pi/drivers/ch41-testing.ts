// Chapter 41 - Testing Stochastic Software
// How far apart are pass@1 and pass^5, and what does the gap hide?
// The chapter's own evaluate() over 40 tasks x 5 runs of a seeded 85% step, reproducing pass@1 = 0.86, pass^5 = 0.45; a thrown step counted as a failed run.

import { createModels, fauxAssistantMessage, fauxProvider, fauxToolCall } from "@earendil-works/pi-ai";
import { step } from "../ch38-typed-step/step.ts";
import { evaluate, seeded } from "../ch41-testing/eval.ts";
import { Type } from "@earendil-works/pi-ai";

const Triage = Type.Object({ severity: Type.Union([Type.Literal("low"), Type.Literal("high")]) });

function setup() {
	const faux = fauxProvider();
	const models = createModels();
	models.setProvider(faux.provider);
	return { faux, models, model: faux.getModel() };
}

async function passK() {
	const rand = seeded(42);
	const { faux, models, model } = setup();
	const run = async () => {
		faux.appendResponses([() => fauxAssistantMessage([fauxToolCall("submit", { severity: rand() < 0.85 ? "high" : "low" })], { stopReason: "toolUse" })]);
		return (await step(models, model, "Triage.", "x", Triage)).severity;
	};
	const tasks = Array.from({ length: 40 }, (_, i) => ({ id: `t${i}`, run, passes: (s: string) => s === "high" }));
	const r = await evaluate(tasks, 5);
	return { passAt1: r.passAt1, passPowK: r.passPowK };
}

async function thrownStep() {
	let calls = 0;
	const flaky = {
		id: "flaky",
		run: async () => {
			calls++;
			if (calls === 3) throw new Error("model call failed: 429");
			return "high";
		},
		passes: (s: string) => s === "high",
	};
	const alwaysThrows = { id: "broken", run: async (): Promise<string> => { throw new Error("nope"); }, passes: () => true };
	const r = await evaluate([flaky, alwaysThrows], 5);
	return { calls, passAt1: r.passAt1, passPowK: r.passPowK };
}

const [pk, ts] = await Promise.all([passK(), thrownStep()]);

console.log(JSON.stringify({
	passK: { passAt1: Number(pk.passAt1.toFixed(2)), passPowK: Number(pk.passPowK.toFixed(2)) },
	thrownStep: ts,
}));