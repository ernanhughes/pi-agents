pi.registerCommand("guard", {
  description: "Inspect and configure the path guard",
  handler: async (_args, ctx) => {
    if (ctx.hasUI) {
      const choice = await ctx.ui.select("Path guard", ["Status", "Pause", "Resume"]);
      ctx.ui.notify(`Chose: ${choice ?? "cancelled"}`, "info");
      return;
    }

    // JSON and print: no UI at all. Say something useful on the way out.
    console.log(`[guard] ${blocks.length} blocked call(s); run this in interactive mode to configure`);
  },
});
