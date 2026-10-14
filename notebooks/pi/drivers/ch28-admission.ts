// Chapter 28 - Context Admission Is Application Policy
// Starting in repo/src/billing, which AGENTS.md files are discovered and admitted - and does an override reach outside its directory?
// DefaultResourceLoader built directly over a real fixture tree; the admitted list; the override's locality; a host that drops and adds.

import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, basename } from "node:path";
import { DefaultResourceLoader } from "@earendil-works/pi-coding-agent";

function fixture() {
	const root = mkdtempSync(join(tmpdir(), "pi-admission-"));
	const repo = join(root, "repo");
	const billing = join(repo, "src", "billing");
	const docs = join(repo, "docs");
	const agentDir = join(root, "agent");
	for (const d of [billing, docs, agentDir]) mkdirSync(d, { recursive: true });
	writeFileSync(join(repo, "AGENTS.md"), "repo rules");
	writeFileSync(join(billing, "AGENTS.md"), "billing rules (replaced)");
	writeFileSync(join(billing, "AGENTS.override.md"), "billing override");
	writeFileSync(join(docs, "AGENTS.md"), "docs rules");
	writeFileSync(join(agentDir, "AGENTS.md"), "user rules");
	return { repo, billing, docs, agentDir };
}

const names = (files: { path: string; content: string }[]) => files.map((f) => `${basename(f.path)}=${f.content}`);

async function discovered() {
	const { billing, agentDir } = fixture();
	const loader = new DefaultResourceLoader({ cwd: billing, agentDir });
	await loader.reload();
	return names(loader.getAgentsFiles().agentsFiles);
}

async function overrideLocality() {
	const { billing, agentDir } = fixture();
	const loader = new DefaultResourceLoader({ cwd: billing, agentDir });
	await loader.reload();
	return names(loader.getAgentsFiles().agentsFiles);
}

async function hostAdmission() {
	const { billing, agentDir } = fixture();
	const loader = new DefaultResourceLoader({
		cwd: billing,
		agentDir,
		agentsFilesOverride: (current: any) => ({
			agentsFiles: [
				...current.agentsFiles.filter((f: any) => !f.content.includes("user rules")),
				{ path: "/virtual/AGENTS.md", content: "policy supplied by the host" },
			],
		}),
	} as any);
	await loader.reload();
	return names(loader.getAgentsFiles().agentsFiles);
}

const [discoveredList, overrideList, hostList] = await Promise.all([discovered(), overrideLocality(), hostAdmission()]);

console.log(JSON.stringify({
	discovered: {
		list: discoveredList,
		includesUser: discoveredList.some((g) => g.includes("user rules")),
		includesRepo: discoveredList.some((g) => g.includes("repo rules")),
		includesDocsSibling: discoveredList.some((g) => g.includes("docs rules")),
	},
	override: {
		list: overrideList,
		hasOverride: overrideList.some((g) => g.includes("billing override")),
		hasReplaced: overrideList.some((g) => g.includes("billing rules (replaced)")),
		hasRepoStill: overrideList.some((g) => g.includes("repo rules")),
	},
	host: {
		list: hostList,
		hasUserRules: hostList.some((g) => g.includes("user rules")),
		hasVirtual: hostList.some((g) => g.includes("policy supplied by the host")),
	},
}));