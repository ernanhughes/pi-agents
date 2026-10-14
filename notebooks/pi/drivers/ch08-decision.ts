// Chapter 8 part 2 - who decides, in what order, against the SHIPPED binary.
//
// Print mode has no UI to ask with, so a project extension is the observable: it
// writes a flag file when its factory runs. Every run is offline, in a fresh
// temporary working directory, with a fresh agent directory unless a saved
// decision is deliberately shared.

import { existsSync, mkdirSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import { ProjectTrustStore } from "@earendil-works/pi-coding-agent";
import { runPi } from "../harness/cli.ts";

const PROJECT_EXT = `
import { writeFileSync } from "node:fs";
export default function (pi: any) {
	writeFileSync(process.cwd() + "/project-ext-loaded.flag", "yes");
}
`;

const ext = (name: string) => fileURLToPath(new URL(`../../examples/harness/${name}.ts`, import.meta.url));

function attempt(o: {
	approve?: "yes" | "no" | "none";
	agentFiles?: Record<string, string>;
	extensions?: string[];
	cwd?: string;
	agentDir?: string;
}) {
	const cwd = o.cwd ?? mkdtempSync(join(tmpdir(), "pinb-ch08-cwd-"));
	const r = runPi({
		script: [{ text: "ok" }],
		args: ["--print", "hi"],
		cwd,
		agentDir: o.agentDir,
		approve: o.approve ?? "none",
		agentFiles: o.agentFiles,
		projectFiles: { ".pi/extensions/marker.ts": PROJECT_EXT },
		extraExtensions: o.extensions,
	});
	return { loaded: existsSync(join(cwd, "project-ext-loaded.flag")), exit: r.status };
}

function withSaved(decision: boolean | null) {
	const agentDir = mkdtempSync(join(tmpdir(), "pinb-ch08-agent-"));
	const cwd = mkdtempSync(join(tmpdir(), "pinb-ch08-saved-"));
	if (decision !== null) new ProjectTrustStore(agentDir).set(cwd, decision);
	return { agentDir, cwd };
}

const setting = (v: string) => ({ "settings.json": JSON.stringify({ defaultProjectTrust: v }) });

const rows: any[] = [
	{ who: "nothing at all", ...attempt({}) },
	{ who: "--approve", ...attempt({ approve: "yes" }) },
	{ who: "--no-approve", ...attempt({ approve: "no" }) },
	{ who: "defaultProjectTrust: always", ...attempt({ agentFiles: setting("always") }) },
	{ who: "defaultProjectTrust: ask", ...attempt({ agentFiles: setting("ask") }) },
	{ who: "defaultProjectTrust: never", ...attempt({ agentFiles: setting("never") }) },
	{ who: "saved yes", ...attempt(withSaved(true)) },
	{ who: "saved no", ...attempt(withSaved(false)) },
	{ who: "saved yes + defaultProjectTrust: never", ...attempt({ ...withSaved(true), agentFiles: setting("never") }) },
	{ who: "saved no + --approve", ...attempt({ ...withSaved(false), approve: "yes" }) },
	{ who: "extension says yes + saved no", ...attempt({ ...withSaved(false), extensions: [ext("trust-yes")] }) },
	{ who: "extension says no + saved yes", ...attempt({ ...withSaved(true), extensions: [ext("trust-no")] }) },
	{ who: "extension says undecided + saved yes", ...attempt({ ...withSaved(true), extensions: [ext("trust-undecided")] }) },
	{ who: "extension says yes + --no-approve", ...attempt({ ...withSaved(null), approve: "no", extensions: [ext("trust-yes")] }) },
];

console.log(JSON.stringify(rows));