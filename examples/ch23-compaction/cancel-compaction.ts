import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

// The other documented outcome: refuse to compact at all.
export default function (pi: ExtensionAPI) {
	pi.on("session_before_compact", async (event) => {
		return event.reason === "manual" ? { cancel: true } : undefined;
	});
}
