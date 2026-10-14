// Chapter 2 part 2 - the working directory as identity key.
//
// Two scripted runs of the shipped binary, in two fresh working directories,
// sharing one fresh agent directory. Both persist their session, so the question
// the output answers is: do the two runs land in the same session group?

import { existsSync, mkdtempSync, readdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { runPi } from "../harness/cli.ts";

const agentDir = mkdtempSync(join(tmpdir(), "pinb-ch02-agent-"));
const sessionsRoot = join(agentDir, "sessions");

const groupNames = () =>
	existsSync(sessionsRoot)
		? readdirSync(sessionsRoot, { withFileTypes: true })
				.filter((e) => e.isDirectory())
				.map((e) => e.name)
		: [];

const runs = ["alpha", "beta"].map((label) => {
	const cwd = mkdtempSync(join(tmpdir(), `pinb-ch02-${label}-`));
	const r = runPi({
		script: [{ text: "ok from " + label }],
		args: ["--print", "hello"],
		cwd,
		agentDir,
		session: true,
	});
	return { label, cwdShape: label, exit: r.status, stdout: r.stdout.trim(), groupNames: groupNames() };
});

const sessionFiles = readdirSync(sessionsRoot, { withFileTypes: true }).flatMap((e) =>
	e.isDirectory() ? readdirSync(join(sessionsRoot, e.name)).map((f) => ({ group: e.name, file: f })) : [],
);

console.log(JSON.stringify({ runs, sessionFiles }));