// Writes an `executable_evidence` block into each chapter's metadata record, from evidence.json.
// Run `npm run evidence` first. The block is always the last key in the file and is replaced on
// every run, so it cannot drift from the ledger. Nothing else in a record is touched.
import { readFileSync, readdirSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const metaDir = join(here, "..", "metadata");
const ev = JSON.parse(readFileSync(join(here, "evidence.json"), "utf8"));

const KEY = "executable_evidence:";
let touched = 0;

for (const f of readdirSync(metaDir).filter((x) => /^\d+-chapter\.yaml$/.test(x))) {
	const chapter = String(Number(f.match(/^(\d+)/)[1]));
	const rows = ev.rows.filter((r) => r.chapter === chapter);
	const embeds = ev.embeds.filter((e) => e.chapter === chapter);
	if (!rows.length && !embeds.length) continue;

	const byFile = new Map();
	for (const r of rows) {
		const k = r.file;
		const cur = byFile.get(k) ?? { file: k, claim_class: r.claim_class, evidence_scope: r.evidence_scope, claims: 0, failing: 0 };
		cur.claims++;
		if (r.runtime !== "pass" || r.compile !== "pass") cur.failing++;
		byFile.set(k, cur);
	}

	const lines = [KEY, `  pi_version: ${ev.versions["pi-coding-agent"]}`, "  generated_by: examples/sync-metadata.mjs", "  tests:"];
	if (!byFile.size) lines[lines.length - 1] = "  tests: []";
	for (const t of [...byFile.values()].sort((a, b) => a.file.localeCompare(b.file))) {
		lines.push(`  - file: ${t.file}`, `    claim_class: ${t.claim_class}`, `    evidence_scope: ${t.evidence_scope}`, `    claims: ${t.claims}`, `    failing: ${t.failing}`);
	}
	const shown = embeds.filter((e) => e.kind !== "documented-not-run" && e.kind !== "illustrative");
	lines.push(shown.length ? "  code_shown:" : "  code_shown: []");
	for (const e of shown) lines.push(`  - kind: ${e.kind}`, `    source: ${e.source}`);
	const notRun = embeds.filter((e) => e.kind === "documented-not-run").length;
	const illus = embeds.filter((e) => e.kind === "illustrative").length;
	lines.push(`  documented_not_run: ${notRun}`, `  illustrative: ${illus}`);

	let text = readFileSync(join(metaDir, f), "utf8").replace(/\r\n/g, "\n");
	const at = text.indexOf("\n" + KEY);
	if (at !== -1) text = text.slice(0, at + 1);
	if (!text.endsWith("\n")) text += "\n";
	writeFileSync(join(metaDir, f), text + lines.join("\n") + "\n");
	touched++;
}
console.log(`metadata: executable_evidence written to ${touched} record(s)`);
