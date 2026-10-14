// The recorded-evidence envelope, schema "book-evidence-trace/1".
//
// It is a recording of a SCRIPTED run, produced by the same kind of code as the book's tests. It
// is not a live model run and says so in `model` and `limits`. Each experience runs a real
// scenario and writes what happened; nothing in a trace is written by hand.
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const pkgVersion = (name: string): string =>
	JSON.parse(readFileSync(join(here, "..", "node_modules", "@earendil-works", name, "package.json"), "utf8")).version;

export interface TraceEvent {
	seq: number;
	atMs: number;
	layer: string;
	type: string;
	summary: string;
	data?: Record<string, unknown>;
}

export interface Observation {
	id: string;
	label: string;
	expected: string;
	observed: string;
	/** null means "recorded for information; no expectation was asserted". */
	pass: boolean | null;
}

export interface Run {
	id: string;
	label: string;
	description: string;
	events: TraceEvent[];
}

export interface Trace {
	schema: "book-evidence-trace/1";
	book: { slug: string; title: string };
	chapter: { number: number; title: string };
	experiment: { id: string; title: string };
	claimClass: "OBSERVED";
	evidenceScope: "in_process_runtime" | "shipped_binary";
	recordedAt: string;
	environment: Record<string, string>;
	model: { kind: "scripted"; provider: "faux"; note: string };
	claim: string;
	prediction: string;
	source: { test: string; exporter: string };
	runs: Run[];
	observations: Observation[];
	result: "PASS" | "FAIL";
	limits: string[];
}

export function environment(): Record<string, string> {
	return {
		"pi-ai": pkgVersion("pi-ai"),
		"pi-agent-core": pkgVersion("pi-agent-core"),
		"pi-coding-agent": pkgVersion("pi-coding-agent"),
		node: process.version,
		platform: process.platform,
	};
}

export class Recorder {
	events: TraceEvent[] = [];
	private t0 = performance.now();
	log(layer: string, type: string, summary: string, data?: Record<string, unknown>): void {
		this.events.push({ seq: this.events.length + 1, atMs: Math.round((performance.now() - this.t0) * 10) / 10, layer, type, summary, data });
	}
}

export function finish(t: Omit<Trace, "result" | "schema" | "recordedAt" | "environment" | "model" | "claimClass" | "book">): Trace {
	const failed = t.observations.some((o) => o.pass === false);
	return {
		schema: "book-evidence-trace/1",
		book: { slug: "pi", title: "Pi Agents" },
		claimClass: "OBSERVED",
		recordedAt: new Date().toISOString(),
		environment: environment(),
		model: { kind: "scripted", provider: "faux", note: "The model is a scripted stand-in. Nothing here shows how a real model behaves." },
		result: failed ? "FAIL" : "PASS",
		...t,
	};
}
