import { test } from "node:test";
import assert from "node:assert/strict";
import { fauxAssistantMessage, fauxText } from "@earendil-works/pi-ai";
import { makeSession, systemPromptSeenByProvider } from "../harness/session.ts";

const SKILL = (name: string, description: string | null, body = "STEP ONE: run the checks.", extra = "") =>
	`---\nname: ${name}\n${description === null ? "" : `description: ${description}\n`}${extra}---\n\n# ${name}\n\n${body}\n`;

const withSkills = (files: Record<string, string>) =>
	makeSession({ extensions: [], agentFiles: files, resourceOptions: { noSkills: false } });

test("the system prompt carries each skill's name, description and path, and not its body", async () => {
	const h = await withSkills({
		"skills/review-guard/SKILL.md": SKILL("review-guard", "Reviews changed code. Use when reviewing a diff.", "SECRET-BODY-TEXT"),
	});
	const prompt = await systemPromptSeenByProvider(h);
	assert.match(prompt, /review-guard/);
	assert.match(prompt, /Reviews changed code\. Use when reviewing a diff\./);
	assert.match(prompt, /SKILL\.md/, "the path is given so the model can read the body");
	assert.doesNotMatch(prompt, /SECRET-BODY-TEXT/, "the body is loaded on demand, not advertised");
	h.dispose();
});

test("a skill with no description is not loaded", async () => {
	const h = await withSkills({ "skills/nodesc/SKILL.md": SKILL("nodesc", null) });
	assert.ok(!(await systemPromptSeenByProvider(h)).includes("nodesc"));
	h.dispose();
});

test("/skill:name loads the body as the request, and arguments are appended", async () => {
	const h = await withSkills({ "skills/review-guard/SKILL.md": SKILL("review-guard", "Reviews code.", "BODY-MARKER") });
	let sent = "";
	h.faux.setResponses([(ctx) => ((sent = JSON.stringify((ctx.messages as any[]).filter((m) => m.role === "user").at(-1))), fauxAssistantMessage([fauxText("ok")]))]);
	await h.session.prompt("/skill:review-guard src/auth only");
	assert.match(sent, /BODY-MARKER/);
	assert.match(sent, /src\/auth only/);
	h.dispose();
});

test("disable-model-invocation hides the skill from the model but not from /skill:name", async () => {
	const h = await withSkills({ "skills/manual/SKILL.md": SKILL("manual", "Only on request.", "MANUAL-BODY", "disable-model-invocation: true\n") });
	assert.doesNotMatch(await systemPromptSeenByProvider(h), /Only on request\./);
	let sent = "";
	h.faux.setResponses([(ctx) => ((sent = JSON.stringify(ctx.messages)), fauxAssistantMessage([fauxText("ok")]))]);
	await h.session.prompt("/skill:manual");
	assert.match(sent, /MANUAL-BODY/);
	h.dispose();
});

test("skills are discovered recursively, unlike prompt templates", async () => {
	const h = await withSkills({ "skills/group/inner/SKILL.md": SKILL("inner", "A nested skill.") });
	assert.match(await systemPromptSeenByProvider(h), /A nested skill\./);
	h.dispose();
});

test("a name collision keeps the first discovered skill", async () => {
	const h = await withSkills({
		"skills/a/SKILL.md": SKILL("review", "FIRST description."),
		"skills/b/SKILL.md": SKILL("review", "SECOND description."),
	});
	const prompt = await systemPromptSeenByProvider(h);
	const first = prompt.includes("FIRST description."), second = prompt.includes("SECOND description.");
	assert.equal(first !== second, true, "exactly one of the two is advertised");
	h.dispose();
});
