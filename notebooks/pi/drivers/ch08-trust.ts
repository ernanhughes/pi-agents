// Chapter 8 part 1 - which project paths require a trust decision, and how a
// saved decision is inherited.
//
// `hasTrustRequiringProjectResources` and `ProjectTrustStore` are Pi's own. The
// filesystem fixtures are real temporary directories; nothing is read from the
// reader's own home directory.

import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { ProjectTrustStore, hasTrustRequiringProjectResources } from "@earendil-works/pi-coding-agent";

const TRIGGERS = [
	".pi/settings.json",
	".pi/mcp.json",
	".pi/extensions/example.ts",
	".pi/skills/example/SKILL.md",
	".pi/prompts/example.md",
	".pi/themes/example.json",
	".pi/SYSTEM.md",
	".pi/APPEND_SYSTEM.md",
	".agents/skills/example/SKILL.md",
	".pi/",
	"AGENTS.md",
];

function repoWith(relative: string) {
	const root = mkdtempSync(join(tmpdir(), "pinb-ch08-"));
	const target = join(root, relative);
	mkdirSync(target, { recursive: true });
	writeFileSync(join(target, "placeholder"), "x");
	return root;
}

const triggers = TRIGGERS.map((rel) => {
	const repo = repoWith(rel);
	return { path: rel, requiresDecision: hasTrustRequiringProjectResources(repo) };
});

// Context files are the documented exception, so build one deliberately.
const withContextFiles = (() => {
	const repo = mkdtempSync(join(tmpdir(), "pinb-ch08-ctx-"));
	writeFileSync(join(repo, "AGENTS.md"), "repo rules");
	writeFileSync(join(repo, "CLAUDE.md"), "claude rules");
	return { path: "AGENTS.md + CLAUDE.md only", requiresDecision: hasTrustRequiringProjectResources(repo) };
})();

// An ancestor trigger counts when you start below it.
const ancestor = (() => {
	const repo = mkdtempSync(join(tmpdir(), "pinb-ch08-anc-"));
	const deep = join(repo, "src", "billing");
	mkdirSync(join(deep, ".pi", "extensions"), { recursive: true });
	mkdirSync(join(repo, "docs"), { recursive: true }); // a sibling, which must not count
	writeFileSync(join(repo, "docs", "x"), "x");
	writeFileSync(join(deep, ".pi", "extensions", "e.ts"), "export default () => {};");
	return { path: "start below a trigger in an ancestor", requiresDecision: hasTrustRequiringProjectResources(deep) };
})();

// Saved decisions: nearest ancestor wins, and a child decision does not rewrite the parent.
const agentDir = mkdtempSync(join(tmpdir(), "pinb-ch08-agent-"));
const repo = mkdtempSync(join(tmpdir(), "pinb-ch08-saved-"));
const store = new ProjectTrustStore(agentDir);
const read = (dir: string) => store.get(dir);
const inheritance: any = { initial: read(repo) };
store.set(repo, true);
inheritance.afterParentYes = { repo: read(repo), child: read(join(repo, "src")) };
store.set(join(repo, "src"), false);
inheritance.afterChildNo = { repo: read(repo), child: read(join(repo, "src")) };
store.set(repo, null);
inheritance.afterCleared = { repo: read(repo) };

console.log(JSON.stringify({ triggers, withContextFiles, ancestor, inheritance }));