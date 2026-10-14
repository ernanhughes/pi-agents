const MUTATING = new Set([
  "mcp__jira__transition_issue",
  "mcp__jira__delete_issue",
  "mcp__github__create_pull_request",
]);

pi.on("tool_call", async (event, ctx) => {
  if (!MUTATING.has(event.toolName)) return undefined;

  if (!ctx.hasUI) {
    return { block: true, reason: `${event.toolName} blocked — no UI to confirm` };
  }
  const ok = await ctx.ui.confirm(
    "Allow MCP tool call?",
    `${event.toolName} (from ${event.toolName.split("__")[1]})`,
  );
  return ok ? undefined : { block: true, reason: `${event.toolName} was not approved` };
});
