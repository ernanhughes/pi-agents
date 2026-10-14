// Chapter 22 - what `pi install` records, and what it does not do.
//
// A real package directory on disk, installed with the SHIPPED binary and no
// network. The claims are about files: what lands in settings.json, whether
// anything was copied, and what `pi list` and `pi remove` then report.

import { existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, relative, isAbsolute } from "node:path";
import { runPi, runRaw } from "../harness/cli.ts";

function makePackage(extra: Record<string, unknown> = {}) {
	const root = mkdtempSync(join(tmpdir(), "pinb-ch22-"));
	const pkg = join(root, "my-pkg");
	const agentDir = join(root, "agent");
	const cwd = join(root, "repo");
	for (const d of [join(pkg, "prompts"), join(pkg, "extensions"), agentDir, cwd]) mkdirSync(d, { recursive: true });
	writeFileSync(join(pkg, "package.json"), JSON.stringify({ name: "my-pkg", version: "1.0.0", keywords: ["pi-package"], ...extra }));
	writeFileSync(join(pkg, "prompts", "greet.md"), "---\ndescription: greet\n---\nHELLO-FROM-PACKAGE $1");
	// The extension appends a byte per load, so "how many times did it load" is a file length.
	writeFileSync(join(pkg, "extensions", "flag.ts"), 'import { appendFileSync } from "node:fs";\nexport default function (pi: any) { appendFileSync(process.cwd() + "/loaded.log", "x"); }\n');
	return { root, pkg, agentDir, cwd };
}

const settings = (agentDir: string) => JSON.parse(readFileSync(join(agentDir, "settings.json"), "utf8"));
const loads = (cwd: string) => (existsSync(join(cwd, "loaded.log")) ? readFileSync(join(cwd, "loaded.log"), "utf8").length : 0);

/** What the model received as its first user message, by asking a prompt template to expand. */
function ask(p: ReturnType<typeof makePackage>, prompt: string, extra: string[] = []) {
	const r = runPi({ script: [{ text: "ok" }], args: ["--mode", "json", ...extra, prompt], cwd: p.cwd, agentDir: p.agentDir });
	const recs = r.stdout.trim().split("\n").filter(Boolean).map((l) => JSON.parse(l));
	const user = recs.find((x) => x.type === "message_end" && x.message?.role === "user");
	return { text: [...(user?.message?.content ?? [])].map((b: any) => b.text ?? b).join("\n"), stderr: r.stderr };
}

const p = makePackage();
const install = runRaw(["install", p.pkg], p);
const entry = settings(p.agentDir).packages[0];
const source = typeof entry === "string" ? entry : entry.source;
const listed = runRaw(["list"], p);
const afterInstall = ask(p, "/greet world");
const removed = runRaw(["remove", p.pkg], p);
const afterRemove = ask(p, "/greet world");

// One invocation, nothing written: `pi -e` is the other way to use a package.
const once = makePackage();
const oneShot = ask(once, "/greet there", ["-e", once.pkg]);

console.log(
	JSON.stringify({
		install: {
			exit: install.status,
			entryIsString: typeof entry === "string",
			source,
			isAbsolute: isAbsolute(source),
			relativeToSettings: relative(p.agentDir, p.pkg).split("\\").join("/"),
			resolvesToPackage: join(p.agentDir, source) === p.pkg,
			packageStillOnDisk: existsSync(join(p.pkg, "package.json")),
			copiedIntoAgentDir: existsSync(join(p.agentDir, "my-pkg")),
			agentDirEntries: readdirSync(p.agentDir).sort(),
		},
		list: { exit: listed.status, showsPackage: /my-pkg/.test(listed.stdout), section: /User packages:/.test(listed.stdout) },
		loaded: { expanded: /HELLO-FROM-PACKAGE world/.test(afterInstall.text), extensionLoads: loads(p.cwd) },
		remove: { exit: removed.status, stillListed: /my-pkg/.test(runRaw(["list"], p).stdout), stillExpands: /HELLO-FROM-PACKAGE/.test(afterRemove.text) },
		oneShot: { expanded: /HELLO-FROM-PACKAGE there/.test(oneShot.text), settingsWritten: existsSync(join(once.agentDir, "settings.json")) && /my-pkg/.test(readFileSync(join(once.agentDir, "settings.json"), "utf8")) },
	}),
);

