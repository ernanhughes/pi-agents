// Chapter 22, third part - scope and identity.
//
// Where the declaration lands (user settings, or the project's .pi), whether the
// project's package loads before the project is trusted, and whether two
// equivalent declarations load the package once or twice. SHIPPED binary, offline.

import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { runPi, runRaw } from "../harness/cli.ts";

function makePackage() {
	const root = mkdtempSync(join(tmpdir(), "pinb-ch22c-"));
	const pkg = join(root, "my-pkg");
	const agentDir = join(root, "agent");
	const cwd = join(root, "repo");
	for (const d of [join(pkg, "prompts"), join(pkg, "extensions"), agentDir, cwd]) mkdirSync(d, { recursive: true });
	writeFileSync(join(pkg, "package.json"), JSON.stringify({ name: "my-pkg", version: "1.0.0", keywords: ["pi-package"] }));
	writeFileSync(join(pkg, "prompts", "greet.md"), "---\ndescription: greet\n---\nHELLO-FROM-PACKAGE $1");
	writeFileSync(join(pkg, "extensions", "flag.ts"), 'import { appendFileSync } from "node:fs";\nexport default function (pi: any) { appendFileSync(process.cwd() + "/loaded.log", "x"); }\n');
	return { root, pkg, agentDir, cwd };
}

const loads = (cwd: string) => (existsSync(join(cwd, "loaded.log")) ? readFileSync(join(cwd, "loaded.log"), "utf8").length : 0);

/** Does the package's prompt template expand in one run? approve chooses whether the project is trusted. */
function run(p: ReturnType<typeof makePackage>, approve: "yes" | "no") {
	const r = runPi({ script: [{ text: "ok" }], args: ["--mode", "json", "/greet x"], cwd: p.cwd, agentDir: p.agentDir, approve });
	return /HELLO-FROM-PACKAGE/.test(r.stdout);
}

// --- --local: the declaration goes to the project, and trust gates it -------
const local = makePackage();
const installed = runRaw(["install", "--local", local.pkg], local);
const projectSettings = join(local.cwd, ".pi", "settings.json");
const projectEntry = existsSync(projectSettings) ? JSON.parse(readFileSync(projectSettings, "utf8")).packages?.[0] : null;
const userSettings = join(local.agentDir, "settings.json");
const trusted = { declined: run(local, "no"), approved: run(local, "yes") };

// --- identity: the same package written two equivalent ways loads once -------
const identity = makePackage();
writeFileSync(join(identity.agentDir, "settings.json"), JSON.stringify({ packages: [identity.pkg, { source: identity.pkg }] }));
const idRun = runPi({ script: [{ text: "ok" }], args: ["--mode", "json", "hi"], cwd: identity.cwd, agentDir: identity.agentDir });

console.log(
	JSON.stringify({
		local: {
			exit: installed.status,
			projectSettingsWritten: existsSync(projectSettings),
			projectEntry: projectEntry,
			userSettingsHasPackage: existsSync(userSettings) && /my-pkg/.test(readFileSync(userSettings, "utf8")),
			declinedLoads: trusted.declined,
			approvedLoads: trusted.approved,
		},
		identity: { entries: 2, extensionLoads: loads(identity.cwd), ranCleanly: idRun.status === 0 },
	}),
);