// Chapter 42: a field a tool fills in about itself. AgentTool.replay is declared in 1.0.2.
// This records two things about it: that a tool can set it, and that no shipped code reads it.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { Type } from "@earendil-works/pi-ai";
import type { AgentTool } from "@earendil-works/pi-agent-core";

const packages = fileURLToPath(new URL("../node_modules/@earendil-works/", import.meta.url));
const READS_REPLAY = /\.replay\b|\breplay\s*[:?]/;
const Params = Type.Object({ path: Type.String() });

// The tool chooses its own recovery policy. Nothing here checks that the choice is true.
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

test("a tool can declare replay about itself, and nothing in the declaration verifies it", () => {
	assert.equal(writeFile.replay, "safe");
});

test("the scan would notice a reader, so an empty result is not vacuous", () => {
	assert.ok(READS_REPLAY.test('if (tool.replay === "safe") retry();'));
	assert.ok(READS_REPLAY.test('const t = { replay: "never" };'));
});

test("1.0.4: no shipped JavaScript in the Pi packages reads a tool's replay field", () => {
	const readers: string[] = [];
	let scanned = 0;
	for (const pkg of ["pi-agent-core", "pi-coding-agent", "pi-mcp", "pi-codemode"]) {
		for (const file of jsFiles(join(packages, pkg, "dist"))) {
			scanned++;
			for (const [i, line] of readFileSync(file, "utf8").split("\n").entries()) {
				const code = line.trim();
				if (code.startsWith("//") || code.startsWith("*") || code.startsWith("/*")) continue;
				if (READS_REPLAY.test(code)) readers.push(`${file}:${i + 1}`);
			}
		}
	}
	assert.ok(scanned > 50, `scanned ${scanned} files`);
	// Version-sensitive on purpose: if a later release reads the field, this fails and chapter 42 must be re-read.
	assert.deepEqual(readers, []);
});
