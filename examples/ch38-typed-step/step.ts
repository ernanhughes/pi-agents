import { Agent, type AgentTool } from "@earendil-works/pi-agent-core";
import type { Model, Models, Static, TSchema } from "@earendil-works/pi-ai";

export interface StepOptions {
	/** How many invalid submissions to tolerate before giving up. */
	maxAttempts?: number;
	/** How many model turns to allow in total, whatever they do. Bounds a model that never submits. */
	maxTurns?: number;
	extraTools?: AgentTool[];
}

// `kind` says which bound or failure ended the step, so a caller can retry a provider
// failure and not a model that answered in prose.
export type StepFailure = "provider" | "invalid-submissions" | "turn-limit" | "no-submit";

export class StepFailed extends Error {
	readonly kind: StepFailure;
	constructor(message: string, kind: StepFailure) {
		super(message);
		this.kind = kind;
	}
}

// One stochastic step as a function: text in, a value that matches `schema` out.
// The model finishes only by calling `submit`. The agent core validates the
// arguments before execute() runs, so execute() only ever sees a valid value.
export async function step<S extends TSchema>(
	models: Models,
	model: Model<any>,
	system: string,
	input: string,
	schema: S,
	options: StepOptions = {},
): Promise<Static<S>> {
	const maxAttempts = options.maxAttempts ?? 3;
	const maxTurns = options.maxTurns ?? 10;
	let result: Static<S> | undefined;

	const submit: AgentTool = {
		name: "submit",
		label: "Submit",
		description: "Submit the final answer. This ends the task. Call it exactly once.",
		parameters: schema,
		async execute(_id, params) {
			// The first valid submission is the answer. A later one cannot
			// overwrite it, so a model that submits twice cannot retroactively
			// change the value this call returns.
			if (result === undefined) result = params as Static<S>;
			return { content: [{ type: "text", text: "accepted" }], details: undefined, terminate: true };
		},
	};

	const agent = new Agent({
		initialState: { systemPrompt: system, model, tools: [submit, ...(options.extraTools ?? [])] },
		streamFn: models.streamSimple.bind(models),
	});

	// An invalid submission comes back to the model as an error result, so the
	// loop re-asks by itself. Bound it, because a model can repeat a mistake.
	// maxAttempts bounds invalid submissions only. A model that never calls submit
	// produces no invalid submission, so the turn count is the bound that covers it.
	//
	// maxTurns bounds the whole run, so it must fire whether or not a submission
	// has been stored. It is not conditional on `result === undefined`, and that
	// is the load-bearing detail: submit returns `terminate: true`, but a batch
	// only ends the turn when every completed result in it agrees (chapter 17).
	// A response carrying submit *and* a non-terminating tool therefore stores a
	// result and keeps looping, and a bound that switched off once a result
	// existed would stop holding exactly then.
	let failures = 0;
	let turns = 0;
	let hitTurnLimit = false;
	agent.subscribe((e) => {
		if (e.type === "tool_execution_end" && e.toolName === "submit" && e.isError && ++failures >= maxAttempts) {
			agent.abort();
		}
		if (e.type === "turn_end" && ++turns >= maxTurns) {
			hitTurnLimit = true;
			agent.abort();
		}
	});

	await agent.prompt(input);

	// A stored submission is already schema-valid, so it is the answer. Returning
	// it after enforcing the bound is deliberate: the bound is there to stop the
	// loop, not to reject a value the model already committed to.
	if (result !== undefined) return result;
	if (failures >= maxAttempts) throw new StepFailed(`no valid submission after ${failures} attempt(s)`, "invalid-submissions");
	if (hitTurnLimit) throw new StepFailed(`no submission after ${turns} turn(s)`, "turn-limit");
	// A failed request is not a model decision. It ends the run with the error on the final message.
	const last = agent.state.messages.findLast((m) => m.role === "assistant");
	if (last && (last.stopReason === "error" || last.stopReason === "aborted")) {
		throw new StepFailed(`model call failed: ${last.errorMessage ?? last.stopReason}`, "provider");
	}
	throw new StepFailed(failures ? `no valid submission after ${failures} attempt(s)` : "the model finished without calling submit", failures ? "invalid-submissions" : "no-submit");
}
