pi.registerCommand("guard", {
  description: "Inspect and configure the path guard",
  getArgumentCompletions: (prefix) => {
    const modes = ["status", "pause", "resume", "reset"];
    const hit = modes.filter((m) => m.startsWith(prefix));
    return hit.length ? hit.map((m) => ({ value: m, label: m })) : null;
  },
  handler: async (args, ctx) => {
    // dispatch on args
  },
});
