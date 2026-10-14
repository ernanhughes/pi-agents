import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, lstatSync, mkdtempSync, readFileSync, readdirSync, rmSync, symlinkSync, writeFileSync, cpSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { runDesk, LIMITS } from "./run.ts";
import { authorize, PolicyRefusal } from "./policy.ts";
import { digest, redact, validateCitations } from "./evidence.ts";
import { runProcess } from "./process.ts";
import type { Scenario } from "./script.ts";

const here = dirname(fileURLToPath(import.meta.url));
const fixture = join(here, "fixture");
const expectedArtifacts = ["events.jsonl", "evidence.json", "manifest.json", "patch.diff", "review.md", "run.json", "tests.json"];
const json = (dir: string, file: string) => JSON.parse(readFileSync(join(dir, file), "utf8"));
const originalSource = () => digest(readFileSync(join(fixture, "src/records.ts")));
const gitStatus = () => {
  const options = { cwd: here, encoding: "utf8" as const, windowsHide: true };
  const status = spawnSync("git", ["status", "--porcelain", "--untracked-files=all"], options).stdout;
  // Other chapter suites run concurrently. Pi's existing atomic settings writer
  // briefly creates these files in examples/; they are unrelated to this run.
  const stable = status.split("\n").filter((line) => !/^\?\? examples\/_tmp_\d+_[0-9a-f]+$/.test(line)).join("\n");
  // Status alone would miss changes to a file that was already marked modified.
  return stable + digest(spawnSync("git", ["diff", "--binary", "HEAD"], options).stdout);
};

async function demo(scenario: Scenario, inspect: (result: Awaited<ReturnType<typeof runDesk>>) => void | Promise<void>) {
  const root = mkdtempSync(join(tmpdir(), "desk-test-"));
  const sourceBefore = originalSource();
  const worktreeBefore = gitStatus();
  try {
    const result = await runDesk({ scenario, outputRoot: root });
    assert.deepEqual(readdirSync(result.directory).sort(), expectedArtifacts);
    const bytes = readdirSync(result.directory).reduce((n, f) => n + readFileSync(join(result.directory, f)).length, 0);
    assert.ok(bytes <= LIMITS.artifactBytes);
    const events = readFileSync(join(result.directory, "events.jsonl"), "utf8").trim().split("\n").map((line) => JSON.parse(line));
    assert.ok(events.length <= LIMITS.events);
    assert.ok(Buffer.byteLength(JSON.stringify(events)) <= LIMITS.eventBytes);
    assert.equal(json(result.directory, "run.json").originalUnchanged, true);
    assert.equal(json(result.directory, "run.json").applied, false);
    assert.equal(json(result.directory, "manifest.json").piVersion, "1.0.4");
    assert.ok(readFileSync(join(result.directory, "review.md"), "utf8").includes("Not measured"));
    await inspect(result);
    assert.equal(originalSource(), sourceBefore);
    assert.equal(gitStatus(), worktreeBefore, "the original worktree must not change during a run");
  } finally { rmSync(root, { recursive: true, force: true }); }
}

test("actual Pi loop reproduces the bug, fixes the copy, and produces a reviewable patch", async () => {
  await demo("success", (r) => {
    assert.equal(r.status, "verified");
    assert.equal(r.checks[0].phase, "before");
    assert.equal(r.checks[0].exitCode, 1);
    assert.deepEqual(r.checks.slice(-3).map((c) => [c.kind, c.exitCode]), [["tests", 0], ["typecheck", 0], ["grader", 0]]);
    assert.equal(r.requests, 7);
    assert.equal(r.toolCalls, 7);
    assert.match(r.patch, /\+    if \(line.trim\(\) === ""\) continue;/);
    assert.match(r.patch, /\+test\("surrounding whitespace-only lines and CRLF"/);
    const paths = r.patch.split("\n").filter((l) => l.startsWith("+++ "));
    assert.deepEqual(paths, ["+++ b/src/records.ts", "+++ b/tests/regression.ts"]);
    const events = readFileSync(join(r.directory, "events.jsonl"), "utf8").trim().split("\n").map((l) => JSON.parse(l));
    assert.equal(events.filter((e) => e.type === "agent_end").length, 1);
    assert.equal(events.filter((e) => e.type === "tool_execution_end").length, 7);
    assert.ok(events.findIndex((e) => e.type === "agent_end") < events.findIndex((e) => e.type === "host_check_end" && e.kind === "grader"));
    // A consumer can apply the generated patch to another disposable copy.
    const copy = join(r.directory, "apply-check");
    cpSync(fixture, copy, { recursive: true });
    const apply = spawnSync("git", ["apply", "--check", join(r.directory, "patch.diff")], { cwd: copy, encoding: "utf8", windowsHide: true });
    assert.equal(apply.status, 0, apply.stderr);
  });
});

test("repeated scripted runs yield the same patch and normalized results", async () => {
  let first: Awaited<ReturnType<typeof runDesk>>;
  await demo("success", (r) => { first = r; });
  await demo("success", (r) => {
    assert.equal(r.patch, first.patch);
    assert.deepEqual([r.status, r.requests, r.toolCalls, r.checks.map((c) => c.exitCode)], [first.status, first.requests, first.toolCalls, first.checks.map((c) => c.exitCode)]);
  });
});

for (const scenario of ["forbidden", "traversal", "alias", "nested", "injection", "symlink", "bad-citation", "altered-citation", "empty-citation", "failed-tests", "weakened-tests", "error", "refusal", "invalid-output", "tool-error", "budget", "tool-budget", "abort", "timeout"] as const) {
  test(`actual Pi failure path: ${scenario} still writes evidence and preserves originals`, async () => {
    await demo(scenario, (r) => {
      assert.notEqual(r.status, "verified");
      assert.ok(r.failures.length);
      if (["forbidden", "traversal", "alias", "nested", "injection", "symlink", "tool-error"].includes(scenario)) assert.equal(r.status, "refused");
      if (scenario === "injection") assert.equal(r.toolCalls, 1, "extra approved field is schema-rejected before execute");
      if (scenario === "budget") { assert.equal(r.status, "budget-exhausted"); assert.equal(r.requests, 2); }
      if (scenario === "tool-budget") { assert.equal(r.status, "budget-exhausted"); assert.equal(r.toolCalls, 2); }
      if (scenario === "abort" || scenario === "timeout") assert.equal(r.status, scenario === "abort" ? "aborted" : "timeout");
      if (scenario === "failed-tests") assert.ok(r.checks.some((c) => c.phase === "after" && c.kind === "tests" && c.exitCode === 1));
      if (scenario === "weakened-tests") {
        assert.equal(r.checks.findLast((c) => c.kind === "tests")?.exitCode, 0);
        assert.equal(r.checks.findLast((c) => c.kind === "grader")?.exitCode, 1);
      }
      if (scenario === "error") assert.ok(!readFileSync(join(r.directory, "run.json"), "utf8").includes("sk-demo-secret"));
    });
  });
}

test("central policy rejects traversal, aliases, nested calls, approval, and shell strings", () => {
  const denied = [
    ["write_file", { path: "../outside.ts", content: "oops" }],
    ["write_file", { path: "src/../package.json", content: "oops" }],
    ["write_file", { path: "C:\\outside.ts", content: "oops" }],
    ["write_file", { path: "src\\records.ts", content: "oops" }],
    ["functions.write_file", { path: "src/records.ts", content: "oops" }],
    ["read_file", { path: "README.md", toolCalls: [{ tool: "write_file" }] }],
    ["write_file", { path: "src/records.ts", content: "oops", approved: true }],
    ["check", { kind: "tests && echo secret" }],
    ["write_file", { path: "src/records.ts", content: "x".repeat(LIMITS.fileBytes + 1) }],
  ] as const;
  for (const [name, args] of denied) assert.throws(() => authorize(fixture, name, args), PolicyRefusal);
});

test("symlink and directory-junction escapes are refused before effects", async (t) => {
  const root = mkdtempSync(join(tmpdir(), "desk-symlink-"));
  const workspace = join(root, "workspace");
  cpSync(fixture, workspace, { recursive: true });
  try {
    rmSync(join(workspace, "src"), { recursive: true });
    try { symlinkSync(join(fixture, "src"), join(workspace, "src"), process.platform === "win32" ? "junction" : "dir"); }
    catch (error) { t.skip(`symlink creation unavailable: ${error}`); return; }
    assert.equal(lstatSync(join(workspace, "src")).isSymbolicLink(), true);
    assert.throws(() => authorize(workspace, "write_file", { path: "src/records.ts", content: "oops" }), PolicyRefusal);
    assert.equal(readFileSync(join(fixture, "src/records.ts"), "utf8").includes("oops"), false);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("citation ranges and quotations must exist, and an empty conclusion fails", () => {
  const line = readFileSync(join(fixture, "src/records.ts"), "utf8").split(/\r?\n/)[0];
  validateCitations(fixture, [{ path: "src/records.ts", start: 1, end: 1, quote: line }]);
  assert.throws(() => validateCitations(fixture, []), /needs/);
  assert.throws(() => validateCitations(fixture, [{ path: "src/records.ts", start: 100, end: 100, quote: "fake" }]), /does not exist/);
  assert.throws(() => validateCitations(fixture, [{ path: "src/records.ts", start: 1, end: 1, quote: "fake" }]), /differs/);
});

test("watchdog kills otherwise continuing work and waits for child closure", async () => {
  const controller = new AbortController();
  const started = Date.now();
  const timer = setTimeout(() => controller.abort(), 250);
  try {
    const result = await runProcess([process.execPath, "-e", "console.log('started'); setInterval(() => {}, 1000)"], here, controller.signal);
    assert.match(result.stdout, /started/);
    assert.notEqual(result.exitCode, 0);
    assert.ok(Date.now() - started < 5000);
    assert.throws(() => process.kill(result.pid!, 0), "the child must no longer exist");
  } finally { clearTimeout(timer); }
});

test("process output growth terminates work instead of accumulating a transcript", async () => {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 3000);
  try {
    const result = await runProcess([process.execPath, "-e", "setInterval(() => console.log('x'.repeat(1024)), 1)"], here, controller.signal, 2048);
    assert.equal(result.truncated, true);
    assert.ok(Buffer.byteLength(result.stdout + result.stderr) <= 2048);
    assert.throws(() => process.kill(result.pid!, 0));
  } finally { clearTimeout(timer); }
});

test("caller cancellation before setup still returns a failed dossier", async () => {
  const root = mkdtempSync(join(tmpdir(), "desk-abort-"));
  try {
    const signal = AbortSignal.abort();
    const r = await runDesk({ outputRoot: root, signal });
    assert.equal(r.status, "aborted");
    assert.equal(json(r.directory, "run.json").applied, false);
    assert.deepEqual(readdirSync(r.directory).sort(), expectedArtifacts);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("optional display failure does not corrupt the workflow", async () => {
  const root = mkdtempSync(join(tmpdir(), "desk-display-"));
  try {
    const r = await runDesk({ outputRoot: root, onEvent() { throw new Error("display unavailable"); } });
    assert.equal(r.status, "verified");
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("common credential-shaped text is redacted", () => {
  assert.equal(redact("api_key=sk-sensitive token=abc password=xyz Bearer abc.def"), "api_key=[REDACTED] token=[REDACTED] password=[REDACTED] [REDACTED]");
});
