// Chapter 30 - Debugging by Layer
// A DEMONSTRATION of the book's proposed "replace the layer below" method, on
// machinery that exists: the faux provider, the session harness, and the shipped
// binary. The layer list and the method are the book's formulation (proposed),
// not a procedure Pi documents.

import { Type, fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";

// A symptom: the model "keeps retrying". The cause could be the provider, the
// model, the loop, a gate, or a tool. We assign it by replacing a layer.
const throwingTool = (pi: any) =>
	pi.registerTool({
		name: "effect",
		label: "effect",
		description: "writes a file",
		parameters: Type.Object({}),
		async execute() {
			throw new Error("tool blew up");
		},
	});

const returningTool = (pi: any) =>
	pi.registerTool({
		name: "effect",
		label: "effect",
		description: "writes a file",
		parameters: Type.Object({}),
		async execute() {
			return { content: [{ type: "text", text: "wrote the file" }], details: undefined };
		},
	});

const call = () => fauxAssistantMessage([fauxToolCall("effect", {})], { stopReason: "toolUse" });
const done = () => fauxAssistantMessage([fauxText("done")]);

async function withTool(ext: any) {
	const h = await makeSession({ extensions: [ext] });
	h.faux.setResponses([call(), done()]);
	await h.session.prompt("do the thing");
	const r = h.session.messages.find((m) => m.role === "toolResult") as any;
	h.dispose();
	return { isError: r.isError, text: r.content?.[0]?.text ?? "" };
}

async function withGate() {
	const gate = (pi: any) => {
		returningTool(pi);
		pi.on("tool_call", async () => ({ block: true, reason: "gate refused" }));
	};
	const h = await makeSession({ extensions: [gate] });
	h.faux.setResponses([call(), done()]);
	await h.session.prompt("do the thing");
	const r = h.session.messages.find((m) => m.role === "toolResult") as any;
	h.dispose();
	return { isError: r.isError, text: r.content?.[0]?.text ?? "" };
}

// The interface layer: a command that works with a UI and not without one.
async function commandWithUI(hasUI: boolean) {
	const cmd = (pi: any) =>
		pi.registerCommand("act", {
			description: "act",
			handler: async (_args: any, ctx: any) => {
				if (ctx.hasUI) ctx.ui.notify("acted (with UI)", "info");
				// No UI: nothing to notify. In a real print run this is where a
				// console.log would go; suppressed here so the driver's JSON is clean.
			},
		});
	const { UiRecorder } = await import("../harness/session.ts");
	const ui = hasUI ? new UiRecorder() : undefined;
	const h = await makeSession({ extensions: [cmd], ...(ui ? { ui } : {}) });
	await h.session.prompt("/act");
	h.dispose();
	if (ui) return { notifications: ui.notifications.map((n) => n.message) };
	return { notifications: [] as string[] };
}

const [throwing, returning, gated, withUIResult, noUIResult] = await Promise.all([
	withTool(throwingTool),
	withTool(returningTool),
	withGate(),
	commandWithUI(true),
	commandWithUI(false),
]);

console.log(JSON.stringify({
	symptom: {
		throwingTool: throwing,
		returningTool: returning,
		gate: gated,
	},
	replaceProvider: {
		// The faux provider stands in for the real model, per chapter 41's vocabulary.
		symptomSurvivesWithScriptedProvider: throwing.isError && gated.isError,
		conclusion: "the symptom is in the tool or the gate, not the model",
	},
	replaceInterface: {
		withUI: withUIResult.notifications,
		noUI: noUIResult.notifications,
		symptomDisappears: withUIResult.notifications.length > 0 && noUIResult.notifications.length === 0,
	},
}));