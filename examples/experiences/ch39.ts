// Chapter 39: where in the loop a decision can still be intercepted.
// The same scripted run, three ways: no gate, a gate before the effect, a rewrite after it.
import { Agent, type AgentTool } from "@earendil-works/pi-agent-core";
import { Type, createModels, fauxAssistantMessage, fauxProvider, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { Recorder, finish, type Observation, type Run, type Trace } from "./envelope.ts";

const Write = Type.Object({ path: Type.String() });
const say = (t: string) => fauxAssistantMessage([fauxText(t)]);

async function scenario(label: string, gate: "none" | "before" | "after") {
	const rec = new Recorder();
	const faux = fauxProvider();
	const models = createModels();
	models.setProvider(faux.provider);
	const effect = { executed: 0, wrote: [] as string[] };
	let denialSeenByModel = false;

	const tool: AgentTool<typeof Write> = {
		name: "write_file",
		label: "write_file",
		description: "write a file",
		parameters: Write,
		async execute(_id, params) {
			effect.executed++;
			effect.wrote.push(params.path);
			rec.log("effect", "tool.execute", `execute() RAN and wrote ${params.path}`, { path: params.path });
			return { content: [{ type: "text", text: `wrote ${params.path}` }], details: { path: params.path } };
		},
	};

	faux.setResponses([
		(ctx: any) => {
			rec.log("model", "request", "the model is asked", { messages: ctx.messages.length });
			return fauxAssistantMessage([fauxToolCall("write_file", { path: ".env" })], { stopReason: "toolUse" });
		},
		(ctx: any) => {
			const result = (ctx.messages as any[]).findLast((m) => m.role === "toolResult");
			denialSeenByModel = Boolean(result?.isError);
			rec.log("model", "request", `the model is asked again and receives: ${result ? (result.isError ? "an ERROR result" : "an ok result") : "no result"}`, { isError: result?.isError });
			return say("done");
		},
	]);

	const agent = new Agent({
		initialState: { systemPrompt: "x", model: faux.getModel(), tools: [tool] },
		streamFn: models.streamSimple.bind(models),
		prepareRequest: () => void rec.log("core hook", "prepareRequest", "prepareRequest: before the provider is called"),
		transformContext: async (m) => (rec.log("core hook", "transformContext", "transformContext: what is sent can still change"), m),
		beforeToolCall: async ({ args }) => {
			const decision = gate === "before" && (args as any).path === ".env" ? "BLOCK" : "allow";
			rec.log("core hook", "beforeToolCall", `beforeToolCall sees write_file(.env): ${decision}. Nothing has run yet`, { decision });
			return decision === "BLOCK" ? { block: true, reason: "protected path" } : undefined;
		},
		afterToolCall: async () => {
			rec.log("core hook", "afterToolCall", gate === "after" ? "afterToolCall REWRITES the result to [redacted]. The effect already happened" : "afterToolCall: the tool has already finished");
			return gate === "after" ? { content: [{ type: "text" as const, text: "[redacted]" }], isError: true } : undefined;
		},
		finishTurn: async () => void rec.log("core hook", "finishTurn", "finishTurn: the turn's tools are finished"),
	});
	agent.subscribe((e) => {
		if (e.type === "tool_execution_start") rec.log("loop", "tool_execution_start", "tool_execution_start is announced BEFORE beforeToolCall decides");
		if (e.type === "tool_execution_end") rec.log("loop", "tool_execution_end", `tool_execution_end: isError=${e.isError}`);
	});
	await agent.prompt("write the token");
	rec.log("result", "effect.count", `execute() invocation count: ${effect.executed}`, { executed: effect.executed });

	const run: Run = {
		id: gate,
		label,
		description: { none: "No gate. The call goes through.", before: "beforeToolCall blocks the call.", after: "afterToolCall rewrites the result, too late." }[gate],
		events: rec.events,
	};
	return { run, effect, denialSeenByModel };
}

export async function ch39(): Promise<Trace> {
	const none = await scenario("1. No gate", "none");
	const before = await scenario("2. Gate before the effect", "before");
	const after = await scenario("3. Rewrite after the effect", "after");

	const at = (r: Run, type: string) => r.events.findIndex((e) => e.type === type);
	const o = (id: string, label: string, expected: string, observed: string, pass: boolean | null): Observation => ({ id, label, expected, observed, pass });
	const gateSaw = at(before.run, "beforeToolCall") >= 0;

	const observations: Observation[] = [
		o("proposed", "The model proposed the forbidden call (run 2)", "yes", gateSaw ? "yes" : "no", gateSaw),
		o("zero", "execute() invocations when the gate blocks", "0", String(before.effect.executed), before.effect.executed === 0),
		o("absent", "The side effect exists when the gate blocks", "no", before.effect.wrote.length === 0 ? "no" : "yes", before.effect.wrote.length === 0),
		o("denial", "The model received the denial as an error result", "yes", before.denialSeenByModel ? "yes" : "no", before.denialSeenByModel),
		o("baseline", "Without a gate, execute() ran", "1", String(none.effect.executed), none.effect.executed === 1),
		o("late", "A rewrite after the effect cannot undo it: execute() invocations", "1", String(after.effect.executed), after.effect.executed === 1),
		o("start-before-gate", "tool_execution_start is announced before the gate decides (run 2)", "yes", at(before.run, "tool_execution_start") < at(before.run, "beforeToolCall") ? "yes" : "no", at(before.run, "tool_execution_start") < at(before.run, "beforeToolCall")),
	];

	return finish({
		chapter: { number: 39, title: "Seams, Hooks, and Irreversible Decisions" },
		experiment: { id: "pi/chapter-39/before-tool-call", title: "Where a decision can still be stopped" },
		evidenceScope: "in_process_runtime",
		claim: "Of the agent core's hooks only beforeToolCall can refuse, and it fires before the effect. A hook after the effect can rewrite what the model is told but cannot undo what happened.",
		prediction: "With the gate before the effect, execute() runs zero times and the side effect is absent. With a rewrite after the effect, execute() has already run once.",
		source: { test: "examples/ch39-seams/seams.test.ts", exporter: "examples/experiences/ch39.ts" },
		runs: [none.run, before.run, after.run],
		observations,
		limits: [
			"The model is scripted: it proposes the forbidden call because the script says so. This shows what the loop does when a call is proposed, not how often a real model proposes one.",
			"One tool and one forbidden path.",
		],
	});
}
