import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { citationsAreReal } from "../ch40-composition/pipeline.ts";
import { authorize } from "./policy.ts";

export interface Citation { path: string; start: number; end: number; quote: string }
export const digest = (text: string | Buffer) => createHash("sha256").update(text).digest("hex");

/** This checks source identity, not the semantic truth of arbitrary model prose.
 * Reuse chapter 40's exact-quotation check, and close its empty-array gap here. */
export function validateCitations(root: string, citations: Citation[]): void {
  if (!citations.length || citations.length > 8) throw new Error("a conclusion needs 1–8 source citations");
  const excerpts = citations.map((c) => {
    const path = authorize(root, "read_file", { path: c.path })!;
    const lines = readFileSync(path, "utf8").split(/\r?\n/);
    if (!Number.isInteger(c.start) || !Number.isInteger(c.end) || c.start < 1 || c.end < c.start || c.end > lines.length) throw new Error("citation line range does not exist");
    const actual = lines.slice(c.start - 1, c.end).join("\n");
    if (!c.quote.trim() || actual !== c.quote) throw new Error("citation differs from the current source");
    return actual;
  });
  if (!citationsAreReal({ verdict: "supported", confidence: 1, citations: citations.map((c) => c.quote), reason: "exact source identity only" }, excerpts)) throw new Error("invented citation");
}

// No raw transcript is persisted. Also sanitize bounded model/check text.
export function redact(text: string): string {
  return text.replace(/\b(?:sk-[\w-]+|Bearer\s+[\w.\/-]+)\b/gi, "[REDACTED]")
    .replace(/((?:api[_-]?key|token|password|secret)\s*[:=]\s*)[^\s,;"}]+/gi, "$1[REDACTED]");
}
