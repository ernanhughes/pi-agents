import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

// The guard exactly as the chapter first showed it.
export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName !== "bash" && event.toolName !== "edit") return;
    const raw = JSON.stringify(event.input);
    if (!/(^|\s)git\s+push\b/.test(raw) && !/migrations\//.test(raw)) return;
    if (await ctx.ui.confirm("Allow this call?", raw.slice(0, 120))) return;
    return { block: true, reason: "Blocked by guard extension" };
  });
}
