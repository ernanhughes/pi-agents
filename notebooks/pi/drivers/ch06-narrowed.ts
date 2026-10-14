// Chapter 6 - does a narrowed agent actually refuse, and does the command run?
//
// Drives the SHIPPED pi binary three times, offline, each in a fresh temporary
// working directory. Reports the tool result AND whether the command left a file,
// because a failed tool result and a command that ran and failed look identical
// in a transcript and are different in the world.

import { existsSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { runPi } from "../harness/cli.ts";

function attempt(extra: string[]) {
	const cwd = mkdtempSync(join(tmpdir(), "pinb-ch06-"));
	const r = runPi({
		script: [{ tool: "bash", args: { command: "touch ran.flag" } }, { text: "done" }],
		args: ["--mode", "json", ...extra, "go"],
		cwd,
	});
	const recs = r.stdout
		.trim()
		.split("\n")
		.filter(Boolean)
		.map((l) => JSON.parse(l));
	const start = recs.find((x) => x.type === "tool_execution_start");
	const end = recs.find((x) => x.type === "tool_execution_end");
	const sys = recs.find((x) => x.type === "message_start");
	return {
		args: extra.join(" "),
		exit: r.status,
		toolAttempted: Boolean(start),
		toolName: start?.toolName ?? null,
		isError: end?.isError ?? null,
		declaredTools: sys?.message?.toolsAdded?.map((t: any) => t.name) ?? null,
		fileCreated: existsSync(join(cwd, "ran.flag")),
	};
}

console.log(
	JSON.stringify({
		default: attempt([]),
		narrowed: attempt(["--tools", "read,grep,find,ls"]),
		narrowedWithNoMcp: attempt(["--tools", "read,grep,find,ls", "--no-mcp"]),
	}),
);