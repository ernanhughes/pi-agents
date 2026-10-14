pi.registerCommand("guard-blocks", {
  description: "Show blocked calls recorded on this branch",
  handler: async (_args, ctx) => {
    if (ctx.mode !== "tui") {
      ctx.ui.notify("/guard-blocks requires interactive mode", "error");
      return;
    }

    await ctx.ui.custom<void>((_tui, theme, _kb, done) => {
      return new BlockListComponent(blocks, theme, () => done());
    });
  },
});
