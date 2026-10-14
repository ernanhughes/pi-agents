// Chapter 11 - two kinds of rule in one guard, and what a blocked call looks like.
//
// Loads the chapter's own `ch11-guard/guard.ts` unmodified, plus the retained
// pre-fix version as a control. Every blocked case is checked on the filesystem,
// because "blocked" is a claim about the world and not about the transcript.

import { existsSync } from "node:fs";
import { join } from "node:path";
import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession, UiRecorder } from "../harness/session.ts";
import guard from "../ch11-guard/guard.ts";
import guardOriginal from "../ch11-guard/guard-original.ts";

const bash = (command: string) => fauxAssistantMessage([fauxToolCall("bash", { command })], { stopReason: "toolUse" });

async function attempt(
	extension: any,
	label: string,
	commands: string[],
	answers: boolean[] | null,
) {
	const ui = new UiRecorder();
	if (answers) ui.confirmAnswers = answers;
	const h = await makeSession({ extensions: [extension], ui: answers ? ui : undefined });
	h.faux.setResponses([...commands.map(bash), fauxAssistantMessage([fauxText("done")])]);
	await h.session.prompt("go");
	const results = h.session.messages
		.filter((m) => m.role === "toolResult")
		.map((m: any) => ({ isError: m.isError, text: (m.content[0].text ?? "").split("\n")[0].slice(0, 70) }));
	const ran = ["ran.flag"].map((f) => existsSync(join(h.cwd, f)));
	h.dispose();
	return { label, confirmsShown: ui.confirms.length, results, ran, requests: results.length };
}

const noUI = await attempt(guard, "no UI to ask", ["touch ran.flag && git push --force origin main"], null);
const forcePush = await attempt(guard, "force push, person says yes", ["touch ran.flag && git push --force origin main"], [true]);
const ordinary = await attempt(guard, "ordinary push, person says yes", ["touch ran.flag && git push origin main"], [true]);
const ordinaryRefused = await attempt(guard, "ordinary push, person says no", ["touch ran.flag && git push origin main"], [false]);
const migrations = await attempt(guard, "a migrations/ command, person says yes", ["touch ran.flag && sed -i x migrations/001.sql"], [true]);
const quiet = await attempt(guard, "an unrelated command", ["touch ran.flag && echo harmless"], [true]);

// The retained pre-fix guard, on the same two scenarios. The difference that
// matters is the force push: the original asks a person, the fixed one refuses.
const originalForcePush = await attempt(
	guardOriginal,
	"the first version of this guard, a force push",
	["touch ran.flag && git push --force origin main"],
	[true],
);
const originalOrdinary = await attempt(guardOriginal, "the first version, an ordinary push", ["touch ran.flag && git push origin main"], [true]);

console.log(
	JSON.stringify({
		noUI,
		forcePush,
		ordinary,
		ordinaryRefused,
		migrations,
		quiet,
		originalForcePush,
		originalOrdinary,
	}),
);