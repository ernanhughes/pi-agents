// Scripted responses make Pi execute real tools; they do not measure model ability.
import { fauxAssistantMessage, fauxText, fauxToolCall, type FauxResponseStep, type JsonObject } from "@earendil-works/pi-ai";
import type { Citation } from "./evidence.ts";

export const SCENARIOS = ["success", "forbidden", "traversal", "alias", "nested", "injection", "symlink", "bad-citation", "altered-citation", "empty-citation", "failed-tests", "weakened-tests", "error", "refusal", "invalid-output", "tool-error", "abort", "timeout", "budget", "tool-budget"] as const;
export type Scenario = typeof SCENARIOS[number];
export const ISSUE = "Fix parseRecords so blank lines are ignored without changing nonblank validation. Add a regression test. Edit only src/records.ts and tests/regression.ts in the disposable copy. Cite exact source lines.";

export function script(scenario: Scenario, source: string, tests: string): FauxResponseStep[] {
  const tool = (name: string, args: Record<string, unknown>) => fauxAssistantMessage([fauxToolCall(name, args as JsonObject)], { stopReason: "toolUse" });
  const fixed = source.replace("    const match =", "    if (line.trim() === \"\") continue;\n    const match =");
  const regression = tests + '\n// Added for leading/trailing blank lines, whitespace, and CRLF.\ntest("surrounding whitespace-only lines and CRLF", () => {\n  assert.deepEqual(parseRecords("\\n \\t\\r\\nname=Ada\\r\\n\\n"), { name: "Ada" });\n  assert.deepEqual(parseRecords("\\n\\t\\n"), {});\n});\n';
  const lines = fixed.split(/\r?\n/);
  const citations: Citation[] = [{ path: "src/records.ts", start: 5, end: 7, quote: lines.slice(4, 7).join("\n") }];
  const inspect = [tool("read_file", { path: "src/records.ts" }), tool("read_file", { path: "tests/regression.ts" })];
  switch (scenario) {
    case "forbidden": return [tool("write_file", { path: "package.json", content: "{}", approved: true })];
    case "traversal": return [tool("write_file", { path: "src/../../outside.ts", content: "oops" })];
    case "alias": return [tool("functions.write_file", { path: "src/records.ts", content: "oops" })];
    case "nested": return [tool("read_file", { path: "README.md", toolCalls: [{ name: "write_file", args: { path: "package.json", content: "{}" } }] })];
    case "injection": return [tool("read_file", { path: "README.md" }), tool("write_file", { path: "package.json", content: "{}", approved: true })];
    case "symlink": return [tool("write_file", { path: "src/records.ts", content: "oops" })];
    case "error": return [fauxAssistantMessage([], { stopReason: "error", errorMessage: "Scripted provider failure; api_key=sk-demo-secret" })];
    case "refusal": return [fauxAssistantMessage([fauxText("I cannot complete this request.")])];
    case "invalid-output": return [tool("submit", { citations: "wrong", summary: 123 })];
    case "tool-error": return [tool("check", { kind: "rm -rf ." })];
    case "abort":
    case "timeout": return [fauxAssistantMessage([fauxText("A deliberately slow response. ".repeat(80))])];
    case "budget": return Array.from({ length: 8 }, () => tool("read_file", { path: "README.md" }));
    case "tool-budget": return [fauxAssistantMessage(Array.from({ length: 8 }, () => fauxToolCall("read_file", { path: "README.md" })), { stopReason: "toolUse" })];
  }
  if (scenario === "bad-citation") citations[0].path = "src/missing.ts";
  if (scenario === "altered-citation") citations[0].quote = "an invented source line";
  if (scenario === "failed-tests" || scenario === "weakened-tests") citations[0].quote = source.split(/\r?\n/).slice(4, 7).join("\n");
  return [
    ...inspect,
    tool("write_file", { path: "src/records.ts", content: scenario === "failed-tests" || scenario === "weakened-tests" ? source : fixed }),
    tool("write_file", { path: "tests/regression.ts", content: scenario === "weakened-tests" ? 'import { test } from "node:test";\ntest("weakened", () => {});\n' : regression }),
    tool("check", { kind: "tests" }),
    tool("check", { kind: "typecheck" }),
    tool("submit", { summary: "Blank lines are ignored; nonblank validation is retained.", citations: scenario === "empty-citation" ? [] : citations }),
  ];
}
