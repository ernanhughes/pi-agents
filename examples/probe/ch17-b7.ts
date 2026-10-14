pi.registerToolRenderer((toolName, next) => {
  if (toolName.startsWith("mcp__")) {
    return { renderCall: () => ({ custom: "call an MCP server" }) };
  }
  return next();
});
