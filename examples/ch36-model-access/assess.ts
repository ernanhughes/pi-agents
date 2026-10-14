import {
	Type,
	validateToolCall,
	type Context,
	type Model,
	type Models,
	type Static,
	type Tool,
} from "@earendil-works/pi-ai";

// The result we want from the model. Everything downstream depends on this
// shape, not on the model's prose.
export const EvidenceAssessment = Type.Object({
	verdict: Type.Union([Type.Literal("supported"), Type.Literal("contradicted"), Type.Literal("insufficient")]),
	confidence: Type.Number({ minimum: 0, maximum: 1 }),
	citations: Type.Array(Type.String(), { description: "Evidence items relied on, quoted exactly." }),
	reason: Type.String({ description: "One or two sentences." }),
});
export type EvidenceAssessment = Static<typeof EvidenceAssessment>;

const submit: Tool = {
	name: "submit_assessment",
	description: "Submit your assessment of the claim. Call this exactly once.",
	parameters: EvidenceAssessment,
};

// One model call, no loop, no session. Input in, typed value out.
export async function assess(
	models: Models,
	model: Model<any>,
	claim: string,
	evidence: string[],
): Promise<EvidenceAssessment> {
	const context: Context = {
		systemPrompt: "Decide whether the evidence supports the claim. Use only the evidence given.",
		messages: [
			{
				role: "user",
				content: `Claim: ${claim}\n\nEvidence:\n${evidence.map((e, i) => `${i + 1}. ${e}`).join("\n")}`,
				timestamp: Date.now(),
			},
		],
		tools: [submit],
	};

	const reply = await models.complete(model, context);
	if (reply.stopReason === "error" || reply.stopReason === "aborted") {
		throw new Error(`model call failed: ${reply.errorMessage ?? reply.stopReason}`);
	}

	// toolChoice is only "auto" | "none", so the model is asked to call the tool,
	// not forced to. Check that it did.
	const call = reply.content.find((block) => block.type === "toolCall");
	if (!call) throw new Error("the model answered in prose instead of calling submit_assessment");

	// Throws if the arguments do not match the schema.
	return validateToolCall([submit], call) as EvidenceAssessment;
}
