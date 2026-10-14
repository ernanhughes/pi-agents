pi.registerCommand("guard", {
  description: "Inspect and configure the path guard",
  handler: async (_args, ctx) => {
    const choice = await ctx.ui.select("Path guard", [
      "Show blocked calls",
      "Pause the guard",
      "Resume the guard",
    ]);
    if (choice === "Show blocked calls") {
      ctx.ui.notify(`${blocks.length} blocked call(s) this session`, "info");
    }
  },
});
