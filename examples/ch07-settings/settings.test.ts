// Chapters 6 and 7: how settings merge, run through Pi's own SettingsManager over real files.
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { SettingsManager } from "@earendil-works/pi-coding-agent";

function files(user: object, project: object | null, trusted = true) {
	const root = mkdtempSync(join(tmpdir(), "pi-settings-"));
	const agentDir = join(root, "agent");
	const cwd = join(root, "repo");
	mkdirSync(agentDir, { recursive: true });
	mkdirSync(join(cwd, ".pi"), { recursive: true });
	writeFileSync(join(agentDir, "settings.json"), JSON.stringify(user));
	if (project) writeFileSync(join(cwd, ".pi", "settings.json"), JSON.stringify(project));
	return SettingsManager.create(cwd, agentDir, { projectTrusted: trusted } as any);
}

test("defaultTools: a project list of only +name and -name edits the user's selection", () => {
	const s = files({ defaultTools: ["read", "bash"] }, { defaultTools: ["+grep", "+find", "+ls"] });
	assert.deepEqual(s.getDefaultTools(), ["read", "bash", "grep", "find", "ls"]);
});

test("defaultTools: a project list containing a plain name replaces the selection outright", () => {
	const s = files({ defaultTools: ["read", "bash", "edit", "write"] }, { defaultTools: ["read", "powershell"] });
	assert.deepEqual(s.getDefaultTools(), ["read", "powershell"]);
});

test("defaultTools: within one list, plain names form the selection and +/- then apply in order", () => {
	const s = files({}, { defaultTools: ["read", "bash", "-bash", "+grep"] });
	assert.deepEqual(s.getDefaultTools(), ["read", "grep"]);
});

test("defaultTools: -name removes from the user's list", () => {
	const s = files({ defaultTools: ["read", "bash", "edit", "write"] }, { defaultTools: ["-bash"] });
	assert.deepEqual(s.getDefaultTools(), ["read", "edit", "write"]);
});

test("scalar settings: the project value wins over the user value", () => {
	const s = files({ compaction: { reserveTokens: 1000 } }, { compaction: { reserveTokens: 2000 } });
	assert.equal(s.getCompactionSettings().reserveTokens, 2000);
});

test("scalar settings: a nested key the project does not set still comes from the user file", () => {
	const s = files({ compaction: { reserveTokens: 1000, keepRecentTokens: 5000 } }, { compaction: { reserveTokens: 2000 } });
	assert.equal(s.getCompactionSettings().keepRecentTokens, 5000);
});

test("the SettingsManager getter returns one scope's list; the union happens when resources load (see union.test.ts)", () => {
	const s = files({ skills: ["~/shared-skills"] }, { skills: ["./local-skills"] });
	assert.deepEqual(s.getSkillPaths(), ["./local-skills"]);
});

test("untrusted project: its settings are not read at all", () => {
	const s = files({ compaction: { reserveTokens: 1000 } }, { compaction: { reserveTokens: 2000 } }, false);
	assert.equal(s.getCompactionSettings().reserveTokens, 1000);
});

test("trust can be granted later, and the project layer then applies", () => {
	const s = files({ compaction: { reserveTokens: 1000 } }, { compaction: { reserveTokens: 2000 } }, false);
	s.setProjectTrusted(true);
	assert.equal(s.getCompactionSettings().reserveTokens, 2000);
});

test("defaultProjectTrust is an agent-directory setting: a project file cannot set it", () => {
	const s = files({ defaultProjectTrust: "ask" }, { defaultProjectTrust: "always" });
	assert.equal(s.getDefaultProjectTrust(), "ask");
});
