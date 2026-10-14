import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

test("chapter 1: the agent core runs with no provider and no terminal", () => {
	const script = fileURLToPath(new URL("./agent-core.ts", import.meta.url));
	const r = spawnSync(process.execPath, [script], { encoding: "utf8" });
	assert.equal(r.status, 0, r.stderr);
	assert.equal(r.stdout.trim(), 'stop: toolUse\ntool: word_count {"words":4}\nstop: stop');
});
