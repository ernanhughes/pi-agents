// One shared experimental history for chapters 4, 5, 23 and 24: state over time.
//
//   user A  -> assistant A
//   user B  -> assistant B (a bash tool call) -> tool result -> assistant B (answer)
//   user C  -> assistant C
//
// Persisted to a real JSONL file. Each chapter reads a different property of the same run.
import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import type { ExtensionFactory } from "@earendil-works/pi-coding-agent";
import { makeSession, type Harness, type HarnessOptions } from "./session.ts";

export const pad = (label: string, n = 40) => `${label}: ${"the schema has a billing table. ".repeat(n)}`;

export interface History {
	h: Harness;
	file: string;
	entries: () => any[];
	userEntry: (text: string) => any;
}

export async function buildHistory(options: Partial<HarnessOptions> = {}): Promise<History> {
	const h = await makeSession({ extensions: [], persist: true, ...options } as HarnessOptions);
	const say = (t: string) => fauxAssistantMessage([fauxText(t)]);

	h.faux.setResponses([say(pad("answer A"))]);
	await h.session.prompt("question A");

	h.faux.setResponses([fauxAssistantMessage([fauxToolCall("bash", { command: "echo from-tool-B" })], { stopReason: "toolUse" }), say(pad("answer B"))]);
	await h.session.prompt("question B");

	h.faux.setResponses([say(pad("answer C"))]);
	await h.session.prompt("question C");

	const entries = () => h.session.sessionManager.getEntries() as any[];
	const userEntry = (text: string) =>
		entries().find((e) => e.type === "message" && e.message.role === "user" && JSON.stringify(e.message.content).includes(text));
	return { h, file: h.session.sessionManager.getSessionFile()!, entries, userEntry };
}

/** Capture the request the provider receives for the next prompt. */
export async function requestFor(h: Harness, text: string): Promise<any[]> {
	let sent: any[] = [];
	h.faux.setResponses([(ctx: any) => ((sent = [...ctx.messages]), fauxAssistantMessage([fauxText("ok")]))]);
	await h.session.prompt(text);
	return sent;
}

export const userTexts = (messages: any[]) =>
	messages.filter((m) => m.role === "user").map((m) => (typeof m.content === "string" ? m.content : m.content.map((b: any) => b.text ?? "").join("")));

export type { ExtensionFactory };
