import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { DefaultResourceLoader } from "@earendil-works/pi-coding-agent";
import { makeSession, UiRecorder } from "../harness/session.ts";
import patchDeskExtension from "./extension.ts";
import { runProcess } from "./process.ts";

const here = dirname(fileURLToPath(import.meta.url));

test("real Pi command invokes the shared host and reports completed verification", async () => {
  const ui = new UiRecorder();
  const h = await makeSession({ extensions: [patchDeskExtension], tools: [], ui });
  let directory: string | undefined;
  try {
    await h.session.prompt("/patch-desk");
    assert.equal(h.faux.state.callCount, 0, "the command itself needs no outer model call");
    const notice = ui.notifications.find((n) => n.message.startsWith("Pi Patch Desk:"))!;
    assert.ok(notice, JSON.stringify(ui.notifications));
    assert.match(notice.message, /Pi Patch Desk: verified/);
    directory = notice.message.split("\n")[1].slice("Review: ".length);
    assert.equal(JSON.parse(readFileSync(join(directory, "run.json"), "utf8")).completed, true);
    assert.equal(JSON.parse(readFileSync(join(directory, "run.json"), "utf8")).applied, false);
  } finally {
    h.dispose();
    if (directory && resolve(directory).startsWith(resolve(here, "runs") + sep)) rmSync(directory, { recursive: true, force: true });
    rmSync(dirname(h.agentDir), { recursive: true, force: true });
  }
});

test("pinned resource loader discovers the explicit prompt template and skill", async () => {
  const root = mkdtempSync(join(tmpdir(), "desk-resources-"));
  try {
    const loader = new DefaultResourceLoader({ cwd: root, agentDir: root, noExtensions: true, noContextFiles: true, noThemes: true,
      noSkills: true, noPromptTemplates: true,
      additionalSkillPaths: [join(here, "skills/pi-patch-desk")],
      additionalPromptTemplatePaths: [join(here, "prompts/fix-verified.md")],
    });
    await loader.reload();
    assert.equal(loader.getSkills().skills.some((s) => s.name === "pi-patch-desk"), true);
    assert.equal(loader.getPrompts().prompts.some((p) => p.name === "fix-verified"), true);
    assert.deepEqual(loader.getSkills().diagnostics, []);
    assert.deepEqual(loader.getPrompts().diagnostics, []);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("headless driver emits final completion only after the Pi loop and host checks", async () => {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15_000);
  let directory: string | undefined;
  try {
    const result = await runProcess([process.execPath, join(here, "cli.ts"), "--json"], here, controller.signal);
    assert.equal(result.exitCode, 0, result.stderr);
    const events = result.stdout.trim().split("\n").map((line) => JSON.parse(line));
    assert.equal(events.at(-1).type, "desk_completed");
    assert.equal(events.at(-1).status, "verified");
    assert.ok(events.findIndex((e) => e.type === "agent_end") < events.findIndex((e) => e.type === "host_check_end" && e.kind === "grader"));
    directory = events.at(-1).directory;
    assert.ok(directory && existsSync(join(directory, "review.md")));
  } finally {
    clearTimeout(timer);
    if (directory && resolve(directory).startsWith(resolve(here, "runs") + sep)) rmSync(directory, { recursive: true, force: true });
  }
});
