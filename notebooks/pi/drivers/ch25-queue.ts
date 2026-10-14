// Chapter 25 - Steering, Queuing, and Changing Direction
// Where does a queued message land relative to a turn's tool calls?

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

const shape = (ctx: any) =>
	(ctx.messages as any[]).filter((m) => m.role !== "system").map((m) => (m.role === "user" ? `user:${[].concat(m.content).map((b: any) => b.text ?? b).join("")}` : m.role));

async function steering() {
	const h = await makeSession({ extensions: [slow] });
	let second: string[] = [];
	h.faux.setResponses([callSlow(), (ctx: any) => ((second = shape(ctx)), fauxAssistantMessage([fauxText("ok")]))]);
	const running = h.session.prompt("start");
	await new Promise((r) => setTimeout(r, 40));
	await h.session.steer("change direction");
	await running;
	h.dispose();
	return { second };
}

async function followUp() {
	const h = await makeSession({ extensions: [slow] });
	const requests: string[][] = [];
	h.faux.setResponses([callSlow(), (c: any) => (requests.push(shape(c)), fauxAssistantMessage([fauxText("first answer")])), (c: any) => (requests.push(shape(c)), fauxAssistantMessage([fauxText("after follow-up")]))]);
	const running = h.session.prompt("start");
	await new Promise((r) => setTimeout(r, 40));
	await h.session.followUp("then also this");
	await running;
	await h.session.waitForIdle();
	h.dispose();
	return { requests };
}

async function steerBeforeFollowUp() {
	const h = await makeSession({ extensions: [slow] });
	const requests: string[][] = [];
	h.faux.setResponses([
		callSlow(),
		(c: any) => (requests.push(shape(c)), fauxAssistantMessage([fauxText("a")])),
		(c: any) => (requests.push(shape(c)), fauxAssistantMessage([fauxText("b")])),
	]);
	const running = h.session.prompt("start");
	await new Promise((r) => setTimeout(r, 40));
	await h.session.followUp("FOLLOW");
	await h.session.steer("STEER");
	await running;
	await h.session.waitForIdle();
	h.dispose();
	return { requests };
}

async function queueUpdate() {
	const h = await makeSession({ extensions: [slow] });
	const updates: { steering: string[]; followUp: string[] }[] = [];
	h.session.subscribe((e: any) => {
		if (e.type === "queue_update") updates.push({ steering: [...e.steering], followUp: [...e.followUp] });
	});
	h.faux.setResponses([callSlow(), fauxAssistantMessage([fauxText("a")]), fauxAssistantMessage([fauxText("b")])]);
	const running = h.session.prompt("start");
	await new Promise((r) => setTimeout(r, 40));
	await h.session.steer("one");
	await h.session.followUp("two");
	await running;
	await h.session.waitForIdle();
	h.dispose();
	return { updates };
}

async function deliveryMode() {
	const results: Record<string, string[]> = {};
	for (const [mode, expectedInFirst] of [["one-at-a-time", ["user:S1"]], ["all", ["user:S1", "user:S2"]]] as const) {
		const h = await makeSession({ extensions: [slow], settings: { steeringMode: mode } });
		let first: string[] = [];
		h.faux.setResponses([callSlow(), (c: any) => ((first = shape(c)), fauxAssistantMessage([fauxText("a")])), fauxAssistantMessage([fauxText("b")])]);
		const running = h.session.prompt("start");
		await new Promise((r) => setTimeout(r, 40));
		await h.session.steer("S1");
		await h.session.steer("S2");
		await running;
		await h.session.waitForIdle();
		h.dispose();
		results[mode] = first.filter((x) => x === "user:S1" || x === "user:S2");
	}
	return results;
}

async function promptWhileStreaming() {
	const h = await makeSession({ extensions: [slow] });
	h.faux.setResponses([callSlow(), fauxAssistantMessage([fauxText("a")])]);
	const running = h.session.prompt("start");
	await new Promise((r) => setTimeout(r, 40));
	let error = "";
	try {
		await h.session.prompt("no behaviour given");
	} catch (e: any) {
		error = String(e.message);
	}
	await running;
	h.dispose();
	return { error };
}

async function clearQueue() {
	const h = await makeSession({ extensions: [slow] });
	h.faux.setResponses([callSlow(), fauxAssistantMessage([fauxText("a")])]);
	const running = h.session.prompt("start");
	await new Promise((r) => setTimeout(r, 40));
	await h.session.steer("S1");
	await h.session.followUp("F1");
	const cleared = h.session.clearQueue();
	const pending = h.session.pendingMessageCount;
	await running;
	h.dispose();
	return { cleared, pending };
}

async function commandWhileStreaming() {
	let ranWhileStreaming: boolean | undefined;
	let session: any;
	const ext = (pi: any) => {
		slow(pi);
		pi.registerCommand("status", { description: "s", handler: async () => void (ranWhileStreaming = session.isStreaming) });
	};
	const h = await makeSession({ extensions: [ext] });
	session = h.session;
	h.faux.setResponses([callSlow(), fauxAssistantMessage([fauxText("a")])]);
	const running = h.session.prompt("start");
	await new Promise((r) => setTimeout(r, 40));
	await h.session.prompt("/status", { streamingBehavior: "steer" } as any);
	let steerError = "";
	try {
		await h.session.steer("/status");
	} catch (e: any) {
		steerError = String(e.message);
	}
	await running;
	h.dispose();
	return { ranWhileStreaming, steerError };
}

const [
	steeringResult,
	followUpResult,
	steerBeforeFollowUpResult,
	queueUpdateResult,
	deliveryModeResult,
	promptWhileStreamingResult,
	clearQueueResult,
	commandWhileStreamingResult,
] = await Promise.all([
	steering(),
	followUp(),
	steerBeforeFollowUp(),
	queueUpdate(),
	deliveryMode(),
	promptWhileStreaming(),
	clearQueue(),
	commandWhileStreaming(),
]);

console.log(JSON.stringify({
	steering: { second: steeringResult.second },
	followUp: { requests: followUpResult.requests },
	steerBeforeFollowUp: { requests: steerBeforeFollowUpResult.requests },
	queueUpdate: { updates: queueUpdateResult.updates },
	deliveryMode: deliveryModeResult,
	promptWhileStreaming: { error: promptWhileStreamingResult.error },
	clearQueue: { cleared: clearQueueResult.cleared, pending: clearQueueResult.pending },
	commandWhileStreaming: { ranWhileStreaming: commandWhileStreamingResult.ranWhileStreaming, steerError: commandWhileStreamingResult.steerError },
}));