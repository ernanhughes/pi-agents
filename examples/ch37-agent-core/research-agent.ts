import { Agent, type AgentTool } from "@earendil-works/pi-agent-core";
import { Type, type Model, type Models } from "@earendil-works/pi-ai";

export interface Corpus {
	[id: string]: string;
}

// A tool is data plus one function. This one is read-only and pure, so it is
// safe to run in parallel with itself.
const LookupParams = Type.Object({ query: Type.String() });

export function lookupEvidence(corpus: Corpus): AgentTool<typeof LookupParams> {
	return {
		name: "lookup_evidence",
		label: "Look up evidence",
		description: "Return the corpus entries whose text contains the query. Use short keywords.",
		parameters: LookupParams,
		async execute(_id, params) {
			const q = params.query.toLowerCase();
			const hits = Object.entries(corpus).filter(([, text]) => text.toLowerCase().includes(q));
			const text = hits.length ? hits.map(([id, t]) => `[${id}] ${t}`).join("\n") : "no matches";
			return { content: [{ type: "text", text }], details: { query: params.query, hits: hits.map(([id]) => id) } };
		},
	};
}

// The agent core takes exactly two things from the outside: a model and a
// stream function. The prompt, the tools and the transcript are ours.
export function makeResearchAgent(models: Models, model: Model<any>, corpus: Corpus): Agent {
	return new Agent({
		initialState: {
			systemPrompt: "Research the claim using lookup_evidence. Answer in one sentence.",
			model,
			tools: [lookupEvidence(corpus)],
		},
		streamFn: models.streamSimple.bind(models),
	});
}
