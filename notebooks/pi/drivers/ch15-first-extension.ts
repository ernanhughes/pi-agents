// Chapter 15 - registration, activation and a no-argument call.
//
// Loads the chapter's two extensions unmodified. The tool is `direct`-exposure with
// an optional `base` parameter; the command is `hello`.

import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";
import reviewScope from "../ch15-first-extension/review-scope.ts";
import hello from "../ch15-first-extension/hello.ts";

async function inventory() {
	const h = await makeSession({ extensions: [reviewScope, hello] });
	const registered = h.session.getAllTools().map((t: any) => t.name);
	const active = h.session.getActiveToolNames();
	const callable = h.session.getCallableToolNames();
	const commands = h.session.extensionRunner.getRegisteredCommands().map((c: any) => c.name);
	h.dispose();
	return { registered, active, callable, commands };
}

async function callWith(args: Record<string, unknown> | undefined) {
	const h = await makeSession({ extensions: [reviewScope] });
	h.faux.setResponses([
		fauxAssistantMessage([fauxToolCall("review_scope", args)], { stopReason: "toolUse" }),
		fauxAssistantMessage([fauxText("done")]),
	]);
	await h.session.prompt("what changed?");
	const result = h.session.messages.filter((m) => m.role === "toolResult").at(-1) as any;
	h.dispose();
	return { isError: result.isError, content: result.content?.[0]?.text ?? null, details: result.details ?? null };
}

const noArgs = await callWith({});
const withBase = await callWith({ base: "main" });

console.log(JSON.stringify({ inventory: await inventory(), noArgs, withBase }));