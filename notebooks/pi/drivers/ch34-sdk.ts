// Chapter 34 - SDK Sessions
// Does assigning agent.state.messages change what the provider receives?
// Real AgentSession: the forged assignment, then a captured outgoing context; steer/followUp/prompt without a behaviour; SessionManager.getSessionFile(); dispose() stopping delivery.

import { fauxAssistantMessage, fauxText } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";

const say = (t: string) => fauxAssistantMessage([fauxText(t)]);

async function streaming() {
	const h = await makeSession({ extensions: [] });
	h.faux.setResponses([say("the repository has three packages")]);
	const deltas: string[] = [];
	const off = h.session.subscribe((event: any) => {
		if (event.type === "message_update" && event.assistantMessageEvent.type === "text_delta") deltas.push(event.assistantMessageEvent.delta);
	});
	try { await h.session.prompt("Explain this repository"); } finally { off(); }
	const joined = deltas.join("");
	const last = h.session.getLastAssistantText();
	h.dispose();
	return { deltas: deltas.length, joined, last };
}

async function streamingBehaviour() {
	const h = await makeSession({ extensions: [], fauxOptions: { tokensPerSecond: 20 } });
	h.faux.setResponses([say("a fairly long answer that takes a little while to stream out"), say("second"), say("third")]);
	const running = h.session.prompt("first");
	await new Promise((r) => setTimeout(r, 30));
	const wasStreaming = h.session.isStreaming;
	let rejected = false;
	try { await h.session.prompt("second, no behaviour given"); } catch { rejected = true; }
	const steered = await h.session.steer("change direction");
	const followed = await h.session.followUp("then also this");
	await running;
	await h.session.waitForIdle();
	h.dispose();
	return { wasStreaming, rejected, steered, followed };
}

async function sessionManagerAuthoritative() {
	const h = await makeSession({ extensions: [] });
	h.faux.setResponses([say("one")]);
	await h.session.prompt("first question");
	h.session.agent.state.messages = [{ role: "user", content: "FORGED HISTORY", timestamp: Date.now() } as any];
	let sent = "";
	h.faux.setResponses([(ctx: any) => ((sent = JSON.stringify(ctx.messages)), say("two"))]);
	await h.session.prompt("second question");
	h.dispose();
	return { sentHasForged: /FORGED HISTORY/.test(sent), sentHasReal: /first question/.test(sent) };
}

async function inMemoryNoFile() {
	const h = await makeSession({ extensions: [] });
	const file = h.session.sessionManager.getSessionFile();
	h.dispose();
	return { file };
}

async function disposeStops() {
	const h = await makeSession({ extensions: [] });
	let events = 0;
	h.session.subscribe(() => void events++);
	h.dispose();
	const before = events;
	h.faux.setResponses([say("x")]);
	await h.session.prompt("after dispose").catch(() => {});
	const after = events;
	return { before, after };
}

const [str, behaviour, authoritative, noFile, disposed] = await Promise.all([
	streaming(),
	streamingBehaviour(),
	sessionManagerAuthoritative(),
	inMemoryNoFile(),
	disposeStops(),
]);

console.log(JSON.stringify({
	streaming: str,
	streamingBehaviour: behaviour,
	authoritative,
	inMemory: { fileUndefined: noFile.file === undefined },
	dispose: { eventsBefore: disposed.before, eventsAfter: disposed.after, stopped: disposed.before === disposed.after },
}));