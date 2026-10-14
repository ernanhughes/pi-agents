// Chapter 23 on the shared history: what compaction replaces, and what survives it.
import { test } from "node:test";
import assert from "node:assert/strict";
import { Type, fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";
import { buildHistory, pad, requestFor, userTexts } from "../harness/history.ts";
import customSummary from "./custom-summary.ts";

const say = (t: string) => fauxAssistantMessage([fauxText(t)]);

/** An extension that records the preparation Pi hands to session_before_compact, then lets customSummary answer. */
function capture() {
	const seen: any[] = [];
	const ext = (pi: any) => pi.on("session_before_compact", async (e: any) => void seen.push(e.preparation));
	return { seen, ext };
}

const settings = (keepRecentTokens: number) => ({ compaction: { enabled: false, keepRecentTokens, reserveTokens: 1000 } });

test("the cut point is never a tool result, whatever keepRecentTokens is", async () => {
	for (const keep of [50, 150, 300, 600, 900, 1500, 2500]) {
		const h = await buildHistory({ extensions: [customSummary], settings: settings(keep) } as any);
		try {
			await h.h.session.compact();
		} catch {
			h.h.dispose();
			continue; // too small a session for this budget
		}
		const compaction = h.entries().find((e) => e.type === "compaction");
		const firstKept = h.entries().find((e) => e.id === compaction.firstKeptEntryId);
		assert.notEqual(firstKept.message?.role, "toolResult", `keepRecentTokens ${keep}: the kept range must not begin with a tool result`);
		h.h.dispose();
	}
});

test("the result stays with its call: when the cut falls inside the tool exchange, both sides are on the same side", async () => {
	for (const keep of [50, 150, 300, 600, 900, 1500]) {
		const { h, entries } = await buildHistory({ extensions: [customSummary], settings: settings(keep) } as any);
		try { await h.session.compact(); } catch { h.dispose(); continue; }
		const compaction = entries().find((e) => e.type === "compaction");
		const sent = await requestFor(h, "next");
		const toolResults = sent.filter((m: any) => m.role === "toolResult").length;
		const toolCalls = sent.flatMap((m: any) => (m.role === "assistant" ? m.content.filter((b: any) => b.type === "toolCall") : [])).length;
		assert.equal(toolResults, toolCalls, `keepRecentTokens ${keep}: no tool call without its result, and no result without its call`);
		assert.ok(compaction);
		h.dispose();
	}
});

test("compaction is iterative: the second summary is given the first as previousSummary", async () => {
	const c = capture();
	const h = await makeSession({ extensions: [c.ext, customSummary], settings: settings(500) });
	const grow = async (n: number, tag: string) => {
		for (let i = 0; i < n; i++) {
			h.faux.setResponses([say(pad(`${tag}${i}`))]);
			await h.session.prompt(`${tag}-question ${i}`);
		}
	};
	await grow(4, "a");
	await h.session.compact();
	await grow(4, "b");
	await h.session.compact();

	assert.equal(c.seen.length, 2);
	assert.ok(!c.seen[0].previousSummary, "the first compaction has nothing to build on");
	assert.match(c.seen[1].previousSummary, /^Custom summary of/, "the second receives the first's summary");
	h.dispose();
});

test("file operations are extracted for the extension: what was read and what was modified", async () => {
	const c = capture();
	const h = await makeSession({ extensions: [c.ext, customSummary], settings: settings(300) });
	h.faux.setResponses([fauxAssistantMessage([fauxToolCall("write", { path: "out/report.md", content: "x" })], { stopReason: "toolUse" }), say(pad("done writing"))]);
	await h.session.prompt("write a report");
	h.faux.setResponses([fauxAssistantMessage([fauxToolCall("read", { path: "package.json" })], { stopReason: "toolUse" }), say(pad("done reading"))]);
	await h.session.prompt("read the manifest");
	for (let i = 0; i < 3; i++) {
		h.faux.setResponses([say(pad(`filler ${i}`))]);
		await h.session.prompt(`filler ${i}`);
	}
	await h.session.compact();
	// fileOps holds three Sets: read, written and edited.
	const ops = c.seen[0].fileOps;
	assert.deepEqual([...ops.read].filter((f: string) => f.includes("package.json")), ["package.json"], "a file the model read");
	assert.deepEqual([...ops.written], ["out/report.md"], "a file it wrote");
	assert.equal(ops.edited.size, 0, "and none it edited");
	h.dispose();
});

test("a single long span splits: when one user message's turns exceed keepRecentTokens, the cut lands inside it", async () => {
	const c = capture();
	const pause = (pi: any) => pi.registerTool({ name: "noop", label: "noop", description: "n", parameters: Type.Object({}), async execute() { return { content: [{ type: "text", text: pad("tool output", 30) }], details: undefined }; } });
	const h = await makeSession({ extensions: [pause, c.ext, customSummary], settings: settings(400) });
	h.faux.setResponses([
		...Array.from({ length: 6 }, () => fauxAssistantMessage([fauxToolCall("noop", {})], { stopReason: "toolUse" })),
		say("finished the long task"),
	]);
	await h.session.prompt("one long task");
	await h.session.compact();

	const prep = c.seen[0];
	console.log("split turn:", prep.isSplitTurn, "| messagesToSummarize:", prep.messagesToSummarize.length, "| turnPrefixMessages:", prep.turnPrefixMessages?.length);
	assert.equal(prep.isSplitTurn, true);
	assert.ok(prep.turnPrefixMessages.length > 0, "the early part of the span is the prefix");
	h.dispose();
});

test("compaction does not shrink the system prompt or the tool declarations", async () => {
	const { h } = await buildHistory({ extensions: [customSummary], settings: settings(300) } as any);
	await h.session.compact();
	const sent = await requestFor(h, "after");
	const system = sent.find((m: any) => m.role === "system");
	assert.ok(system, "a system message is still sent");
	const full = JSON.stringify(system);
	assert.match(full, /bash/, "the tool declarations are still there");
	h.dispose();
});

test("compaction replaces what the model reads and nothing in the file: navigating to before the compaction sends the originals again", async () => {
	const { h, entries, userEntry } = await buildHistory({ extensions: [customSummary], settings: settings(300) } as any);
	await h.session.compact();
	const compaction = entries().find((e) => e.type === "compaction");

	// The summary arrives as a user-role message and (in this test) quotes what it replaced, so set it aside.
	const real = (texts: string[]) => texts.filter((t) => !t.includes("Custom summary"));
	let sent = userTexts(await requestFor(h, "while compacted"));
	assert.ok(!real(sent).some((t) => t.includes("question A")), "the oldest question is summarised away");
	assert.ok(sent.some((t) => t.includes("Custom summary")));

	// The entry just before the compaction entry is the last one on the branch it summarised.
	await h.session.navigateTree(compaction.parentId, { summarize: false });
	sent = userTexts(await requestFor(h, "from before the compaction"));
	assert.ok(real(sent).some((t) => t.includes("question A")), "the original messages are sent again");
	assert.ok(!sent.some((t) => t.includes("Custom summary")), "and the summary is not");
	assert.ok(userEntry("question A"), "and they were in the file all along");
	h.dispose();
});

test("an extension that cancels leaves the history exactly as it was", async () => {
	const cancel = (pi: any) => pi.on("session_before_compact", async () => ({ cancel: true }));
	const { h, entries } = await buildHistory({ extensions: [cancel], settings: settings(300) } as any);
	const before = entries().length;
	await assert.rejects(h.session.compact());
	assert.equal(entries().length, before);
	assert.ok(!entries().some((e) => e.type === "compaction"));
	h.dispose();
});
