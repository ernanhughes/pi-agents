// Chapter 18 - Changing What Pi Knows
// Does a section derived from *active* tools disappear when the tool is disabled, while getAllTools() still reports it?
// Real sessions walking active → disabled → re-enabled; the system message the provider received; the settle-guard's request count.

import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession, systemPromptSeenByProvider } from "../harness/session.ts";
import tools from "../ch17-tools/tools.ts";
import promptCustomizer from "../ch18-knowledge/prompt-customizer.ts";
import reviewGuardSection from "../ch18-knowledge/review-guard-section.ts";
import settleGuard from "../ch18-knowledge/settle-guard.ts";

const say = (t: string) => fauxAssistantMessage([fauxText(t)]);
const runChecks = () => fauxAssistantMessage([fauxToolCall("run_checks", { skipTests: true })], { stopReason: "toolUse" });

async function promptCustomizerTest() {
	const h = await makeSession({ extensions: [promptCustomizer] });
	const prompt = await systemPromptSeenByProvider(h);
	h.dispose();
	return {
		hasToolGuidance: prompt.includes("<tool_guidance>"),
		hasRead: prompt.includes("Use `read` for file contents"),
		hasBash: prompt.includes("Use `bash` for file operations"),
	};
}

async function promptCustomizerOnlyRead() {
	const h = await makeSession({ extensions: [promptCustomizer], tools: ["read"] });
	const prompt = await systemPromptSeenByProvider(h);
	h.dispose();
	return {
		hasRead: prompt.includes("Use `read` for file contents"),
		hasBash: prompt.includes("Use `bash` for file operations"),
	};
}

async function reviewGuardSectionWithTool() {
	const h = await makeSession({ extensions: [tools, reviewGuardSection] });
	const prompt = await systemPromptSeenByProvider(h);
	h.dispose();
	return { hasSection: prompt.includes("run_checks") };
}

async function reviewGuardSectionWithoutTool() {
	const h = await makeSession({ extensions: [reviewGuardSection] });
	const prompt = await systemPromptSeenByProvider(h);
	h.dispose();
	return { hasSection: prompt.includes("run_checks") };
}

async function reviewGuardSectionActive() {
	const h = await makeSession({ extensions: [tools, reviewGuardSection], tools: ["read", "run_checks"] });
	const prompt = await systemPromptSeenByProvider(h);
	h.dispose();
	return { hasSection: prompt.includes("run_checks") };
}

async function reviewGuardSectionDisabled() {
	const h = await makeSession({ extensions: [tools, reviewGuardSection], tools: ["read"] });
	const prompt = await systemPromptSeenByProvider(h);
	h.dispose();
	return { hasSection: prompt.includes("run_checks") };
}

async function reviewGuardSectionReenabled() {
	const h = await makeSession({ extensions: [tools, reviewGuardSection], tools: ["read", "run_checks"] });
	const prompt = await systemPromptSeenByProvider(h);
	h.dispose();
	return { hasSection: prompt.includes("run_checks") };
}

async function accessorProbe() {
	const h = await makeSession({ extensions: [tools, (await import("../ch18-knowledge/accessor-probe.ts")).default] });
	await h.session.prompt("go");
	const { beforeNarrow, registered, active } = (await import("../ch18-knowledge/accessor-probe.ts")).seen;
	h.dispose();
	return { beforeNarrow, registered, active };
}

async function settleGuardNoChecks() {
	const h = await makeSession({ extensions: [tools, settleGuard] });
	h.faux.setResponses([say("looks fine"), say("still fine"), say("third"), say("fourth")]);
	await h.session.prompt("review my diff");
	const callCount = h.faux.state.callCount;
	const messages = JSON.stringify(h.session.messages);
	h.dispose();
	return { callCount, hasNudge: messages.includes("without running `run_checks`") };
}

async function settleGuardWithChecks() {
	const h = await makeSession({ extensions: [tools, settleGuard] });
	h.faux.setResponses([
		runChecks(),
		say("checked, fine"),
		say("must not be requested"),
	]);
	await h.session.prompt("review my diff");
	const callCount = h.faux.state.callCount;
	const messages = JSON.stringify(h.session.messages);
	h.dispose();
	return { callCount, hasNudge: messages.includes("without running `run_checks`") };
}

const [
	pc,
	pcOnlyRead,
	rgWith,
	rgWithout,
	rgActive,
	rgDisabled,
	rgReenabled,
	accessor,
	settleNoChecks,
	settleWithChecks,
] = await Promise.all([
	promptCustomizerTest(),
	promptCustomizerOnlyRead(),
	reviewGuardSectionWithTool(),
	reviewGuardSectionWithoutTool(),
	reviewGuardSectionActive(),
	reviewGuardSectionDisabled(),
	reviewGuardSectionReenabled(),
	accessorProbe(),
	settleGuardNoChecks(),
	settleGuardWithChecks(),
]);

console.log(JSON.stringify({
	promptCustomizer: pc,
	promptCustomizerOnlyRead: pcOnlyRead,
	reviewGuardWithTool: rgWith,
	reviewGuardWithoutTool: rgWithout,
	reviewGuardActive: rgActive,
	reviewGuardDisabled: rgDisabled,
	reviewGuardReenabled: rgReenabled,
	accessor: { beforeNarrow: accessor.beforeNarrow, registered: accessor.registered, active: accessor.active },
	settleNoChecks,
	settleWithChecks,
}));