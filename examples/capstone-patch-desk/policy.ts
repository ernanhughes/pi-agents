import { lstatSync, realpathSync, readFileSync } from "node:fs";
import { join, relative, resolve, sep } from "node:path";

export const EDITABLE = Object.freeze(["src/records.ts", "tests/regression.ts"]);
export const READABLE = Object.freeze([...EDITABLE, "README.md"]);
export const FILE_BYTES = 16_384;

export class PolicyRefusal extends Error {}

/** One decision function, used by the Pi hook AND immediately before effects.
 * No batch, nested dispatch, shell, alias, or model-supplied approval is supported.
 * This is an application policy, not an OS sandbox. */
export function authorize(root: string, name: string, args: unknown): string | undefined {
  if (!args || typeof args !== "object" || Array.isArray(args)) throw new PolicyRefusal("arguments must be an object");
  const a = args as Record<string, unknown>;
  const keys = Object.keys(a).sort().join(",");
  if (name === "check") {
    if (keys !== "kind" || !["tests", "typecheck"].includes(String(a.kind))) throw new PolicyRefusal("only fixed tests/typecheck commands are allowed");
    return;
  }
  if (name === "submit") {
    if (keys !== "citations,summary") throw new PolicyRefusal("submission cannot supply approval or tool calls");
    return;
  }
  if (name !== "read_file" && name !== "write_file") throw new PolicyRefusal(`tool is not allowed: ${name}`);
  if (keys !== (name === "read_file" ? "path" : "content,path")) throw new PolicyRefusal("unexpected arguments (including nested calls or approval)");
  const allowed = name === "read_file" ? READABLE : EDITABLE;
  if (typeof a.path !== "string" || !allowed.includes(a.path)) throw new PolicyRefusal("path is outside the exact fixture allowlist");
  if (name === "write_file" && (typeof a.content !== "string" || Buffer.byteLength(a.content) > FILE_BYTES)) throw new PolicyRefusal("write exceeds the file budget");
  const base = realpathSync(root);
  // Reject every symlink/junction component, even one that currently points inward.
  let current = base;
  for (const component of a.path.split("/")) {
    current = join(current, component);
    if (lstatSync(current).isSymbolicLink()) throw new PolicyRefusal("symlinks/junctions are not allowed");
  }
  const target = realpathSync(current);
  const rel = relative(base, target);
  if (!rel || rel.startsWith(`..${sep}`) || resolve(base, rel) !== target) throw new PolicyRefusal("path escaped the workspace");
  if (Buffer.byteLength(readFileSync(target)) > FILE_BYTES) throw new PolicyRefusal("read exceeds the file budget");
  return target;
}
