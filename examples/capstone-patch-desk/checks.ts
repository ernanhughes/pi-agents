import { fileURLToPath } from "node:url";
import { join } from "node:path";
import { runProcess, type ProcessResult } from "./process.ts";

const examples = fileURLToPath(new URL("../", import.meta.url));
export type CheckKind = "tests" | "typecheck" | "grader";
export interface CheckRecord extends ProcessResult { phase: "before" | "after"; kind: CheckKind }

export function checkCommand(root: string, kind: CheckKind): string[] {
  switch (kind) {
    case "tests": return [process.execPath, "--test", "tests/regression.ts"];
    case "grader": return [process.execPath, fileURLToPath(new URL("grader.ts", import.meta.url)), join(root, "src/records.ts")];
    case "typecheck": return [process.execPath, join(examples, "node_modules/typescript/bin/tsc"), "--noEmit", "--strict", "--target", "ES2023", "--module", "NodeNext", "--moduleResolution", "NodeNext", "--allowImportingTsExtensions", "--skipLibCheck", "--types", "node", "--typeRoots", join(examples, "node_modules/@types"), "src/records.ts", "tests/regression.ts"];
  }
}

export async function check(root: string, kind: CheckKind, phase: CheckRecord["phase"], signal: AbortSignal): Promise<CheckRecord> {
  return { phase, kind, ...await runProcess(checkCommand(root, kind), root, signal) };
}
