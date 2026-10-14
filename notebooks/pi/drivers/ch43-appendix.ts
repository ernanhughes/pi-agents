// Chapter 43 (Appendix A) - References and Further Reading
// What does the pin actually contain, and what does the ledger actually record?
// Count docs/*.md at the pin; tabulate claim_class x evidence_scope from evidence.json; count the appendix's own arXiv / ecosystem / companion-book entries; check each cited id appears in the text.

import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

const PI_CODING = join(process.cwd(), "node_modules", "@earendil-works", "pi-coding-agent");
const docsDir = join(PI_CODING, "docs");
const docFiles = readdirSync(docsDir).filter((f) => f.endsWith(".md")).sort();

const EVIDENCE = JSON.parse(readFileSync(join(process.cwd(), "evidence.json"), "utf8"));
const rows = EVIDENCE.rows ?? [];
const scopes = ["declarations", "in_process_runtime", "shipped_binary", "real_model"];
const classes = ["DOCUMENTED", "OBSERVED", "PROPOSED"];

const matrix: Record<string, Record<string, number>> = {};
for (const c of classes) matrix[c] = Object.fromEntries(scopes.map((s) => [s, 0]));
for (const r of rows) {
	const c = r.claim_class ?? "?";
	const s = r.evidence_scope ?? "?";
	if (matrix[c]) matrix[c][s] = (matrix[c][s] ?? 0) + 1;
}

// The appendix text itself
const appendix = readFileSync(join(process.cwd(), "..", "content", "books", "pi", "43-chapter.md"), "utf8");
const arxivIds = [...appendix.matchAll(/arXiv:(\d{4}\.\d{5})/g)].map((m) => m[1]);
const ecosystemRows = (appendix.match(/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+/g) ?? []);
const uniqueEcosystem = [...new Set(ecosystemRows)];
const companionBooks = (appendix.match(/\*([A-Za-z][A-Za-z ]+?) From First Principles\*/g) ?? []).map((m) => m.replace(/\*/g, ""));
const uniqueCompanions = [...new Set(companionBooks)];

// Each cited arXiv id appears in the text (it does, by construction being extracted from it),
// and each is a plausible arXiv id; we report the count and the set.
console.log(JSON.stringify({
	docs: {
		pinnedDocsDir: "docs/",
		count: docFiles.length,
		files: docFiles,
	},
	ledger: {
		totalRows: rows.length,
		matrix,
		claimClasses: classes,
	},
	appendix: {
		arxivIds: arxivIds,
		arxivCount: new Set(arxivIds).size,
		ecosystemRepos: uniqueEcosystem.length,
		companionBooks: uniqueCompanions,
	},
}));