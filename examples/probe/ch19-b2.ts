const rebuild = (ctx: ExtensionContext) => {
  const next: GuardBlock[] = [];
  for (const entry of ctx.sessionManager.getBranch()) {
    if (entry.type === "custom" && entry.customType === "guard.block") {
      next.push(entry.data as GuardBlock);
    }
  }
  blocks = next;
};

pi.on("session_start", async (_e, ctx) => rebuild(ctx));
pi.on("session_tree", async (_e, ctx) => rebuild(ctx));
