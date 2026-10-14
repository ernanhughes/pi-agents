// Chapter 12 - what a prompt template actually produces, and who sees the raw text.
//
// Loads a real template from a real agent directory, sends /review through a real
// session, and captures both the text an `input` handler saw and the user message
// the provider received.

import { fauxAssistantMessage, fauxText } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";

const REVIEW = `---
description: Review uncommitted git changes
argument-hint: "[focus]"
---
Review the uncommitted git changes.
Focus on \${1:-correctness, security, and error handling}.
`;

async function expand(input: string, extra: any[] = []) {
	let rawSeen = "";
	let sentUser = "";
	const spy = (pi: any) =>
		pi.on("input", async (e: any) => {
			rawSeen = e.text;
			return undefined;
		});

	const h = await makeSession({
		extensions: [spy, ...extra],
		agentFiles: { "prompts/review.md": REVIEW },
		resourceOptions: { noPromptTemplates: false },
	});
	h.faux.appendResponses([
		(ctx: any) => {
			const u = (ctx.messages as any[]).filter((m: any) => m.role === "user").at(-1);
			sentUser = [].concat(u.content).map((b: any) => b.text ?? b).join("");
			return fauxAssistantMessage([fauxText("ok")]);
		},
	]);
	await h.session.prompt(input);
	const templates = h.session.promptTemplates.map((p: any) => p.name);
	const calls = h.faux.state.callCount;
	h.dispose();
	return { rawSeen, sentUser, templates, requests: calls };
}

// The whole substitution table in one template, as the chapter's test does.
// Bare $1 / $2 / $@ / $ARGUMENTS, plus the slice forms.
const TABLE = `---
description: substitution table
---
A=[$1] B=[$2] ALL=[$@] ARGUMENTS=[$ARGUMENTS] FROM2=[\${@:2}] 2of2=[\${@:2:2}] NONE=[$3]
`;

async function table() {
	const h = await makeSession({ agentFiles: { "prompts/t.md": TABLE }, resourceOptions: { noPromptTemplates: false } });
	let sent = "";
	h.faux.appendResponses([
		(ctx: any) => {
			const u = (ctx.messages as any[]).filter((m: any) => m.role === "user").at(-1);
			sent = [].concat(u.content).map((b: any) => b.text ?? b).join("");
			return fauxAssistantMessage([fauxText("ok")]);
		},
	]);
	await h.session.prompt("/t a b c");
	h.dispose();
	return sent.trim();
}

// A command registered by an extension of the same name preempts the template.
const commandRan = (pi: any) => {
	(pi as any).ran = false;
	pi.registerCommand("review", { description: "an extension command", handler: async () => void ((pi as any).ran = true) });
};

console.log(
	JSON.stringify({
		default: await expand("/review"),
		argument: await expand('/review "API compatibility"'),
		substitutionTable: await table(),
		withCommand: await expand("/review", [commandRan]),
	}),
);