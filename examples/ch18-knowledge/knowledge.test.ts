import { test } from "node:test";
import assert from "node:assert/strict";
import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession, systemPromptSeenByProvider } from "../harness/session.ts";
import tools from "../ch17-tools/tools.ts";
import promptCustomizer from "./prompt-customizer.ts";
import reviewGuardSection from "./review-guard-section.ts";
import accessorProbe, { reset, seen } from "./accessor-probe.ts";
import settleGuard from "./settle-guard.ts";

const say = (t: string) => fauxAssistantMessage([fauxText(t)]);

test("prompt-customizer: the tool guidance section is derived from the tools that are active", async () => {
	const h = await makeSession({ extensions: [promptCustomizer] });
	const prompt = await systemPromptSeenByProvider(h);
	assert.match(prompt, /<tool_guidance>/, "a section is delivered to the provider wrapped in its name");
	assert.match(prompt, /Use `read` for file contents/);
	assert.match(prompt, /Use `bash` for file operations/);
	h.dispose();
});

test("prompt-customizer: a tool that is not active is not described", async () => {
	const h = await makeSession({ extensions: [promptCustomizer], tools: ["read"] });
	const prompt = await systemPromptSeenByProvider(h);
	assert.match(prompt, /Use `read` for file contents/);
	assert.doesNotMatch(prompt, /<tool_guidance>[\s\S]*Use `bash` for file operations/);
	h.dispose();
});

test("review-guard section appears when run_checks is active and disappears with it", async () => {
	const withTool = await makeSession({ extensions: [tools, reviewGuardSection] });
	assert.match(await systemPromptSeenByProvider(withTool), /`run_checks` runs this repository's type check/);
	withTool.dispose();

	const without = await makeSession({ extensions: [reviewGuardSection] });
	assert.doesNotMatch(await systemPromptSeenByProvider(without), /run_checks/);
	without.dispose();
});

// The distinction that a registered-vs-absent test cannot see. run_checks is
// registered in every session below; the only difference is the active selection.
test("review-guard section tracks the active tool set, not the registered one", async () => {
	const active = await makeSession({ extensions: [tools, reviewGuardSection], tools: ["read", "run_checks"] });
	assert.match(await systemPromptSeenByProvider(active), /`run_checks` runs this repository's type check/);
	active.dispose();

	// Registered, but not active. Describing it would tell the model to use a tool
	// it has not been given.
	const disabled = await makeSession({ extensions: [tools, reviewGuardSection], tools: ["read"] });
	assert.doesNotMatch(await systemPromptSeenByProvider(disabled), /`run_checks` runs this repository's type check/);
	disabled.dispose();

	// Re-enabled: the section comes back, because the condition is evaluated per run.
	const reenabled = await makeSession({ extensions: [tools, reviewGuardSection], tools: ["read", "run_checks"] });
	assert.match(await systemPromptSeenByProvider(reenabled), /`run_checks` runs this repository's type check/);
	reenabled.dispose();
});

test("getAllTools would have reported the disabled tool; getActiveTools does not", async () => {
	// Pins the reason the example uses the active set: the two accessors disagree
	// exactly when a tool is registered but not active.
	// Read through locals: clearing the shared object and then reading it back
	// narrows the properties to `never` in TypeScript's control flow.
	reset();
	const h = await makeSession({ extensions: [tools, accessorProbe] });
	await h.session.prompt("go");
	const { beforeNarrow, registered, active } = seen;
	assert.ok(beforeNarrow?.includes("run_checks"), "run_checks starts active");
	assert.ok(registered?.includes("run_checks"), "registered, which is what getAllTools() reports");
	assert.ok(!active?.includes("run_checks"), "not active, which is what the model can actually call");
	h.dispose();
});

test("settle-guard: answering without running the checks buys exactly one more request", async () => {
	const h = await makeSession({ extensions: [tools, settleGuard] });
	h.faux.setResponses([say("looks fine"), say("still fine"), say("third"), say("fourth")]);
	await h.session.prompt("review my diff");
	console.log("requests when the model never runs run_checks:", h.faux.state.callCount);
	assert.equal(h.faux.state.callCount, 2, "one continuation, not a loop");
	assert.match(JSON.stringify(h.session.messages), /without running `run_checks`/);
	h.dispose();
});

test("settle-guard: having run the checks, the model is not asked again", async () => {
	const h = await makeSession({ extensions: [tools, settleGuard] });
	h.faux.setResponses([
		fauxAssistantMessage([fauxToolCall("run_checks", { skipTests: true })], { stopReason: "toolUse" }),
		say("checked, fine"),
		say("must not be requested"),
	]);
	await h.session.prompt("review my diff");
	assert.equal(h.faux.state.callCount, 2);
	assert.doesNotMatch(JSON.stringify(h.session.messages), /without running `run_checks`/);
	h.dispose();
});
