import { spawn } from "node:child_process";

export interface ProcessResult {
  command: string[];
  exitCode: number | null;
  signal: string | null;
  stdout: string;
  stderr: string;
  truncated: boolean;
  pid?: number;
}

// Pass neither provider credentials nor the parent's general environment to checks.
export function cleanEnvironment(): NodeJS.ProcessEnv {
  const env: NodeJS.ProcessEnv = { GIT_CONFIG_NOSYSTEM: "1", GIT_CONFIG_GLOBAL: process.platform === "win32" ? "NUL" : "/dev/null" };
  for (const key of ["PATH", "SystemRoot", "WINDIR", "TEMP", "TMP", "TMPDIR"]) {
    if (process.env[key]) env[key] = process.env[key];
  }
  return env;
}

/** Abort kills the actual child and waits for close; it does not just race a promise.
 * Fixed checks launch no shell and have no child-process tree of their own. */
export async function runProcess(command: string[], cwd: string, signal: AbortSignal, maxBytes = 16_384): Promise<ProcessResult> {
  signal.throwIfAborted();
  return new Promise((resolve, reject) => {
    const child = spawn(command[0], command.slice(1), { cwd, env: cleanEnvironment(), shell: false, windowsHide: true });
    const result: ProcessResult = { command, exitCode: null, signal: null, stdout: "", stderr: "", truncated: false, pid: child.pid };
    let bytes = 0;
    const capture = (key: "stdout" | "stderr", chunk: Buffer) => {
      const remaining = Math.max(0, maxBytes - bytes);
      result[key] += chunk.subarray(0, remaining).toString("utf8");
      bytes += Math.min(chunk.length, remaining);
      if (chunk.length > remaining) { result.truncated = true; child.kill("SIGKILL"); }
    };
    child.stdout.on("data", (chunk: Buffer) => capture("stdout", chunk));
    child.stderr.on("data", (chunk: Buffer) => capture("stderr", chunk));
    const abort = () => { child.kill("SIGKILL"); };
    signal.addEventListener("abort", abort, { once: true });
    // Cover cancellation between spawn and listener registration.
    if (signal.aborted) abort();
    child.once("error", (error) => { signal.removeEventListener("abort", abort); reject(error); });
    child.once("close", (code, killedBy) => {
      signal.removeEventListener("abort", abort);
      result.exitCode = code;
      result.signal = killedBy;
      resolve(result);
    });
  });
}
