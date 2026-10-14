import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, writeFileSync, chmodSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { spawnSync } from "node:child_process";
import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession, systemPromptSeenByProvider } from "../harness/session.ts";
import { bashPath, bashWorks } from "../harness/bash.ts";

// `PI_REVIEW_GUARD_ROOT` wins; otherwise the script asks Git for the top level of
// the working tree it was launched in. It never counts parents, because a project
// skill and a shared skill sit at different depths.
const RUN_CHECKS = `#!/usr/bin/env bash
# scripts/run-checks.sh - run the target repository's own verification.
set -euo pipefail

root="\${PI_REVIEW_GUARD_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$root"

echo "== repository: $root =="
echo "== typecheck =="
pnpm typecheck

echo "== unit tests =="
pnpm test:unit
`;

const SKILL = `---
name: review-guard
description: Reviews changed code against this repository's conventions and runs its own checks. Use when reviewing a diff.
---

# Review guard

1. Run \`scripts/run-checks.sh\` and read its output before reviewing anything.
2. Read \`references/checklist.md\`.
`;

const posix = (p: string) => p.split("\\").join("/");

/** A Git working tree with a fake pnpm on PATH that reports the directory it ran in. */
function repo(label: string) {
	const root = mkdtempSync(join(tmpdir(), `pi-${label}-`));
	const bin = join(root, "bin");
	mkdirSync(bin);
	writeFileSync(join(bin, "pnpm"), '#!/usr/bin/env bash\necho "pnpm $@ (cwd: $(pwd))"\n');
	chmodSync(join(bin, "pnpm"), 0o755);
	const init = spawnSync("git", ["init", "-q", root], { encoding: "utf8" });
	assert.equal(init.status, 0, `git init failed: ${init.stderr}`);
	return { root, bin };
}

/** How the shell itself spells a directory, so the assertion compares like with like. */
function shellPathOf(dir: string) {
	const r = spawnSync(bashPath(), ["-c", "pwd"], { cwd: dir, encoding: "utf8" });
	assert.equal(r.status, 0, r.stderr);
	return r.stdout.trim();
}

/** Install the script at `skillsDir`, run it from `cwd`, with `env` layered on top. */
function runScript(skillsDir: string, cwd: string, bin: string, env: Record<string, string> = {}) {
	const script = join(skillsDir, "review-guard", "scripts", "run-checks.sh");
	mkdirSync(dirname(script), { recursive: true });
	writeFileSync(script, RUN_CHECKS);
	chmodSync(script, 0o755);
	return spawnSync(bashPath(), [script], {
		cwd,
		encoding: "utf8",
		env: {
			...process.env,
			PATH: `${bin}${process.platform === "win32" ? ";" : ":"}${process.env.PATH}`,
			// Empty, not absent: `${VAR:-...}` falls through to discovery.
			PI_REVIEW_GUARD_ROOT: "",
			...env,
		},
	});
}

const needBash = { skip: bashWorks() ? false : "no POSIX shell (Git Bash or bash on PATH) is available" };

test("a project skill checks the repository it was launched in, not a directory it counted to", needBash, () => {
	// The layout chapter 8 and this chapter show: repo/.pi/skills/<name>/scripts/.
	// Three parents, not two, would be the wrong answer here — which is why the
	// script asks Git instead of counting.
	const { root, bin } = repo("skillfiles-project");
	const r = runScript(join(root, ".pi", "skills"), root, bin);
	assert.equal(r.status, 0, r.stderr);
	assert.match(r.stdout, /== typecheck ==/);
	assert.ok(
		r.stdout.includes(`cwd: ${shellPathOf(root)}`),
		`pnpm ran in ${shellPathOf(root)}; the skill directory is three levels deeper, so a parent count would have picked the wrong directory. stdout:\n${r.stdout}`,
	);
});

test("a shared or packaged skill outside the repository still resolves the target repository", needBash, () => {
	const { root, bin } = repo("skillfiles-shared");
	const agentDir = mkdtempSync(join(tmpdir(), "pi-skillfiles-agent-"));
	const r = runScript(join(agentDir, "skills"), root, bin);
	assert.equal(r.status, 0, r.stderr);
	assert.ok(
		r.stdout.includes(`cwd: ${shellPathOf(root)}`),
		`a skill at ${posix(agentDir)} cannot derive the repository from its own depth; it must ask Git. stdout:\n${r.stdout}`,
	);
});

test("PI_REVIEW_GUARD_ROOT overrides discovery, so one installed skill can serve several repositories", needBash, () => {
	const { root, bin } = repo("skillfiles-here");
	const other = repo("skillfiles-elsewhere");
	const r = runScript(join(root, ".pi", "skills"), root, bin, { PI_REVIEW_GUARD_ROOT: other.root });
	assert.equal(r.status, 0, r.stderr);
	assert.ok(r.stdout.includes(`cwd: ${shellPathOf(other.root)}`), `the override was ignored. stdout:\n${r.stdout}`);
});

// The chapter's claim is that skill frontmatter does NOT become environment
// variables. This pins it: a `compatibility:` line naming the variable must not
// change where the script runs, because nothing in Pi reads frontmatter into
// process.env. If a release ever adds that, this test fails and the chapter needs
// re-reading rather than quietly becoming true.
test("skill frontmatter does not become an environment variable", needBash, () => {
	const { root, bin } = repo("skillfiles-frontmatter");
	const decoy = repo("skillfiles-decoy");
	const skill = `---
name: review-guard
description: Reviews changed code and runs its own checks. Use when reviewing a diff.
compatibility: requires PI_REVIEW_GUARD_ROOT=${decoy.root.split("\\").join("/")}
metadata:
  PI_REVIEW_GUARD_ROOT: ${decoy.root.split("\\").join("/")}
allowed-tools: [bash]
---

1. Run \`scripts/run-checks.sh\` and read its output.
`;
	mkdirSync(join(root, ".pi", "skills", "review-guard"), { recursive: true });
	writeFileSync(join(root, ".pi", "skills", "review-guard", "SKILL.md"), skill);
	const r = runScript(join(root, ".pi", "skills"), root, bin);
	assert.equal(r.status, 0, r.stderr);
	assert.ok(
		r.stdout.includes(`cwd: ${shellPathOf(root)}`),
		`frontmatter named the decoy repository, and the script followed it. Nothing in Pi writes frontmatter into process.env, so it must fall through to discovery. stdout:\n${r.stdout}`,
	);
	assert.ok(!r.stdout.includes(shellPathOf(decoy.root)), "the frontmatter value must have no effect at all");
});

// The one place parent-relative resolution IS correct: a file that ships inside the
// skill directory moves with the skill, so its depth within the skill is constant.
test("a bundled config beside the script is found relative to the script", needBash, () => {
	const { root, bin } = repo("skillfiles-cwd");
	const other = repo("skillfiles-config-target");
	const skillsDir = join(root, ".pi", "skills");
	const script = join(skillsDir, "review-guard", "scripts", "run-checks.sh");
	mkdirSync(dirname(script), { recursive: true });
	writeFileSync(script, `#!/usr/bin/env bash
set -euo pipefail
config="$(dirname "$0")/../guard.conf"
[ -f "$config" ] && . "$config"
root="\${PI_REVIEW_GUARD_ROOT:-\${GUARD_ROOT:-$(git rev-parse --show-toplevel)}}"
cd "$root"
echo "== repository: $root =="
pnpm typecheck
`);
	chmodSync(script, 0o755);
	writeFileSync(join(skillsDir, "review-guard", "guard.conf"), `GUARD_ROOT="${other.root.split("\\").join("/")}"\n`);
	const elsewhere = mkdtempSync(join(tmpdir(), "pi-skillfiles-runfrom-"));
	const r = spawnSync(bashPath(), [script], {
		cwd: elsewhere,
		encoding: "utf8",
		env: { ...process.env, PATH: `${bin}${process.platform === "win32" ? ";" : ":"}${process.env.PATH}`, PI_REVIEW_GUARD_ROOT: "" },
	});
	assert.equal(r.status, 0, r.stderr);
	assert.ok(r.stdout.includes(`cwd: ${shellPathOf(other.root)}`), `the bundled config was not read. stdout:\n${r.stdout}`);
});

test("set -euo pipefail makes a check script fail loudly; without it the same failure exits zero", needBash, () => {
	const failing = (header: string) => `${header}\nfalse\necho "reached the end"\n`;
	const strict = spawnSync(bashPath(), ["-c", failing("set -euo pipefail")], { encoding: "utf8" });
	const lax = spawnSync(bashPath(), ["-c", failing("")], { encoding: "utf8" });
	assert.notEqual(strict.status, 0);
	assert.equal(lax.status, 0, "the model would have reported a clean review");
	assert.match(lax.stdout, /reached the end/);
});

test("the model is told where the skill lives, so a relative path in SKILL.md can be resolved", async () => {
	const h = await makeSession({
		extensions: [],
		agentFiles: {
			"skills/review-guard/SKILL.md": SKILL,
			"skills/review-guard/scripts/run-checks.sh": RUN_CHECKS,
			"skills/review-guard/references/checklist.md": "- item one",
		},
		resourceOptions: { noSkills: false },
	});
	const prompt = await systemPromptSeenByProvider(h);
	const m = prompt.match(/<location>([^<]*SKILL\.md)<\/location>|(\S*review-guard[\/]SKILL\.md)/);
	assert.ok(m, "the SKILL.md path appears in the prompt");
	const skillDir = dirname((m![1] ?? m![2]).trim());
	assert.match(skillDir.split("\\").join("/"), /skills\/review-guard$/);
	h.dispose();
});

test("a bundled file reaches the context only when the model reads it with its own tool", async () => {
	const h = await makeSession({
		extensions: [],
		agentFiles: { "skills/review-guard/SKILL.md": SKILL, "skills/review-guard/references/checklist.md": "CHECKLIST-ITEM-77" },
		resourceOptions: { noSkills: false },
	});
	assert.doesNotMatch(await systemPromptSeenByProvider(h), /CHECKLIST-ITEM-77/, "not in the prompt");

	const file = join(h.agentDir, "skills", "review-guard", "references", "checklist.md");
	h.faux.setResponses([fauxAssistantMessage([fauxToolCall("read", { path: file })], { stopReason: "toolUse" }), fauxAssistantMessage([fauxText("ok")])]);
	await h.session.prompt("review");
	const result = h.session.messages.find((m) => m.role === "toolResult") as any;
	assert.match(result.content[0].text, /CHECKLIST-ITEM-77/);
	h.dispose();
});


