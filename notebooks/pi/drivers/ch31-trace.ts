// Chapter 31 - regenerate the chapter's evidence trace at the current pin.
//
// `experiences/ch31.ts` is a real exporter: it runs the scripted scenario against
// the shipped binary and writes a `book-evidence-trace/1` envelope. Nothing here
// writes a trace by hand; this driver only calls the exporter and reports what
// came back, so the notebook can compare it with the published 1.0.2 recording.

import { ch31 } from "../experiences/ch31.ts";

const trace = await ch31();

console.log(JSON.stringify({
	schema: trace.schema,
	result: trace.result,
	recordedAt: trace.recordedAt,
	environment: trace.environment,
	evidenceScope: trace.evidenceScope,
	claimClass: trace.claimClass,
	source: trace.source,
	runs: trace.runs.map((r) => ({
		id: r.id,
		label: r.label,
		events: r.events.map((e) => `${e.layer}:${e.type}`),
	})),
	observations: trace.observations,
	limits: trace.limits,
}));