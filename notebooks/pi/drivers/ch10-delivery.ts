// Chapter 10 part 2 - where a message sent mid-turn actually lands.
//
// This is chapter 25's mechanism, reached from chapter 10's question: when you type
// while the agent is working, is your message seen now, at the next boundary, or
// after the run finishes? Uses the book's `slow`-style tool so there is a window.

import { Type, fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";

const slow = (pi: any) =>
	pi.registerTool({
		name: "slow",
		label: "slow",
		description: "waits",
		parameters: Type.Object({}),
		async execute() {
			await new Promise((r) => setTimeout(r, 120));
			return { content: [{ type: "text", text: "slow done" }], details: undefined };
		},
	});

const callSlow = (n = 1) =>
	fauxAssistantMessage(Array.from({ length: n }, () => fauxToolCall("slow", {})), { stopReason: "toolUse" });

/** The user-role texts in a request, in order, with tool results as bare roles. */
const shape = (ctx: any) =>
	(ctx.messages as any[])
		.filter((m) => m.role !== "system")
		.map((m) => (m.role === "user" ? `user:${[].concat(m.content).map((b: any) => b.text ?? b).join("")}` : m.role));

async function delivery(which: "steer" | "followUp") {
	const h = await makeSession({ extensions: [slow] });
	const requests: string[][] = [];
	h.faux.setResponses([
		callSlow(),
		(c: any) => (requests.push(shape(c)), fauxAssistantMessage([fauxText("first answer")])),
		(c: any) => (requests.push(shape(c)), fauxAssistantMessage([fauxText("after the message")])),
	]);

	const running = h.session.prompt("start");
	await new Promise((r) => setTimeout(r, 40));
	if (which === "steer") await h.session.steer("change direction");
	else await h.session.followUp("then also this");
	const disposition = which === "steer" ? "steer" : "followUp";
	await running;
	await h.session.waitForIdle();
	const cleared = h.session.clearQueue();
	h.dispose();
	return { which, requests, pendingAfterClear: h.session ? undefined : undefined, cleared, disposition };
}

const steering = await delivery("steer");
const followUp = await delivery("followUp");

// The refusal case: a prompt sent while streaming with no behaviour declared.
let refusal = "";
{
	const h = await makeSession({ extensions: [slow] });
	h.faux.setResponses([callSlow(), fauxAssistantMessage([fauxText("done")])]);
	const running = h.session.prompt("start");
	await new Promise((r) => setTimeout(r, 40));
	try {
		await h.session.prompt("a second prompt with no behaviour");
		refusal = "accepted";
	} catch (e: any) {
		refusal = `rejected: ${String(e.message).split("\n")[0]}`;
	}
	await h.session.abort();
	await running;
	h.dispose();
}

console.log(JSON.stringify({ steering, followUp, refusal }));