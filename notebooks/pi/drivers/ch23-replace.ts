// Chapter 23 - after a manual compaction, what does the next request contain,
// and what is still in the file?
//
// One real persisted session (the book's shared history), `keepRecentTokens`
// lowered so a short scripted conversation has something to summarise, and the
// provider's request read back. No compaction rule is re-implemented here: the
// extension under test only *supplies* a summary and keeps Pi's cut point.
//
// NB_KEEP sets keepRecentTokens (default 900) so the notebook's exercise can
// move the cut point without editing this file.

import { readFileSync } from "node:fs";
import { buildHistory, requestFor, userTexts } from "../harness/history.ts";
import customSummary from "../ch23-compaction/custom-summary.ts";

const KEEP = Number(process.env.NB_KEEP ?? 900);
const settings = { compaction: { enabled: false, keepRecentTokens: KEEP, reserveTokens: 1000 } };
const { h, file, entries, userEntry } = await buildHistory({ extensions: [customSummary], settings } as any);

const tally = () => {
	const all = entries();
	const by = (t: string) => all.filter((e) => e.type === t).length;
	return {
		entries: all.length,
		lines: readFileSync(file, "utf8").trim().split("\n").length,
		messages: by("message"),
		compactions: by("compaction"),
		questionAInFile: readFileSync(file, "utf8").includes("question A"),
	};
};

const before = tally();
let compacted: any = null;
let cutFailed = "";
try {
	await h.session.compact();
	compacted = entries().find((e) => e.type === "compaction");
} catch (e: any) {
	cutFailed = String(e.message).split("\n")[0];
}
const after = tally();

const sent = compacted ? await requestFor(h, "next question") : [];
const plain = userTexts(sent).filter((t) => !t.includes("Custom summary")); // the summary is itself user-role
const roles = sent.filter((m: any) => m.role !== "system").map((m: any) => m.role);
const toolCalls = sent.flatMap((m: any) => (m.role === "assistant" ? m.content.filter((b: any) => b.type === "toolCall") : [])).length;
const toolResults = sent.filter((m: any) => m.role === "toolResult").length;
const firstKept = compacted ? entries().find((e) => e.id === compacted.firstKeptEntryId) : null;

// The same entries, read from before the compaction instead of after it.
await h.session.navigateTree(compacted.parentId, { summarize: false });
const before2 = userTexts(await requestFor(h, "from before"));

console.log(
	JSON.stringify({
		keepRecentTokens: KEEP,
		cutFailed,
		before,
		after,
		compaction: compacted && {
			fromHook: compacted.fromHook,
			summaryIsTheExtensions: /^Custom summary of/.test(compacted.summary),
			hasFirstKeptEntryId: Boolean(compacted.firstKeptEntryId),
			firstKeptRole: firstKept?.message?.role ?? null,
			firstKeptIsToolResult: firstKept?.message?.role === "toolResult",
			tokensBeforeIsPositive: compacted.tokensBefore > 0,
		},
		sent: {
			roles,
			userTexts: plain.map((t) => t.slice(0, 40)),
			questionASent: plain.some((t) => t.includes("question A")),
			questionCSent: plain.some((t) => t.includes("question C")),
			summaryArrivedAsUserMessage: userTexts(sent).some((t) => t.includes("Custom summary")),
			toolCalls,
			toolResults,
			systemStillDeclaresBash: /bash/.test(JSON.stringify(sent.find((m: any) => m.role === "system") ?? {})),
		},
		navigatedBack: {
			questionASentAgain: before2.some((t) => t.includes("question A")),
			summarySent: before2.some((t) => t.includes("Custom summary")),
		},
		fileStillHasQuestionA: userEntry("question A") !== undefined,
	}),
);

h.dispose();