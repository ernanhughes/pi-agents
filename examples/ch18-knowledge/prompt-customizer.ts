import type { BuildSystemPromptOptions, ExtensionAPI } from "@earendil-works/pi-coding-agent";

function buildToolGuidance(options: BuildSystemPromptOptions): string {
	const has = (name: string) => options.selectedTools?.includes(name) ?? false;
	const rules: string[] = [];

	if (has("read")) rules.push("- Use `read` for file contents; it supports text and images.");
	if (has("bash")) rules.push("- Use `bash` for file operations such as `ls`, `find`, and `grep`.");
	if (has("edit")) rules.push("- Use `edit` for precise text replacements that match existing content exactly.");
	if (has("write")) rules.push("- Use `write` to create new files or replace existing files completely.");
	if (options.skills?.length) {
		rules.push(`- Available skills: ${options.skills.map((s) => s.name).join(", ")}.`);
	}
	return rules.join("\n");
}

export default function promptCustomizer(pi: ExtensionAPI) {
	pi.on("before_agent_start", (event) => {
		const guidance = buildToolGuidance(event.systemPromptOptions);
		if (guidance) event.systemPromptOptions.sections.tool_guidance = guidance;
		else delete event.systemPromptOptions.sections.tool_guidance;
	});
}
