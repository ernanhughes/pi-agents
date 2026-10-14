// Chapter 10 part 1 - what actually reaches the first prompt.
//
// Three documented mechanics, run against the SHIPPED binary: @path attachment, the
// `--` option terminator, and piped stdin. All offline, each in a fresh temporary
// working directory.

import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { runPi } from "../harness/cli.ts";

const NOTES = "MEETING-NOTES-MARKER\n- ship the notebook";

function attempt(opts: { args: string[]; stdin?: string; files?: Record<string, string> }) {
	const cwd = mkdtempSync(join(tmpdir(), "pinb-ch10-"));
	for (const [rel, content] of Object.entries(opts.files ?? {})) {
		writeFileSync(join(cwd, rel), content);
	}
	const r = runPi({ script: [{ text: "ok" }], args: ["--mode", "json", ...opts.args], cwd, stdin: opts.stdin });
	const recs = r.stdout
		.trim()
		.split("\n")
		.filter(Boolean)
		.map((l) => JSON.parse(l));
	const user = recs.find((x) => x.type === "message_end" && x.message?.role === "user");
	const text = [...(user?.message?.content ?? [])].map((b: any) => b.text ?? b).join("\n");
	return { exit: r.status, userText: text, stderr: r.stderr.trim() };
}

console.log(
	JSON.stringify({
		plain: attempt({ args: ["go"] }),
		attached: attempt({ args: ["@notes.md", "summarise"], files: { "notes.md": NOTES } }),
		optionTerminator: attempt({ args: ["--", "-5 degrees is cold"] }),
		pipedStdin: attempt({ args: ["go"], stdin: "PIPED-MARKER line\n" }),
	}),
);