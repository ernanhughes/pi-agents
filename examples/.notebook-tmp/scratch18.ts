// scratch
import { makeSession, systemPromptSeenByProvider } from "../harness/session.ts";
import tools from "../ch17-tools/tools.ts";
import promptCustomizer from "../ch18-knowledge/prompt-customizer.ts";
import reviewGuardSection from "../ch18-knowledge/review-guard-section.ts";

async function scenario(active: string[] | undefined) {
	const h = await makeSession({
		extensions: [tools, reviewGuardSection, promptCustomizer],
		tools: active,
	});
	const prompt = await systemPromptSeenByProvider(h);
	const out = {
		registered: h.session.getAllTools().map((t: any) => t.name),
		active: h.session.getActiveToolNames(),
		hasGuardSection: prompt.includes("`run_checks` runs this repository's type check"),
		hasBashGuidance: prompt.includes("Use `bash` for file operations"),
		systemPromptAccessorHasSection: h.session.systemPrompt.includes("run_checks"),
		systemPromptLen: h.session.systemPrompt.length,
	};
	h.dispose();
	return out;
}

console.log(JSON.stringify({ all: await scenario(undefined), readOnly: await scenario(["read"]), both: await scenario(["read", "run_checks"]) }, null, 2));
