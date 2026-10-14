// An extension for the SHIPPED `pi` binary. It registers the faux provider as a model, and
// takes its script from the PI_FAUX_SCRIPT environment variable, so a test can drive the real
// CLI, JSON and RPC surfaces with a scripted model and no credential.
//
//   PI_FAUX_SCRIPT='[{"text":"hello"}]'                      one text answer
//   PI_FAUX_SCRIPT='[{"tool":"bash","args":{"command":"x"}},{"text":"done"}]'
//   PI_FAUX_SCRIPT='[{"error":"boom"}]'                      a failed response
import { fauxAssistantMessage, fauxProvider, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

type Step = { text?: string; tool?: string; args?: Record<string, unknown>; error?: string; delayMs?: number };

export default function (pi: ExtensionAPI) {
	const script: Step[] = JSON.parse(process.env.PI_FAUX_SCRIPT ?? "[]");
	const faux = fauxProvider({ tokensPerSecond: Number(process.env.PI_FAUX_TPS ?? 0) || undefined });
	faux.setResponses(
		script.map((s) => {
			if (s.error) return fauxAssistantMessage([], { stopReason: "error", errorMessage: s.error });
			if (s.tool) return fauxAssistantMessage([fauxToolCall(s.tool, (s.args ?? {}) as never)], { stopReason: "toolUse" });
			return fauxAssistantMessage([fauxText(s.text ?? "")]);
		}),
	);
	const model = faux.getModel();
	pi.registerProvider("faux", {
		baseUrl: "http://faux.invalid",
		apiKey: "not-a-real-key",
		api: faux.api as never,
		streamSimple: (m, c, o) => faux.provider.streamSimple!(m, c, o),
		models: [
			{
				id: model.id,
				name: "Faux",
				input: ["text"],
				cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
				reasoning: false,
				contextWindow: 100_000,
				maxTokens: 4096,
			},
		],
	});
}
