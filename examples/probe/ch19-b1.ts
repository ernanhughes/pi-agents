import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

interface GuardBlock {
  tool: string;
  reason: string;
  at: number;
}

const PROTECTED = [".env", ".git/", "node_modules/"];

export default function (pi: ExtensionAPI) {
  // In-memory mirror, rebuilt from the session on every load.
  let blocks: GuardBlock[] = [];

  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName !== "write" && event.toolName !== "edit") return undefined;

    const path = String(event.input.path ?? "");
    const hit = PROTECTED.find((p) => path.includes(p));
    if (!hit) return undefined;

    const entry: GuardBlock = {
      tool: event.toolName,
      reason: `path matches ${hit}`,
      at: Date.now(),
    };
    blocks = [...blocks, entry];

    // Durable, branch-aware, and invisible to the model.
    pi.appendEntry<GuardBlock>("guard.block", entry);

    if (ctx.hasUI) ctx.ui.notify(`Blocked ${event.toolName} on ${path}`, "warning");
    return { block: true, reason: `Path "${path}" is protected` };
  });

  pi.registerCommand("guard-blocks", {
    description: "List blocked tool calls recorded in this session",
    handler: async (_args, ctx) => {
      ctx.ui.notify(
        blocks.length === 0 ? "No blocked calls in this session" : blocks.map((b) => b.reason).join("; "),
        "info",
      );
    },
  });
}
