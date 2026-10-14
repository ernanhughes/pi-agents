// Chapter 33 - The JSON Event Stream
// Is the framing really LF-only, and do all three reconstruction levels agree?
// One shipped-binary JSON run, parsed three ways: LF only, Unicode separators, and buffered-delta reconstruction.

import { runPi } from "../harness/cli.ts";

const LS = String.fromCharCode(0x2028);
const PS = String.fromCharCode(0x2029);
const run = (script: any[], extra: string[] = []) => runPi({ script, args: ["--mode", "json", ...extra, "go"] });
const parse = (stdout: string) => stdout.split("\n").filter(Boolean).map((l) => JSON.parse(l));

const hi = run([{ text: "hi" }]);
const unicode = run([{ text: `before${LS}after` }]);
const longAnswer = run([{ text: "a reasonably long answer for several deltas" }]);
const reconstruction = run([{ text: "the quick brown fox jumps" }]);
const tool = run([{ tool: "bash", args: { command: "echo hi" } }, { text: "done" }]);
const failed = run([{ error: "provider exploded" }]);

const hiRecs = parse(hi.stdout);
const [header] = hiRecs;

const unicodeRaw = unicode.stdout.split("\n").filter(Boolean);
const unicodeNaive = unicode.stdout.split(new RegExp("\r\n|\r|\n|" + LS + "|" + PS)).filter(Boolean);
const unicodeNaiveBroken = unicodeNaive.some((l) => { try { JSON.parse(l); return false; } catch { return true; } });

const longRecs = parse(longAnswer.stdout);
const updates = longRecs.filter((e: any) => e.type === "message_update");
const deltaOnly = updates.every((u: any) => !("message" in u) && !("partial" in u.assistantMessageEvent) && "usage" in u);

const reconRecs = parse(reconstruction.stdout);
const deltas = reconRecs.filter((e: any) => e.type === "message_update" && e.assistantMessageEvent.type === "text_delta").map((e: any) => e.assistantMessageEvent.delta).join("");
const textEnd = reconRecs.find((e: any) => e.type === "message_update" && e.assistantMessageEvent.type === "text_end");
const finalMessage = reconRecs.filter((e: any) => e.type === "message_end" && e.message.role === "assistant").at(-1);

const toolRecs = parse(tool.stdout);
const toolStart = toolRecs.find((e: any) => e.type === "tool_execution_start");
const toolEnd = toolRecs.find((e: any) => e.type === "tool_execution_end");
const turnEnd = toolRecs.find((e: any) => e.type === "turn_end");

const types = hiRecs.map((e: any) => e.type);
const failRecs = parse(failed.stdout);

console.log(JSON.stringify({
	header: { type: header?.type, version: header?.version, hasParentId: "parentId" in (header ?? {}) },
	framing: { lfTerminated: hi.stdout.endsWith("\n"), everyLineParses: hi.stdout.split("\n").filter(Boolean).every((l) => { try { JSON.parse(l); return true; } catch { return false; } }), stderrEmpty: hi.stderr === "" },
	unicode: { rawIncludesLS: unicode.stdout.includes(LS), lfRecords: unicodeRaw.length, naiveRecords: unicodeNaive.length, naiveBroken: unicodeNaiveBroken },
	lifecycle: { agentStartBeforeTurnStart: types.indexOf("agent_start") < types.indexOf("turn_start"), lastTwo: types.slice(-2) },
	deltaOnly: { updates: updates.length, deltaOnly },
	reconstruction: {
		deltas, textEndContent: textEnd?.assistantMessageEvent?.content ?? null,
		finalText: finalMessage?.message?.content?.find((b: any) => b.type === "text")?.text ?? null,
	},
	innerVocabulary: { kinds: [...new Set(updates.map((u: any) => u.assistantMessageEvent.type))], allHaveContentIndex: updates.every((u: any) => typeof u.assistantMessageEvent.contentIndex === "number") },
	tool: { name: toolStart?.toolName, args: toolStart?.args, sameCallId: toolEnd?.toolCallId === toolStart?.toolCallId, endIsError: toolEnd?.isError, resultHasHi: /hi/.test(JSON.stringify(toolEnd?.result ?? {})) },
	turnEnd: { messageRole: turnEnd?.message?.role, toolResults: turnEnd?.toolResults?.length },
	failedRun: { stopReason: failRecs.find((e: any) => e.type === "message_end" && e.message.role === "assistant")?.message?.stopReason, lastType: failRecs.at(-1)?.type },
	noExtensionError: { hasExtensionError: types.includes("extension_error") },
}));