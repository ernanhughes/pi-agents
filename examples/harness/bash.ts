// A POSIX shell for the tests that run a real shell script.
//
// On Windows the `bash` on PATH is usually C:\WINDOWS\system32\bash.exe, which
// is the WSL *launcher*. With no distribution installed it exits non-zero and
// prints "execvpe(/bin/bash) failed", so a missing shell is indistinguishable
// from a failing script. Prefer Git Bash and MSYS, and fall back to whatever
// `bash` resolves to on a POSIX system.
import { existsSync } from "node:fs";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

function gitBash(): string | undefined {
	const roots = [process.env.ProgramFiles, process.env["ProgramFiles(x86)"], process.env.LOCALAPPDATA, "C:\\Program Files"];
	for (const root of roots) {
		if (!root) continue;
		for (const rel of ["Git\\bin\\bash.exe", "Git\\usr\\bin\\bash.exe", "Programs\\Git\\bin\\bash.exe"]) {
			const candidate = join(root, rel);
			if (existsSync(candidate)) return candidate;
		}
	}
	return undefined;
}

let cached: string | undefined;

/** The shell to spawn. Absolute path on Windows, bare `bash` elsewhere. */
export function bashPath(): string {
	if (cached) return cached;
	cached = (process.platform === "win32" ? gitBash() : undefined) ?? "bash";
	return cached;
}

/** True when a POSIX shell is actually usable, so a test can say so rather than fail obscurely. */
export function bashWorks(): boolean {
	const probe = spawnSync(bashPath(), ["-c", "exit 0"], { encoding: "utf8", timeout: 30_000 });
	return probe.status === 0;
}