import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

// Records both tool accessors at the same moment, so a test can show where they
// disagree. The two differ exactly when a tool is registered but not active.
export interface AccessorSeen {
	/** The active set before the probe narrowed it. */
	beforeNarrow?: string[];
	/** Every registered tool, active or not. This is what getAllTools() reports. */
	registered?: string[];
	/** The set declared to the model, after narrowing. */
	active?: string[];
}

export const seen: AccessorSeen = {};

/** Clears the record without narrowing the caller's view of it to `never`. */
export function reset(): void {
	seen.beforeNarrow = undefined;
	seen.registered = undefined;
	seen.active = undefined;
}

export default function (pi: ExtensionAPI) {
	// `tools` on the session filters at registration, so run_checks would never be
	// registered there. Narrowing the *active* set with setActiveTools is what
	// produces the case the two accessors disagree about: the tool stays
	// registered, and is no longer declared to the model.
	pi.on("before_agent_start", () => {
		seen.beforeNarrow = pi.getActiveTools();
		pi.setActiveTools(["read"]);
		seen.registered = pi.getAllTools().map((t) => t.name);
		seen.active = pi.getActiveTools();
	});
}