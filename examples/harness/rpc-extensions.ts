// Extensions used by the RPC tests. They are loaded into the shipped binary.
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
	// A command that waits on a dialog, so the extension UI subprotocol is exercised.
	pi.registerCommand("ask", {
		description: "ask the client to confirm",
		handler: async (_args, ctx) => {
			const ok = await ctx.ui.confirm("Clear session?", "All messages will be lost.");
			ctx.ui.notify(ok ? "confirmed" : "declined", "info");
		},
	});

	// A handler that throws, so extension_error is exercised.
	pi.on("agent_start", async () => {
		if (process.env.PI_TEST_THROW) throw new Error("handler bug");
	});
}
