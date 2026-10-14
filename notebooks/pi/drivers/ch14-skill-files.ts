// Chapter 14 - which repository a bundled script resolves, and what two lines of
// `set` change about its exit code.
//
// Two separate experiments, so two reports in one payload:
//
//   context  - Pi's own rules: the skill's path is in the provider's system
//              prompt, a bundled file is not, and it arrives only when the model
//              reads it with its own `read` tool.
//   shell    - the script the chapter prints, run against real temporary Git
//              repositories with a stand-in `pnpm` on PATH. Needs Git Bash; when
//              no POSIX shell is usable the report says so instead of guessing.

import { chmodSync, existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { spawnSync } from "node:child_process";
import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession, systemPromptSeenByProvider } from "../harness/session.ts";
import { bashPath, bashWorks } from "../harness/bash.ts";

// The chapter's scripts/run-checks.sh, verbatim in behaviour. It asks Git for the
// working tree it was launched in; it never counts parents from $0.
const RUN_CHECKS = `#!/usr/bin/env bash
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
description: Reviews changed code and runs its own checks. Use when reviewing a diff.
---

1. Run \`scripts/run-checks.sh\` and read its output.
2. Read \`references/checklist.md\`.
`;

const posix = (p: string) => p.split("\\").join("/");

// ---------------------------------------------------------------- context ---

async function context() {
	const h = await makeSession({
		extensions: [],
		agentFiles: {
			"skills/review-guard/SKILL.md": SKILL,
			"skills/review-guard/scripts/run-checks.sh": RUN_CHECKS,
			"skills/review-guard/references/checklist.md": "CHECKLIST-ITEM-77",
		},
		resourceOptions: { noSkills: false },
	});
	const prompt = await systemPromptSeenByProvider(h);
	const m = prompt.match(/<location>([^<]*SKILL\.md)<\/location>|(\S*review-guard[/\\]SKILL\.md)/);
	const skillDir = m ? dirname((m![1] ?? m![2]).trim()) : "";

	// The body names the bundled files by relative path; nothing about their
	// contents is in context yet.
	const before = h.session.messages.length;
	h.faux.setResponses([
		fauxAssistantMessage([fauxToolCall("read", { path: join(h.agentDir, "skills/review-guard/references/checklist.md") })], {
			stopReason: "toolUse",
		}),
		fauxAssistantMessage([fauxText("ok")]),
	]);
	await h.session.prompt("review");
	const result = h.session.messages.find((x) => x.role === "toolResult") as any;
	h.dispose();

	return {
		pathInPrompt: Boolean(m),
		skillDirSuffix: posix(skillDir).split("/").slice(-2).join("/"),
		namesScriptInBody: prompt.includes("run-checks.sh"),
		bodyMarkerInPrompt: prompt.includes("CHECKLIST-ITEM-77"),
		markerAfterRead: /CHECKLIST-ITEM-77/.test(result?.content?.[0]?.text ?? ""),
		toolResultsAfterRead: h.session.messages.filter((x) => x.role === "toolResult").length,
		messagesBeforeRead: before,
	};
}

// ------------------------------------------------------------------ shell ---

/** A Git working tree with a stand-in `pnpm` that reports the directory it ran in. */
function repo(label: string) {
	const root = mkdtempSync(join(tmpdir(), `nb-ch14-${label}-`));
	const bin = join(root, "bin");
	mkdirSync(bin);
	writeFileSync(join(bin, "pnpm"), '#!/usr/bin/env bash\necho "pnpm $@ (cwd: $(pwd))"\n');
	chmodSync(join(bin, "pnpm"), 0o755);
	const init = spawnSync("git", ["init", "-q", root], { encoding: "utf8" });
	return { root, bin, gitOk: init.status === 0 };
}

/** How the shell itself spells a directory, so comparisons are like for like. */
function shellPathOf(dir: string) {
	return spawnSync(bashPath(), ["-c", "pwd"], { cwd: dir, encoding: "utf8" }).stdout.trim();
}

function runScript(skillsDir: string, cwd: string, bin: string, env: Record<string, string> = {}) {
	const script = join(skillsDir, "review-guard", "scripts", "run-checks.sh");
	mkdirSync(dirname(script), { recursive: true });
	writeFileSync(script, RUN_CHECKS);
	chmodSync(script, 0o755);
	const r = spawnSync(bashPath(), [script], {
		cwd,
		encoding: "utf8",
		env: {
			...process.env,
			PATH: `${bin}${process.platform === "win32" ? ";" : ":"}${process.env.PATH}`,
			PI_REVIEW_GUARD_ROOT: "", // empty, not absent: ${VAR:-...} falls through
			...env,
		},
	});
	return { status: r.status, stdout: r.stdout ?? "" };
}

function shell() {
	if (!bashWorks()) return { available: false as const, reason: "no POSIX shell (Git Bash or bash on PATH) is usable" };

	const launched = repo("launched");
	const shared = mkdtempSync(join(tmpdir(), "nb-ch14-agent-"));
	const elsewhere = repo("elsewhere");

	// A project skill: the script is three levels below the repository root.
	const project = runScript(join(launched.root, ".pi", "skills"), launched.root, launched.bin);
	// The same script, installed outside every repository, launched in one.
	const outside = runScript(join(shared, "skills"), launched.root, launched.bin);
	// The override is a plain environment variable the operator exported.
	const override = runScript(join(launched.root, ".pi", "skills"), launched.root, launched.bin, {
		PI_REVIEW_GUARD_ROOT: elsewhere.root,
	});

	// `set -euo pipefail` against the same failing line, with and without it.
	const failing = (header: string) => `${header}\nfalse\necho "reached the end"\n`;
	const strict = spawnSync(bashPath(), ["-c", failing("set -euo pipefail")], { encoding: "utf8" });
	const lax = spawnSync(bashPath(), ["-c", failing("")], { encoding: "utf8" });

	// How far the script is from the repository it checks, counted from its own path.
	const depth = posix(join(launched.root, ".pi", "skills", "review-guard", "scripts", "run-checks.sh"))
		.split("/")
		.length - posix(launched.root).split("/").length - 1;

	return {
		available: true as const,
		gitAvailable: launched.gitOk,
		depthFromScriptToRepo: depth,
		project: {
			resolvedLaunchRepo: project.stdout.includes(`cwd: ${shellPathOf(launched.root)}`),
			status: project.status,
			ranBothSteps: project.stdout.includes("pnpm typecheck") && project.stdout.includes("pnpm test:unit"),
		},
		outside: {
			resolvedLaunchRepo: outside.stdout.includes(`cwd: ${shellPathOf(launched.root)}`),
			mentionsSkillDir: outside.stdout.includes(shellPathOf(shared)),
			status: outside.status,
		},
		override: { resolvedOtherRepo: override.stdout.includes(`cwd: ${shellPathOf(elsewhere.root)}`) },
		strictExit: strict.status,
		laxExit: lax.status,
		laxReachedEnd: /reached the end/.test(lax.stdout ?? ""),
		strictReachedEnd: /reached the end/.test(strict.stdout ?? ""),
	};
}

console.log(JSON.stringify({ context: await context(), shell: shell() }));