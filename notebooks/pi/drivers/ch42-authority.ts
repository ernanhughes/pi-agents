// Chapter 42 - Authority, Isolation, and What Makes an Agent Worth Building
// Can a value chosen by the inspected party gate the inspection?
// The chapter's static scan for a reader of AgentTool.replay, with its anti-vacuity self-test.

import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { Type } from "@earendil-works/pi-ai";
import type { AgentTool } from "@earendil-works/pi-agent-core";

const packages = fileURLToPath(new URL("../node_modules/@earendil-works/", import.meta.url));
const READS_REPLAY = /\.replay\b|\breplay\s*[:?]/;
const Params = Type.Object({ path: Type.String() });

const writeFile: AgentTool<typeof Params> = {
	name: "write_file",
	label: "write_file",
	description: "write a file",
	parameters: Params,
	replay: "safe", // a claim by the inspected party
	async execute() {
		return { content: [{ type: "text", text: "ok" }], details: undefined };
	},
};

function jsFiles(dir: string): string[] {
	return readdirSync(dir).flatMap((name) => {
		const path = join(dir, name);
		if (statSync(path).isDirectory()) return name === "node_modules" ? [] : jsFiles(path);
		return path.endsWith(".js") ? [path] : [];
	});
}

const toolCanDeclare = writeFile.replay === "safe";

// The anti-vacuity self-test: the scan would notice a reader.
const antiVacuity = {
	seesDirectComparison: READS_REPLAY.test('if (tool.replay === "safe") retry();'),
	seesObjectLiteral: READS_REPLAY.test('const t = { replay: "never" };'),
};

const readers: string[] = [];
let scanned = 0;
for (const pkg of ["pi-agent-core", "pi-coding-agent", "pi-mcp", "pi-codemode"]) {
	for (const file of jsFiles(join(packages, pkg, "dist"))) {
		scanned++;
		for (const [i, line] of readFileSync(file, "utf8").split("\n").entries()) {
			const code = line.trim();
			if (code.startsWith("//") || code.startsWith("*") || code.startsWith("/*")) continue;
			if (READS_REPLAY.test(code)) readers.push(`${pkg}/${file.split(/[\\/]/).pop()}:${i + 1}`);
		}
	}
}

console.log(JSON.stringify({
	toolCanDeclare,
	antiVacuity,
	scanned,
	readers: readers.slice(0, 10),
	noReaders: readers.length === 0 && scanned > 50,
}));