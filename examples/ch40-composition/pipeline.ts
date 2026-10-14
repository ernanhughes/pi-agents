import { Type, type Model, type Models, type Static } from "@earendil-works/pi-ai";
import { assess, type EvidenceAssessment } from "../ch36-model-access/assess.ts";
import { makeResearchAgent, type Corpus } from "../ch37-agent-core/research-agent.ts";
import { step } from "../ch38-typed-step/step.ts";

// 1. A plain function. No model. Deterministic, free, testable with no script.
export function retrieve(corpus: Corpus, claim: string): string[] {
	const words = claim.toLowerCase().split(/\W+/).filter((w) => w.length > 3);
	return Object.values(corpus).filter((text) => words.some((w) => text.toLowerCase().includes(w)));
}

// 2. A plain function again: the check the model's output must pass.
// A citation the model invented is not in the evidence, so it fails here.
export function citationsAreReal(a: EvidenceAssessment, evidence: string[]): boolean {
	return a.citations.every((c) => evidence.includes(c));
}

export interface Report {
	claim: string;
	assessment: EvidenceAssessment;
	route: "single call" | "agent escalation";
	summary: string;
}

const Summary = Type.Object({ text: Type.String() });

/** Turns the escalation agent may take before it is cut off. A proposed bound, not Pi's. */
export const ESCALATION_TURNS = 6;

// function -> model call -> function -> (agent only if needed) -> model step.
// The agent is the most expensive part, so it only runs when the cheap path
// cannot decide.
export async function checkClaim(models: Models, model: Model<any>, corpus: Corpus, claim: string): Promise<Report> {
	const evidence = retrieve(corpus, claim);

	let assessment = await assess(models, model, claim, evidence);
	let route: Report["route"] = "single call";

	// Checked after every model call, on every path. The check is a function of the
	// assessment and the evidence that assessment was given.
	const checked = (a: EvidenceAssessment, given: string[]) => {
		if (!citationsAreReal(a, given)) throw new Error("assessment cites evidence that was not provided");
	};
	checked(assessment, evidence);

	if (assessment.verdict === "insufficient") {
		// Composition does not imply agency: this is the only place an agent is used.
		// The escalation is bounded. Nothing else in this function is: a research
		// agent that keeps searching is the one component here that can run away,
		// and an unbounded one turns "spend more when the cheap answer was weak"
		// into an unbounded bill. This is the book's pattern, not Pi's contract.
		const agent = makeResearchAgent(models, model, corpus);
		let turns = 0;
		let overran = false;
		const limit = ESCALATION_TURNS;
		const unsubscribe = agent.subscribe((e) => {
			if (e.type === "turn_end" && ++turns >= limit) {
				overran = true;
				agent.abort();
			}
		});
		try {
			await agent.prompt(`Find more evidence about: ${claim}`);
		} finally {
			unsubscribe();
		}
		// Whatever the agent found is used. A turn limit that hit means the search
		// was cut short, not that it found nothing, so say which happened.
		const ids = new Set(
			agent.state.messages
				.filter((m) => m.role === "toolResult")
				.flatMap((m: any) => (m.details?.hits ?? []) as string[]),
		);
		const extra = [...ids].map((id) => corpus[id]).filter((t) => !evidence.includes(t));
		const second = [...evidence, ...extra];
		// Decide this before spending another model call. An escalation that hit its
		// bound and came back with nothing has not produced evidence to re-decide on,
		// and a second assessment on the same empty set would only re-run the first.
		if (overran && extra.length === 0) throw new Error("escalation was cut off before it found anything");
		assessment = await assess(models, model, claim, second);
		route = "agent escalation";
		checked(assessment, second);
	}

	const summary: Static<typeof Summary> = await step(
		models,
		model,
		"Write one sentence for a reader who has not seen the evidence.",
		JSON.stringify(assessment),
		Summary,
	);

	return { claim, assessment, route, summary: summary.text };
}
