// Writes recorded-trace.json files for the programmer.ie AI-experience pages.
//   node export-experience.ts <outDir>      e.g. ../../programmer.ie/content/tools/ai/pi
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { ch31 } from "./experiences/ch31.ts";
import { ch39 } from "./experiences/ch39.ts";
import type { Trace } from "./experiences/envelope.ts";

const out = process.argv[2];
if (!out) {
	console.error("usage: node export-experience.ts <outDir>");
	process.exit(2);
}

const jobs: [string, () => Promise<Trace>][] = [["31-chapter", ch31], ["39-chapter", ch39]];
let failed = 0;
for (const [dir, run] of jobs) {
	const trace = await run();
	mkdirSync(join(out, dir), { recursive: true });
	writeFileSync(join(out, dir, "recorded-trace.json"), JSON.stringify(trace, null, 2) + "\n");
	const events = trace.runs.reduce((n, r) => n + r.events.length, 0);
	console.log(`${dir}: ${trace.result}, ${trace.observations.length} observations, ${events} events`);
	if (trace.result !== "PASS") failed++;
}
process.exit(failed ? 1 : 0);
