import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

// For a provider whose context-overflow message Pi does not recognise: rewrite
// only that provider's overflow response, and nothing else, so Pi's own
// compact-and-retry recovery can run.
export default function (pi: ExtensionAPI) {
	pi.on("message_end", async (event) => {
		const msg = event.message;
		if (msg.role !== "assistant") return;
		if (msg.stopReason !== "error") return;
		if (!msg.errorMessage?.includes("model is too long")) return;

		return {
			message: { ...msg, errorMessage: "context_length_exceeded" },
		};
	});
}
