// Chapter 8: what triggers the trust prompt, and how saved decisions resolve. Pi's own code, real directories.
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { hasTrustRequiringProjectResources, ProjectTrustStore } from "@earendil-works/pi-coding-agent";

const repo = () => {
	const root = mkdtempSync(join(tmpdir(), "pi-trust-"));
	mkdirSync(join(root, "repo", "src"), { recursive: true });
	return { root, repo: join(root, "repo") };
};
const put = (dir: string, rel: string, content = "x") => {
	mkdirSync(join(dir, rel, ".."), { recursive: true });
	writeFileSync(join(dir, rel), content);
};

test("a bare .pi directory does not need a decision", () => {
	const { repo: r } = repo();
	mkdirSync(join(r, ".pi"));
	assert.equal(hasTrustRequiringProjectResources(r), false);
});

test("each documented trigger asks for a decision", () => {
	const triggers = [
		".pi/settings.json",
		".pi/mcp.json",
		".pi/extensions/e.ts",
		".pi/skills/s/SKILL.md",
		".pi/prompts/p.md",
		".pi/themes/t.json",
		".pi/SYSTEM.md",
		".pi/APPEND_SYSTEM.md",
		".agents/skills/s/SKILL.md",
	];
	for (const t of triggers) {
		const { repo: r } = repo();
		put(r, t, "{}");
		assert.equal(hasTrustRequiringProjectResources(r), true, t);
	}
});

test("context files are NOT a trigger: they load regardless of trust", () => {
	const { repo: r } = repo();
	put(r, "AGENTS.md", "rules");
	put(r, "CLAUDE.md", "rules");
	assert.equal(hasTrustRequiringProjectResources(r), false);
});

test(".agents/skills in an ancestor directory counts when you start below it", () => {
	const { repo: r } = repo();
	put(r, ".agents/skills/s/SKILL.md", "x");
	assert.equal(hasTrustRequiringProjectResources(join(r, "src")), true);
});

test("saved decisions: the closest one applies, and a parent decision covers its children", () => {
	const { root, repo: r } = repo();
	const store = new ProjectTrustStore(join(root, "agent"));
	assert.equal(store.get(r), null, "nothing saved: undecided");
	store.set(root, true);
	assert.equal(store.get(join(r, "src")), true, "a parent decision propagates to children");
	store.set(r, false);
	assert.equal(store.get(join(r, "src")), false, "the closest decision wins");
	assert.equal(store.get(root), true, "and does not change the parent's");
});

test("decisions persist in trust.json in the agent directory", () => {
	const { root, repo: r } = repo();
	const agentDir = join(root, "agent");
	new ProjectTrustStore(agentDir).set(r, true);
	assert.ok(existsSync(join(agentDir, "trust.json")));
	assert.equal(new ProjectTrustStore(agentDir).get(r), true, "a new process reads it back");
	assert.match(readFileSync(join(agentDir, "trust.json"), "utf8"), /repo/);
});

test("a decision can be cleared by setting it to null", () => {
	const { root, repo: r } = repo();
	const store = new ProjectTrustStore(join(root, "agent"));
	store.set(r, true);
	store.set(r, null);
	assert.equal(store.get(r), null);
});

// ---- what trust gates, observed through the real resource loader ----
import { DefaultResourceLoader, SettingsManager } from "@earendil-works/pi-coding-agent";

async function load(trusted: boolean) {
	const { root, repo: r } = repo();
	const agentDir = join(root, "agent");
	mkdirSync(agentDir, { recursive: true });
	put(r, ".pi/extensions/project-ext.ts", "export default function (pi: any) {}\n");
	put(r, ".pi/prompts/mine.md", "---\ndescription: mine\n---\nMINE");
	put(r, ".pi/settings.json", "{}");
	put(r, "AGENTS.md", "PROJECT-RULES");
	const sm = SettingsManager.create(r, agentDir, { projectTrusted: trusted } as any);
	const loader = new DefaultResourceLoader({ cwd: r, agentDir, settingsManager: sm, noThemes: true, noSkills: true } as any);
	await loader.reload();
	return {
		extensions: loader.getExtensions().extensions.map((e: any) => String(e.path)).filter((p: string) => p.includes("project-ext")),
		prompts: loader.getPrompts().prompts.map((p: any) => p.name).filter((n: string) => n === "mine"),
		context: loader.getAgentsFiles().agentsFiles.map((f: any) => f.content).filter((c: string) => c.includes("PROJECT-RULES")),
	};
}

test("untrusted: the project's extension and prompt template do not load, but its AGENTS.md still does", async () => {
	const r = await load(false);
	assert.equal(r.extensions.length, 0);
	assert.equal(r.prompts.length, 0);
	assert.equal(r.context.length, 1, "instructions arrive whether or not you trust the folder");
});

test("trusted: the same project's extension and prompt template load", async () => {
	const r = await load(true);
	assert.equal(r.extensions.length, 1);
	assert.equal(r.prompts.length, 1);
	assert.equal(r.context.length, 1);
});
