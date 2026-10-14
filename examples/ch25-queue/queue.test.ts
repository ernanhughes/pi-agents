import { test } from "node:test";
import assert from "node:assert/strict";
import { Type, fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";

// A tool that takes a moment, so there is a window in which to steer.
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

/** The user-role texts in a request, in order, with tool results shown as a marker. */
const shape = (ctx: any) =>
	(ctx.messages as any[]).filter((m) => m.role !== "system").map((m) => (m.role === "user" ? `user:${[].concat(m.content).map((b: any) => b.text ?? b).join("")}` : m.role));

test("steering lands after the turn's tool calls and before the next request", async () => {
	const h = await makeSession({ extensions: [slow] });
	let second: string[] = [];
	h.faux.setResponses([callSlow(), (ctx: any) => ((second = shape(ctx)), fauxAssistantMessage([fauxText("ok")]))]);

	const running = h.session.prompt("start");
	await new Promise((r) => setTimeout(r, 40));
	await h.session.steer("change direction");
	await running;

	assert.deepEqual(second, ["user:start", "assistant", "toolResult", "user:change direction"]);
	h.dispose();
});

test("a follow-up waits until the agent would otherwise stop", async () => {
	const h = await makeSession({ extensions: [slow] });
	const requests: string[][] = [];
	h.faux.setResponses([callSlow(), (c: any) => (requests.push(shape(c)), fauxAssistantMessage([fauxText("first answer")])), (c: any) => (requests.push(shape(c)), fauxAssistantMessage([fauxText("after follow-up")]))]);

	const running = h.session.prompt("start");
	await new Promise((r) => setTimeout(r, 40));
	await h.session.followUp("then also this");
	await running;
	await h.session.waitForIdle();

	assert.ok(!requests[0].includes("user:then also this"), "not delivered while the agent still had work");
	assert.ok(requests[1].includes("user:then also this"), "delivered once it was done");
	h.dispose();
});

test("steering drains before follow-ups", async () => {
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
	assert.ok(requests[0].includes("user:STEER") && !requests[0].includes("user:FOLLOW"));
	h.dispose();
});

test("queue_update carries the complete queue each time, not a delta", async () => {
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
	assert.deepEqual(updates[0], { steering: ["one"], followUp: [] });
	assert.deepEqual(updates[1], { steering: ["one"], followUp: ["two"] }, "the second update still lists the first message");
	assert.deepEqual(updates.at(-1), { steering: [], followUp: [] }, "and the queue ends empty");
	h.dispose();
});

test("one-at-a-time (the default) delivers one steering message per turn; all delivers every queued message", async () => {
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
		assert.deepEqual(first.filter((x) => x === "user:S1" || x === "user:S2"), expectedInFirst, mode);
		h.dispose();
	}
});

test("a prompt while streaming, with no behaviour, is an error rather than a guess", async () => {
	const h = await makeSession({ extensions: [slow] });
	h.faux.setResponses([callSlow(), fauxAssistantMessage([fauxText("a")])]);
	const running = h.session.prompt("start");
	await new Promise((r) => setTimeout(r, 40));
	await assert.rejects(h.session.prompt("no behaviour given"));
	await running;
	h.dispose();
});

test("clearQueue() returns the queued text, which is how an interface restores it into the editor on Escape", async () => {
	const h = await makeSession({ extensions: [slow] });
	h.faux.setResponses([callSlow(), fauxAssistantMessage([fauxText("a")])]);
	const running = h.session.prompt("start");
	await new Promise((r) => setTimeout(r, 40));
	await h.session.steer("S1");
	await h.session.followUp("F1");
	const cleared = h.session.clearQueue();
	assert.deepEqual(cleared, { steering: ["S1"], followUp: ["F1"] });
	assert.equal(h.session.pendingMessageCount, 0);
	await running;
	h.dispose();
});

test("an extension command runs immediately even while the agent is streaming; steering one is refused", async () => {
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
	assert.equal(ranWhileStreaming, true, "ran during the run, not queued behind it");
	await assert.rejects(h.session.steer("/status"), /./, "an extension command is a UI action, not model input");
	await running;
	h.dispose();
});
