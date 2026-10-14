// Verifies that code shown in the manuscript is the code that is tested.
//
//   <!-- example: ch38-typed-step/step.ts -->   the fenced block that follows must
//                                               equal the file exactly.
//   <!-- excerpt: ch38-typed-step/step.ts -->   every non-blank line of the block must
//                                               appear in the file, in order.
//   <!-- declaration: ch26-message-types/declared.ts -->
//                                               like excerpt, ignoring a leading `export `. The file is
//                                               compared with the real exported types by assert-equal.ts.
//   <!-- documented-not-run -->                 real Pi API code that was not run (needs a credential, or
//                                               costs money). The prose must say so.
//   <!-- illustrative -->                       a fragment that is not meant to run on its own.
//
// Every typescript fence in a chapter must carry one of these markers.
//
// Hugo drops HTML comments from the rendered page, so the markers are invisible
// to readers.
import { readFileSync, readdirSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join, dirname } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const chapters = join(here, "..", "content", "books", "pi");
const norm = (s) => s.replace(/\r\n/g, "\n");
const lines = (s) => norm(s).split("\n").map((l) => l.trimEnd());

const FIX = process.argv.includes("--fix");
let checked = 0;
const failures = [];

for (const file of readdirSync(chapters).filter((f) => f.endsWith(".md"))) {
	let text = norm(readFileSync(join(chapters, file), "utf8"));
	let changed = false;
	// Every typescript fence must be marked, with a comment on the line before it.
	for (const f of text.matchAll(/(^|\n)(<!-- [^\n]*-->\n)?```(typescript|ts)\n/g)) {
		if (!f[2]) {
			const line = text.slice(0, f.index + f[1].length).split("\n").length;
			failures.push(`${file}:${line}: typescript block has no marker`);
		}
	}
	const re = /<!-- (example|excerpt|declaration): (\S+) -->\n```[a-z]*\n([\s\S]*?)\n```/g;
	for (const m of text.matchAll(re)) {
		const [, kind, path, block] = m;
		checked++;
		let source;
		try {
			source = norm(readFileSync(join(here, path), "utf8"));
		} catch {
			failures.push(`${file}: ${path} does not exist`);
			continue;
		}
		if (kind === "example") {
			if (lines(block).join("\n").trim() !== lines(source).join("\n").trim()) {
				if (FIX) {
					text = text.replace(m[0], m[0].replace(block, source.replace(/\n+$/, "")));
					changed = true;
				} else {
					failures.push(`${file}: block differs from ${path}`);
				}
			}
			continue;
		}
		const src = lines(source).map((l) => (kind === "declaration" ? l.replace(/^(\s*)export /, "$1") : l));
		let from = 0;
		for (const want of lines(block).filter((l) => l.trim() !== "")) {
			const at = src.findIndex((l, i) => i >= from && l.trim() === want.trim());
			if (at === -1) {
				failures.push(`${file}: excerpt line not found in order in ${path}: ${want.trim()}`);
				break;
			}
			from = at + 1;
		}
	}
	if (changed) writeFileSync(join(chapters, file), text);
}

if (failures.length) {
	console.error(failures.join("\n"));
	process.exit(1);
}
console.log(`checked ${checked} embedded block(s); all match their source`);
