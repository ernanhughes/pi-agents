import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
	pi.registerCommand("guard", {
		description: "Inspect and configure the path guard",
		handler: async (args, ctx) => {
			ctx.ui.notify(`guard received: "${args}"`, "info");
		},
	});
}
