// Chapter 8's decision order, against the SHIPPED pi binary in print mode (no UI to ask with).
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { ProjectTrustStore } from "@earendil-works/pi-coding-agent";
import { runPi } from "../harness/cli.ts";

// A project extension that proves it loaded by writing a flag file when its factory runs.
const PROJECT_EXT = `
import { writeFileSync } from "node:fs";
export default function (pi: any) {
	writeFileSync(process.cwd() + "/project-ext-loaded.flag", "yes");
}
`;

function attempt(opts: { args?: string[]; approve?: "yes" | "no" | "none"; agentFiles?: Record<string, string>; extensions?: string[]; cwd?: string }) {
	const cwd = opts.cwd ?? mkdtempSync(join(tmpdir(), "pi-trust-cwd-"));
	const r = runPi({
		script: [{ text: "ok" }],
		args: ["--print", "hi", ...(opts.args ?? [])],
		cwd,
		approve: opts.approve ?? "none",
		agentFiles: opts.agentFiles,
		projectFiles: { ".pi/extensions/marker.ts": PROJECT_EXT },
		extraExtensions: opts.extensions,
	});
	return { loaded: existsSync(join(cwd, "project-ext-loaded.flag")), r, cwd };
}

test("with no override, extension or saved decision, print mode cannot ask and the default is ask: the project extension does not load", () => {
	assert.equal(attempt({}).loaded, false);
});

test("--approve and --no-approve decide first", () => {
	assert.equal(attempt({ approve: "yes" }).loaded, true);
	assert.equal(attempt({ approve: "no" }).loaded, false);
});

test("defaultProjectTrust: always loads protected project resources, while ask and never skip them", () => {
	const setting = (v: string) => ({ "settings.json": JSON.stringify({ defaultProjectTrust: v }) });
	assert.equal(attempt({ agentFiles: setting("always") }).loaded, true);
	assert.equal(attempt({ agentFiles: setting("ask") }).loaded, false);
	assert.equal(attempt({ agentFiles: setting("never") }).loaded, false);
});

const ext = (name: string) => fileURLToPath(new URL(`../harness/${name}.ts`, import.meta.url));

function withSaved(decision: boolean | null) {
	const agentDir = mkdtempSync(join(tmpdir(), "pi-trust-agent-"));
	const cwd = mkdtempSync(join(tmpdir(), "pi-trust-saved-"));
	if (decision !== null) new ProjectTrustStore(agentDir).set(cwd, decision);
	return { agentDir, cwd };
}

function run(o: { agentDir: string; cwd: string; approve?: "yes" | "no" | "none"; extensions?: string[]; setting?: string }) {
	if (o.setting) mkdirSync(o.agentDir, { recursive: true });
	const r = runPi({
		script: [{ text: "ok" }], args: ["--print", "hi"], cwd: o.cwd, agentDir: o.agentDir, approve: o.approve ?? "none",
		agentFiles: o.setting ? { "settings.json": JSON.stringify({ defaultProjectTrust: o.setting }) } : undefined,
		projectFiles: { ".pi/extensions/marker.ts": PROJECT_EXT }, extraExtensions: o.extensions,
	});
	return existsSync(join(o.cwd, "project-ext-loaded.flag"));
}

test("a saved decision for the directory applies without any flag", () => {
	assert.equal(run(withSaved(true)), true);
	assert.equal(run(withSaved(false)), false);
});

test("a saved decision beats defaultProjectTrust", () => {
	assert.equal(run({ ...withSaved(true), setting: "never" }), true);
	assert.equal(run({ ...withSaved(false), setting: "always" }), false);
});

test("a command-line flag beats a saved decision", () => {
	assert.equal(run({ ...withSaved(false), approve: "yes" }), true);
	assert.equal(run({ ...withSaved(true), approve: "no" }), false);
});

test("a project_trust handler in a command-line extension decides before saved decisions and the default", () => {
	assert.equal(run({ ...withSaved(false), extensions: [ext("trust-yes")] }), true, "yes beats a saved no");
	assert.equal(run({ ...withSaved(true), extensions: [ext("trust-no")] }), false, "no beats a saved yes");
	assert.equal(run({ ...withSaved(null), extensions: [ext("trust-yes")], setting: "never" }), true);
});

test("an extension that answers undecided hands the decision on", () => {
	assert.equal(run({ ...withSaved(true), extensions: [ext("trust-undecided")] }), true, "so the saved decision applies");
});

test("the flag still outranks an extension", () => {
	assert.equal(run({ ...withSaved(null), extensions: [ext("trust-yes")], approve: "no" }), false);
});
