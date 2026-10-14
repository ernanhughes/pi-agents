// Chapter 22, against the SHIPPED pi binary: a real package directory, installed, listed, loaded and removed.
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { runPi, runRaw } from "../harness/cli.ts";

// A package with a prompt template, a skill and an extension. The extension appends to a log
// when its factory runs, so "how many times did it load" is the length of a file.
function makePackage(extra: Record<string, unknown> = {}) {
	const root = mkdtempSync(join(tmpdir(), "pi-pkg-"));
	const pkg = join(root, "my-pkg");
	const agentDir = join(root, "agent");
	const cwd = join(root, "repo");
	for (const d of [join(pkg, "prompts"), join(pkg, "extensions"), join(pkg, "skills", "pkg-skill"), agentDir, cwd]) mkdirSync(d, { recursive: true });
	writeFileSync(join(pkg, "package.json"), JSON.stringify({ name: "my-pkg", version: "1.0.0", keywords: ["pi-package"], ...extra }));
	writeFileSync(join(pkg, "prompts", "greet.md"), "---\ndescription: greet\n---\nHELLO FROM PACKAGE $1");
	writeFileSync(join(pkg, "skills", "pkg-skill", "SKILL.md"), "---\nname: pkg-skill\ndescription: A skill from the package.\n---\n\nbody\n");
	writeFileSync(join(pkg, "extensions", "flag.ts"), 'import { appendFileSync } from "node:fs";\nexport default function (pi: any) { appendFileSync(process.cwd() + "/loaded.log", "x"); }\n');
	return { root, pkg, agentDir, cwd };
}

const settings = (agentDir: string) => JSON.parse(readFileSync(join(agentDir, "settings.json"), "utf8"));
const loads = (cwd: string) => (existsSync(join(cwd, "loaded.log")) ? readFileSync(join(cwd, "loaded.log"), "utf8").length : 0);

/** Run a faux print-mode prompt and return the user message the model received. */
function ask(p: ReturnType<typeof makePackage>, prompt: string, extra: string[] = []) {
	const r = runPi({ script: [{ text: "ok" }], args: ["--mode", "json", ...extra, prompt], cwd: p.cwd, agentDir: p.agentDir });
	const user = r.stdout.trim().split("\n").map((l) => JSON.parse(l)).find((e) => e.type === "message_end" && e.message.role === "user");
	return { text: JSON.stringify(user?.message.content ?? ""), r };
}

test("pi install of a local path records it in the user settings, relative to the settings file, and copies nothing", () => {
	const p = makePackage();
	const r = runRaw(["install", p.pkg], p);
	assert.equal(r.status, 0, r.stderr);
	const entry = settings(p.agentDir).packages[0];
	const source = typeof entry === "string" ? entry : entry.source;
	assert.match(source.split("\\").join("/"), /^\.\.\/my-pkg$/, "a relative path from the agent directory, not a copy");
});

test("pi list shows what is installed", () => {
	const p = makePackage();
	runRaw(["install", p.pkg], p);
	const r = runRaw(["list"], p);
	assert.equal(r.status, 0);
	assert.match(r.stdout, /User packages:/);
	assert.match(r.stdout, /my-pkg/);
});

test("an installed package's prompt template and extension load, with no manifest, from the conventional directories", () => {
	const p = makePackage();
	runRaw(["install", p.pkg], p);
	const { text } = ask(p, "/greet world");
	assert.match(text, /HELLO FROM PACKAGE world/, "the package's prompt template expanded");
	assert.equal(loads(p.cwd), 1, "the package's extension loaded once");
});

test("pi -e loads a package for one invocation and writes nothing to settings", () => {
	const p = makePackage();
	const { text } = ask(p, "/greet there", ["-e", p.pkg]);
	assert.match(text, /HELLO FROM PACKAGE there/);
	assert.ok(!existsSync(join(p.agentDir, "settings.json")) || !JSON.stringify(settings(p.agentDir)).includes("my-pkg"));
});

test("pi remove takes it away again", () => {
	const p = makePackage();
	runRaw(["install", p.pkg], p);
	const r = runRaw(["remove", p.pkg], p);
	assert.equal(r.status, 0, r.stderr);
	assert.doesNotMatch(runRaw(["list"], p).stdout, /my-pkg/);
	assert.doesNotMatch(ask(p, "/greet x").text, /HELLO FROM PACKAGE/);
});

test("the object form filters a package: [] loads none of that type, and the other types still load", () => {
	const p = makePackage();
	writeFileSync(join(p.agentDir, "settings.json"), JSON.stringify({ packages: [{ source: p.pkg, prompts: [] }] }));
	const { text } = ask(p, "/greet x");
	assert.doesNotMatch(text, /HELLO FROM PACKAGE/, "prompts filtered out");
	assert.equal(loads(p.cwd), 1, "the extension was not filtered");
});

test("filters narrow what the package declares; they cannot expose something it did not", () => {
	// The manifest declares only ./elsewhere/*.md. prompts/greet.md exists in the package but is not declared.
	const p = makePackage({ pi: { prompts: ["./elsewhere/*.md"] } });
	mkdirSync(join(p.pkg, "elsewhere"));
	writeFileSync(join(p.pkg, "elsewhere", "other.md"), "---"+String.fromCharCode(10)+"description: other"+String.fromCharCode(10)+"---"+String.fromCharCode(10)+"FROM ELSEWHERE");
	// Control: with no filter, the declared template loads and the undeclared one does not.
	writeFileSync(join(p.agentDir, "settings.json"), JSON.stringify({ packages: [p.pkg] }));
	assert.match(ask(p, "/other").text, /FROM ELSEWHERE/);
	assert.doesNotMatch(ask(p, "/greet x").text, /HELLO FROM PACKAGE/);

	// Naming the undeclared file in a filter does not expose it.
	writeFileSync(join(p.agentDir, "settings.json"), JSON.stringify({ packages: [{ source: p.pkg, prompts: ["prompts/greet.md"] }] }));
	assert.doesNotMatch(ask(p, "/greet x").text, /HELLO FROM PACKAGE/, "an undeclared resource is not exposed by naming it in a filter");
});

test("the same package listed twice loads once: identity is the resolved path", () => {
	const p = makePackage();
	writeFileSync(join(p.agentDir, "settings.json"), JSON.stringify({ packages: [p.pkg, { source: p.pkg }] }));
	ask(p, "hi");
	assert.equal(loads(p.cwd), 1);
});

test("an explicit manifest can point at resources elsewhere in the package", () => {
	const p = makePackage({ pi: { prompts: ["./elsewhere/*.md"] } });
	mkdirSync(join(p.pkg, "elsewhere"));
	writeFileSync(join(p.pkg, "elsewhere", "other.md"), "---\ndescription: other\n---\nFROM ELSEWHERE");
	runRaw(["install", p.pkg], p);
	assert.match(ask(p, "/other").text, /FROM ELSEWHERE/);
	assert.doesNotMatch(ask(p, "/greet x").text, /HELLO FROM PACKAGE/, "the manifest replaced conventional discovery");
});

test("--local writes the declaration to the project settings, which load only once the project is trusted", () => {
	const p = makePackage();
	const r = runRaw(["install", "--local", p.pkg], p);
	assert.equal(r.status, 0, r.stderr);
	const projectSettings = join(p.cwd, ".pi", "settings.json");
	assert.ok(existsSync(projectSettings), "written under the project's .pi");

	const run = (approve: "yes" | "no") => {
		const r2 = runPi({ script: [{ text: "ok" }], args: ["--mode", "json", "/greet x"], cwd: p.cwd, agentDir: p.agentDir, approve });
		return r2.stdout.includes("HELLO FROM PACKAGE");
	};
	assert.equal(run("no"), false, "declined: the project's package is not loaded");
	assert.equal(run("yes"), true, "approved: it is");
});

test("a host-provided package listed in dependencies draws a warning; in peerDependencies with a * range it does not", () => {
	const bad = makePackage({ dependencies: { "@earendil-works/pi-ai": "*" } });
	runRaw(["install", bad.pkg], bad);
	const warned = ask(bad, "hi").r.stderr;
	assert.match(warned, /Host-provided extension packages must be declared in peerDependencies with a "\*" range, not dependencies: @earendil-works\/pi-ai/);

	const good = makePackage({ peerDependencies: { "@earendil-works/pi-ai": "*" } });
	runRaw(["install", good.pkg], good);
	assert.doesNotMatch(ask(good, "hi").r.stderr, /Host-provided/);
});
