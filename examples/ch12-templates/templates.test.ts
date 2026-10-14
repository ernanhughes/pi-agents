import { test } from "node:test";
import assert from "node:assert/strict";
import { fauxAssistantMessage, fauxText } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";

const REVIEW = `---
description: Review uncommitted git changes
argument-hint: "[focus]"
---
Review the uncommitted git changes (\`git status --short\`, \`git diff\`).
Focus on \${1:-correctness, security, and error handling}.
Keep findings short, ordered by severity, each with the file path.
`;

/** Run one prompt through a real session and return the text the provider received as the last user message. */
async function expand(files: Record<string, string>, input: string, extensions: any[] = []): Promise<string> {
	const h = await makeSession({
		extensions,
		agentFiles: files,
		resourceOptions: { noPromptTemplates: false },
	});
	let sent = "";
	h.faux.setResponses([(ctx) => {
		const users = (ctx.messages as any[]).filter((m) => m.role === "user");
		sent = JSON.stringify(users.at(-1)?.content);
		return fauxAssistantMessage([fauxText("ok")]);
	}]);
	await h.session.prompt(input);
	h.dispose();
	return JSON.parse(sent).map?.((b: any) => b.text).join("") ?? JSON.parse(sent);
}

test("${1:-default}: the default applies with no argument", async () => {
	const out = await expand({ "prompts/review.md": REVIEW }, "/review");
	assert.match(out, /Focus on correctness, security, and error handling\./);
});

test("an argument replaces the default", async () => {
	const out = await expand({ "prompts/review.md": REVIEW }, "/review concurrency");
	assert.match(out, /Focus on concurrency\./);
	assert.doesNotMatch(out, /correctness, security/);
});

test("shell-like quoting: a quoted phrase is one argument", async () => {
	const out = await expand({ "prompts/review.md": REVIEW }, '/review "API compatibility"');
	assert.match(out, /Focus on API compatibility\./);
});

test("the substitution table: $1, $2, $@, $ARGUMENTS, ${@:N}, ${@:N:L}", async () => {
	const t = `---\ndescription: t\n---\n[$1][$2][$@][$ARGUMENTS][\${@:2}][\${@:2:1}][\${9:-none}]`;
	const out = await expand({ "prompts/t.md": t }, "/t a b c");
	assert.equal(out.trim(), "[a][b][a b c][a b c][b c][b][none]");
});

test("an extension command with the same name wins over the template", async () => {
	let ran = false;
	const ext = (pi: any) => pi.registerCommand("review", { description: "mine", handler: async () => void (ran = true) });
	const h = await makeSession({ extensions: [ext], agentFiles: { "prompts/review.md": REVIEW }, resourceOptions: { noPromptTemplates: false } });
	h.faux.setResponses([fauxAssistantMessage([fauxText("should not be requested")])]);
	await h.session.prompt("/review");
	assert.equal(ran, true);
	assert.equal(h.faux.state.callCount, 0, "the command handled it, so no model request was made");
	h.dispose();
});

test("an extension input handler sees the raw text before expansion", async () => {
	let raw = "";
	const ext = (pi: any) => pi.on("input", async (e: any) => void (raw = e.text));
	await expand({ "prompts/review.md": REVIEW }, "/review concurrency", [ext]);
	assert.equal(raw, "/review concurrency");
});

test("conventional prompt directories load direct .md children only", async () => {
	const h = await makeSession({
		extensions: [],
		agentFiles: { "prompts/top.md": "---\ndescription: top\n---\nTOP", "prompts/nested/deep.md": "---\ndescription: deep\n---\nDEEP" },
		resourceOptions: { noPromptTemplates: false },
	});
	const names = h.session.promptTemplates.map((p: any) => p.name);
	assert.ok(names.includes("top"));
	assert.ok(!names.includes("deep"), "a nested template is not discovered by convention");
	h.dispose();
});
