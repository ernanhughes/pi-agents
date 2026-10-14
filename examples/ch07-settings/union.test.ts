import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { DefaultResourceLoader, SettingsManager } from "@earendil-works/pi-coding-agent";

const skill = (name: string) => `---\nname: ${name}\ndescription: ${name} skill\n---\n\n${name}\n`;

async function loadSkills(user: object, project: object, trusted: boolean) {
	const root = mkdtempSync(join(tmpdir(), "pi-union-"));
	const agentDir = join(root, "agent");
	const cwd = join(root, "repo");
	mkdirSync(join(agentDir, "shared", "user-skill"), { recursive: true });
	mkdirSync(join(cwd, ".pi", "local", "project-skill"), { recursive: true });
	writeFileSync(join(agentDir, "shared", "user-skill", "SKILL.md"), skill("user-skill"));
	writeFileSync(join(cwd, ".pi", "local", "project-skill", "SKILL.md"), skill("project-skill"));
	writeFileSync(join(agentDir, "settings.json"), JSON.stringify(user));
	writeFileSync(join(cwd, ".pi", "settings.json"), JSON.stringify(project));
	const settingsManager = SettingsManager.create(cwd, agentDir, { projectTrusted: trusted } as any);
	const loader = new DefaultResourceLoader({ cwd, agentDir, settingsManager, noContextFiles: true, noExtensions: true, noPromptTemplates: true, noThemes: true } as any);
	await loader.reload();
	// ~/.agents/skills on the machine running the tests is also discovered, so keep only ours.
	return loader.getSkills().skills.map((s: any) => s.name).filter((n: string) => n === "user-skill" || n === "project-skill").sort();
}

test("resource lists from the user and project files are both loaded", async () => {
	const names = await loadSkills({ skills: ["./shared"] }, { skills: ["./local"] }, true);
	assert.deepEqual(names, ["project-skill", "user-skill"]);
});

test("an untrusted project contributes nothing", async () => {
	const names = await loadSkills({ skills: ["./shared"] }, { skills: ["./local"] }, false);
	assert.deepEqual(names, ["user-skill"]);
});

test("omitting an entry in the project file removes nothing", async () => {
	assert.deepEqual(await loadSkills({ skills: ["./shared"] }, {}, true), ["user-skill"]);
	assert.deepEqual(await loadSkills({ skills: ["./shared"] }, { skills: ["./local"] }, true), ["project-skill", "user-skill"], "the user entry survives although the project list does not name it");
});

test("an exclusion filter works in the file that lists the resource", async () => {
	for (const filter of ["!**/user-skill/**", "!user-skill", "-./shared/user-skill"]) {
		const names = await loadSkills({ skills: ["./shared", filter] }, { skills: ["./local"] }, true);
		assert.deepEqual(names, ["project-skill"], `user file with ${filter}`);
	}
});

test("a project-file exclusion does not reach a user-level resource, observed on 1.0.4", async () => {
	for (const filter of ["!**/user-skill", "!user-skill", "!**/user-skill/**"]) {
		const names = await loadSkills({ skills: ["./shared"] }, { skills: ["./local", filter] }, true);
		assert.deepEqual(names, ["project-skill", "user-skill"], `project file with ${filter}`);
	}
});

test("a project-file exclusion does work on the project's own entries", async () => {
	const names = await loadSkills({ skills: ["./shared"] }, { skills: ["./local", "!**/project-skill/**"] }, true);
	assert.deepEqual(names, ["user-skill"]);
});
