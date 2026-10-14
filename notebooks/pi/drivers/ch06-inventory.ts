// Chapter 6 - what a plain session registers, activates and declares to the model.
//
// Reads a live AgentSession through the book's harness. The three sets it prints
// - registered, active, declared - are the sets the chapter is about.
//
// NB_TOOLS lets the notebook's exercise change the selection without editing code.

import { fauxAssistantMessage, fauxText } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";

async function inventory(tools?: string[]) {
	const h = await makeSession({ extensions: [], tools });
	let declared: string[] | null = null;

	h.faux.appendResponses([
		(ctx: any) => {
			const sys: any = ctx.messages.find((m: any) => m.role === "system");
			declared = (sys?.toolsAdded ?? []).map((t: any) => t.name);
			return fauxAssistantMessage([fauxText("ok")]);
		},
	]);
	await h.session.prompt("go");

	const registered = h.session
		.getAllTools()
		.map((t: any) => ({ name: t.name, exposure: t.exposure ?? "(none)", readOnlyHint: t.annotations?.readOnlyHint ?? null }));
	const active = h.session.getActiveToolNames();
	const callable = h.session.getCallableToolNames();
	h.dispose();
	return { registered, active, callable, declared };
}

const NARROWED: string[] = JSON.parse(process.env.NB_TOOLS ?? '["read", "grep", "find", "ls"]');
console.log(JSON.stringify({ default: await inventory(), narrowed: await inventory(NARROWED) }));