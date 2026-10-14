pi.registerMcpServer("jira", {
  url: "https://mcp.example.com/jira",
  exposure: "codemode",
});
pi.unregisterMcpServer("jira");
