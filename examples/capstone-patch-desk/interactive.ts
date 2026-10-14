// Launch only the pinned Pi binary and explicitly selected teaching resources.
import { spawn } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { PI_BIN } from "../harness/cli.ts";
import { cleanEnvironment } from "./process.ts";

const here = dirname(fileURLToPath(import.meta.url));
const agentDir = mkdtempSync(join(tmpdir(), "patch-desk-pi-"));
try {
  const child = spawn(process.execPath, [PI_BIN,
    "--offline", "--no-session", "--no-context-files", "--no-mcp",
    "--no-extensions", "--no-skills", "--no-prompt-templates", "--no-themes",
    "--no-tools", "--approve",
    "--extension", join(here, "extension.ts"),
    "--extension", join(here, "../harness/faux-extension.ts"),
    "--provider", "faux", "--model", "faux-1",
    "--skill", join(here, "skills/pi-patch-desk"),
    "--prompt-template", join(here, "prompts/fix-verified.md"),
  ], {
    cwd: agentDir, stdio: "inherit", windowsHide: true,
    env: { ...cleanEnvironment(), PI_CODING_AGENT_DIR: agentDir, PI_OFFLINE: "1", PI_TELEMETRY: "0", PI_SKIP_VERSION_CHECK: "1", PI_FAUX_SCRIPT: '[{"text":"Use /patch-desk to run the offline capstone; /patch-desk injection demonstrates a refusal."}]' },
  });
  process.exitCode = await new Promise<number>((resolve, reject) => {
    child.once("error", reject);
    child.once("close", (code) => resolve(code ?? 1));
  });
} finally { rmSync(agentDir, { recursive: true, force: true }); }
