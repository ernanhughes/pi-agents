// Chapter 28: which context files exist, which are discovered, which are admitted.
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, basename } from "node:path";
import { DefaultResourceLoader } from "@earendil-works/pi-coding-agent";

// repo/AGENTS.md, repo/src/billing/AGENTS.override.md and AGENTS.md, a sibling repo/docs/AGENTS.md
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

test("discovered: the agent dir, the working directory and its parents; not siblings", async () => {
	const { billing, agentDir } = fixture();
	const loader = new DefaultResourceLoader({ cwd: billing, agentDir });
	await loader.reload();
	const got = names(loader.getAgentsFiles().agentsFiles);

	assert.ok(got.includes("AGENTS.md=user rules"), "the agent directory applies everywhere");
	assert.ok(got.includes("AGENTS.md=repo rules"), "a parent directory is inherited downward");
	assert.ok(!got.some((g) => g.includes("docs rules")), "a sibling directory is never discovered");
});

test("admitted: an override replaces the AGENTS.md beside it, and only that one", async () => {
	const { billing, agentDir } = fixture();
	const loader = new DefaultResourceLoader({ cwd: billing, agentDir });
	await loader.reload();
	const got = names(loader.getAgentsFiles().agentsFiles);

	assert.ok(got.includes("AGENTS.override.md=billing override"));
	assert.ok(!got.some((g) => g.includes("billing rules (replaced)")), "the sibling AGENTS.md is replaced");
	assert.ok(got.includes("AGENTS.md=repo rules"), "an override does not suppress other directories");
});

test("a host owns admission: it can drop or add files before they reach the model", async () => {
	const { billing, agentDir } = fixture();
	const loader = new DefaultResourceLoader({
		cwd: billing,
		agentDir,
		agentsFilesOverride: (current) => ({
			agentsFiles: [
				...current.agentsFiles.filter((f) => !f.content.includes("user rules")), // never admit the user's own file
				{ path: "/virtual/AGENTS.md", content: "policy supplied by the host" },
			],
		}),
	});
	await loader.reload();
	const got = names(loader.getAgentsFiles().agentsFiles);

	assert.ok(!got.some((g) => g.includes("user rules")));
	assert.ok(got.includes("AGENTS.md=policy supplied by the host"));
});
