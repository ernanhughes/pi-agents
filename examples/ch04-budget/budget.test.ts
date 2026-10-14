// Chapter 4 on the shared history: what is sent, and when the budget becomes a problem.
import { test } from "node:test";
import assert from "node:assert/strict";
import { fauxAssistantMessage, fauxText } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";
import { buildHistory, pad, requestFor, userTexts } from "../harness/history.ts";
import customSummary from "../ch23-compaction/custom-summary.ts";

const say = (t: string) => fauxAssistantMessage([fauxText(t)]);
const WINDOW = 100_000; // the faux model's contextWindow in the harness

const compactions = (h: Awaited<ReturnType<typeof makeSession>>) =>
	h.session.sessionManager.getEntries().filter((e: any) => e.type === "compaction") as any[];

/** Run N long turns, recording the context usage after each and whether a compaction has happened. */
async function grow(settings: Record<string, unknown>, turns = 6) {
	const h = await makeSession({ extensions: [customSummary], settings: { compaction: { enabled: true, keepRecentTokens: 600, ...(settings as any) } } });
	const log: { tokens: number; compactions: number }[] = [];
	for (let i = 0; i < turns; i++) {
		h.faux.setResponses([say(pad(`answer ${i}`))]);
		await h.session.prompt(`question ${i}`);
		log.push({ tokens: h.session.getContextUsage()?.tokens ?? 0, compactions: compactions(h).length });
	}
	return { h, log };
}

test("the footer's number is real: it is context usage over the window, and grows with the conversation", async () => {
	const { h, log } = await grow({ enabled: false, reserveTokens: 1000 }, 4);
	// The first reading includes the system prompt and tool declarations, so it is not comparable with
	// the next; from the second turn on, every answer makes the request larger.
	for (let i = 2; i < log.length; i++) assert.ok(log[i].tokens > log[i - 1].tokens, `turn ${i}`);
	const usage = h.session.getContextUsage()!;
	assert.equal(usage.contextWindow, WINDOW);
	assert.ok(Math.abs(usage.percent! - (usage.tokens! / WINDOW) * 100) < 0.01, "percent is tokens over the window");
	h.dispose();
});

test("the trigger is arithmetic: compaction happens when contextTokens exceeds contextWindow minus reserveTokens, and not before", async () => {
	const reserve = WINDOW - 3000; // so the threshold is 3000 tokens
	const threshold = WINDOW - reserve;
	const { h, log } = await grow({ reserveTokens: reserve }, 8);

	const first = log.findIndex((l) => l.compactions > 0);
	assert.ok(first > 0, "it did compact, but not on the first turn");
	assert.ok(log[first - 1].tokens <= threshold + 400, `the turn before it was at or below the threshold (${log[first - 1].tokens} vs ${threshold})`);
	const entry = compactions(h)[0];
	assert.ok(entry.tokensBefore > threshold, `the context it replaced (${entry.tokensBefore}) was over the threshold (${threshold})`);
	h.dispose();
});

test("a larger reserve compacts earlier: the same conversation, different settings, different turn", async () => {
	const early = await grow({ reserveTokens: WINDOW - 3500 }, 14);
	const late = await grow({ reserveTokens: WINDOW - 6000 }, 14);
	const turnOf = (r: typeof early) => r.log.findIndex((l) => l.compactions > 0);
	assert.ok(turnOf(early) >= 0 && turnOf(late) >= 0);
	assert.ok(turnOf(early) < turnOf(late));
	early.h.dispose();
	late.h.dispose();
});

test("a per-model override changes the threshold for that model, and the key is exact and case-sensitive", async () => {
	const overridden = await grow({ reserveTokens: 1000, modelOverrides: { "faux/faux-1": { reserveTokens: WINDOW - 2000 } } }, 6);
	assert.ok(overridden.log.some((l) => l.compactions > 0), "the override applied");
	const wrongCase = await grow({ reserveTokens: 1000, modelOverrides: { "Faux/Faux-1": { reserveTokens: WINDOW - 2000 } } }, 6);
	assert.ok(wrongCase.log.every((l) => l.compactions === 0), "a key with the wrong case did nothing");
	overridden.h.dispose();
	wrongCase.h.dispose();
});

test("enabled: false turns off automatic compaction, and the manual command still works", async () => {
	const { h, log } = await grow({ enabled: false, reserveTokens: WINDOW - 2000 }, 6);
	assert.ok(log.every((l) => l.compactions === 0));
	await h.session.compact();
	assert.equal(compactions(h).length, 1);
	h.dispose();
});

test("/compact accepts instructions, and an extension sees them", async () => {
	let seen: string | undefined;
	const spy = (pi: any) => pi.on("session_before_compact", async (e: any) => void (seen = e.customInstructions));
	const h = await makeSession({ extensions: [spy, customSummary], settings: { compaction: { enabled: false, keepRecentTokens: 600 } } });
	for (let i = 0; i < 4; i++) {
		h.faux.setResponses([say(pad(`a${i}`))]);
		await h.session.prompt(`q${i}`);
	}
	await h.session.compact("Preserve the failing test names.");
	assert.equal(seen, "Preserve the failing test names.");
	h.dispose();
});

test("the model sees the active branch, not the session file: leaving a branch removes it from the next request and not from the file", async () => {
	const { h, entries, userEntry } = await buildHistory();
	const before = entries().length;
	await h.session.navigateTree(userEntry("question B").id, { summarize: false });
	const sent = userTexts(await requestFor(h, "question B, again"));
	assert.ok(sent.some((t) => t.includes("question A")));
	assert.ok(!sent.some((t) => t.includes("question C")), "the abandoned branch is not sent");
	assert.ok(entries().some((e) => e.type === "message" && JSON.stringify(e.message.content).includes("question C")), "but it is still in the file");
	assert.ok(entries().length > before);
	h.dispose();
});

test("only active tools are declared to the model", async () => {
	const full = await makeSession({ extensions: [] });
	const narrow = await makeSession({ extensions: [], tools: ["read"] });
	const declared = async (h: Awaited<ReturnType<typeof makeSession>>) => {
		let names: string[] = [];
		h.faux.setResponses([(ctx: any) => ((names = (ctx.messages as any[]).flatMap((m) => (m.role === "system" ? (m.toolsAdded ?? []).map((t: any) => t.name) : []))), say("ok"))]);
		await h.session.prompt("go");
		return names;
	};
	assert.ok((await declared(full)).includes("bash"));
	assert.deepEqual(await declared(narrow), ["read"]);
	full.dispose();
	narrow.dispose();
});
