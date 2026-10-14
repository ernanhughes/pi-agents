// An optional interactive command, not a second agent implementation.
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { runDesk } from "./run.ts";
import { SCENARIOS, type Scenario } from "./script.ts";

export default function patchDeskExtension(pi: ExtensionAPI) {
  pi.registerCommand("patch-desk", {
    description: "Run the offline Pi Patch Desk fixture and show its review directory",
    async handler(args, ctx) {
      const scenario = (args.trim() || "success") as Scenario;
      if (!SCENARIOS.includes(scenario)) {
        ctx.ui.notify(`Unknown scripted scenario: ${scenario}`, "error");
        return;
      }
      const result = await runDesk({ scenario, onEvent(event) {
        if (event.type === "host_check_end") ctx.ui.setStatus?.("patch-desk", `${event.phase} ${event.kind}: ${event.exitCode}`);
      } });
      ctx.ui.setStatus?.("patch-desk", result.status);
      ctx.ui.notify(`Pi Patch Desk: ${result.status}\nReview: ${result.directory}\nNo patch applied to the original.`, result.status === "verified" ? "info" : "warning");
    },
  });
}
