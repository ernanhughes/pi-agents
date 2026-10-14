// Chapter 22, second half - the two rules a package author gets wrong most easily.
//
// 1. The dependency rule. A host-provided package in `dependencies` draws a
//    warning; the same package in `peerDependencies` with a "*" range does not.
// 2. The filter rule. A filter narrows what a package declares and can never
//    expose something the package left out.
//
// Both are run against the SHIPPED binary, offline.

import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { runPi, runRaw } from "../harness/cli.ts";

function makePackage(extra: Record<string, unknown> = {}, elsewhere = false) {
	const root = mkdtempSync(join(tmpdir(), "pinb-ch22b-"));
	const pkg = join(root, "my-pkg");
	const agentDir = join(root, "agent");
	const cwd = join(root, "repo");
	const dirs = [join(pkg, "prompts"), join(pkg, "extensions"), agentDir, cwd];
	if (elsewhere) dirs.push(join(pkg, "elsewhere"));
	for (const d of dirs) mkdirSync(d, { recursive: true });
	writeFileSync(join(pkg, "package.json"), JSON.stringify({ name: "my-pkg", version: "1.0.0", keywords: ["pi-package"], ...extra }));
	writeFileSync(join(pkg, "prompts", "greet.md"), "---\ndescription: greet\n---\nHELLO-FROM-PACKAGE $1");
	writeFileSync(join(pkg, "extensions", "flag.ts"), 'import { appendFileSync } from "node:fs";\nexport default function (pi: any) { appendFileSync(process.cwd() + "/loaded.log", "x"); }\n');
	if (elsewhere) writeFileSync(join(pkg, "elsewhere", "other.md"), "---\ndescription: other\n---\nFROM-ELSEWHERE");
	return { root, pkg, agentDir, cwd };
}

const loads = (cwd: string) => (existsSync(join(cwd, "loaded.log")) ? readFileSync(join(cwd, "loaded.log"), "utf8").length : 0);

/** One faux print-mode run; returns what the model received as its first user message, plus stderr. */
function ask(p: ReturnType<typeof makePackage>, prompt: string, extra: string[] = []) {
	const r = runPi({ script: [{ text: "ok" }], args: ["--mode", "json", ...extra, prompt], cwd: p.cwd, agentDir: p.agentDir });
	const recs = r.stdout.trim().split("\n").filter(Boolean).map((l) => JSON.parse(l));
	const user = recs.find((x) => x.type === "message_end" && x.message?.role === "user");
	return { text: [...(user?.message?.content ?? [])].map((b: any) => b.text ?? b).join("\n"), stderr: r.stderr };
}

const HOST_PROVIDED = "@earendil-works/pi-ai";
const warningLine = (stderr: string) => stderr.split(/\r?\n/).find((l) => /Host-provided/.test(l)) ?? "";

// --- 1. the dependency rule, both ways --------------------------------------
const bundled = makePackage({ dependencies: { [HOST_PROVIDED]: "*" } });
runRaw(["install", bundled.pkg], bundled);
const bundledRun = ask(bundled, "hi");
const declared = makePackage({ peerDependencies: { [HOST_PROVIDED]: "*" } });
runRaw(["install", declared.pkg], declared);
const declaredRun = ask(declared, "hi");

// --- 2a. the object form narrows one type and leaves the others -------------
const filtered = makePackage();
writeFileSync(join(filtered.agentDir, "settings.json"), JSON.stringify({ packages: [{ source: filtered.pkg, prompts: [] }] }));
const filteredRun = ask(filtered, "/greet x");

// --- 2b. a filter cannot expose what the package did not declare ------------
const manifest = makePackage({ pi: { prompts: ["./elsewhere/*.md"] } }, true);
writeFileSync(join(manifest.agentDir, "settings.json"), JSON.stringify({ packages: [manifest.pkg] }));
const control = { declared: ask(manifest, "/other"), undeclared: ask(manifest, "/greet x") };
writeFileSync(join(manifest.agentDir, "settings.json"), JSON.stringify({ packages: [{ source: manifest.pkg, prompts: ["prompts/greet.md"] }] }));
const exposedByFilter = ask(manifest, "/greet x");

console.log(
	JSON.stringify({
		dependencies: {
			warned: /Host-provided/.test(bundledRun.stderr),
			warning: warningLine(bundledRun.stderr).trim(),
			peerWarned: /Host-provided/.test(declaredRun.stderr),
			stillLoadsEitherWay: /HELLO-FROM-PACKAGE/.test(ask(declared, "/greet y").text) || loads(declared.cwd) > 0,
		},
		filterNarrows: { templateExpanded: /HELLO-FROM-PACKAGE/.test(filteredRun.text), extensionLoads: loads(filtered.cwd) },
		filterCannotExpose: {
			declaredTemplateLoads: /FROM-ELSEWHERE/.test(control.declared.text),
			undeclaredTemplateLoads: /HELLO-FROM-PACKAGE/.test(control.undeclared.text),
			namingItInAFilterLoads: /HELLO-FROM-PACKAGE/.test(exposedByFilter.text),
		},
	}),
);