// Chapter 32 - Headless Pi
// With a failed response, is the failure an exit status or only in the stream - and does --tools stop bash?
// Six shipped-binary runs: print vs JSON on the same failure; @path; --; piped stdin; --tools with the filesystem checked.

import { existsSync, mkdtempSync, readdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { runPi } from "../harness/cli.ts";

const events = (stdout: string) => stdout.trim().split("\n").filter(Boolean).map((l) => JSON.parse(l));
const workdir = () => mkdtempSync(join(tmpdir(), "pinb-ch32-"));
const userText = (stdout: string) => {
	const u = events(stdout).find((e) => e.type === "message_end" && e.message?.role === "user");
	return JSON.stringify(u?.message?.content ?? "");
};

// print mode, success and failure
const printOk = runPi({ script: [{ text: "the final answer" }], args: ["--print", "hi"], cwd: workdir() });
const printBad = runPi({ script: [{ error: "provider exploded" }], args: ["--print", "hi"], cwd: workdir() });

// JSON mode, same failure
const jsonBad = runPi({ script: [{ error: "provider exploded" }], args: ["--mode", "json", "hi"], cwd: workdir() });
const jsonBadFailed = events(jsonBad.stdout).find((e) => e.type === "message_end" && e.message?.role === "assistant");

// implicit print mode (redirected, no flag)
const implicit = runPi({ script: [{ text: "implicit" }], args: ["hi"], cwd: workdir() });

// piped stdin
const piped = runPi({ script: [{ text: "ok" }], args: ["--mode", "json", "Review this change"], stdin: "diff --git a/x b/x\n+added line\n", cwd: workdir() });

// @path
const atCwd = workdir();
writeFileSync(join(atCwd, "notes.md"), "MEETING-NOTES-MARKER");
const at = runPi({ script: [{ text: "ok" }], args: ["--mode", "json", "@notes.md", "summarise"], cwd: atCwd });

// -- dash
const dash = runPi({ script: [{ text: "ok" }], args: ["--mode", "json", "--", "-5 degrees is cold"], cwd: workdir() });

// --tools narrows
const toolsCwd = workdir();
const narrowed = runPi({ script: [{ tool: "bash", args: { command: "touch ran.flag" } }, { text: "done" }], args: ["--mode", "json", "--tools", "read,grep,find,ls", "go"], cwd: toolsCwd });
const narrowedResult = events(narrowed.stdout).find((e) => e.type === "tool_execution_end");

// default tools can run bash
const defaultCwd = workdir();
runPi({ script: [{ tool: "bash", args: { command: "touch ran.flag" } }, { text: "done" }], args: ["--print", "go"], cwd: defaultCwd });

// --no-session
const noSession = runPi({ script: [{ text: "x" }], args: ["--print", "hi"], cwd: workdir() });
const keptSession = runPi({ script: [{ text: "x" }], args: ["--print", "hi"], cwd: workdir(), session: true });
const sessionDir = join(keptSession.agentDir, "sessions");
const sessionFiles = existsSync(sessionDir) ? readdirSync(sessionDir, { recursive: true }).map(String).filter((f) => f.endsWith(".jsonl")) : [];

console.log(JSON.stringify({
	print: { okExit: printOk.status, okStdout: printOk.stdout, badExit: printBad.status, badStdoutEmpty: printBad.stdout === "", badStderrHasMessage: /provider exploded/.test(printBad.stderr) },
	json: { badExit: jsonBad.status, stopReason: jsonBadFailed?.message?.stopReason, errorMessage: jsonBadFailed?.message?.errorMessage },
	implicit: { exit: implicit.status, stdout: implicit.stdout },
	piped: { hasAddedLine: userText(piped.stdout).includes("added line"), addedBeforePrompt: userText(piped.stdout).indexOf("added line") < userText(piped.stdout).indexOf("Review this change") },
	atPath: { includesMarker: userText(at.stdout).includes("MEETING-NOTES-MARKER") },
	dash: { includesDashPrompt: userText(dash.stdout).includes("-5 degrees is cold") },
	narrowed: { isError: narrowedResult?.isError, ranFlagExists: existsSync(join(toolsCwd, "ran.flag")) },
	defaultTools: { ranFlagExists: existsSync(join(defaultCwd, "ran.flag")) },
	session: { noSessionDir: !existsSync(join(noSession.agentDir, "sessions")), keptSessionFiles: sessionFiles.length },
}));