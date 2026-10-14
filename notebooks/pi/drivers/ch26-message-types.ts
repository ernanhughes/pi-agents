// Chapter 26 - Message Types
// Compile-time: the chapter's declarations match the exported ones (assert-equal.ts is
// checked by tsc). Static: read the 1.0.4 SystemMessage declaration and check whether a
// `replace` member exists there, and whether the shipped JavaScript reads one.

import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

const PI_AI = join(process.cwd(), "node_modules", "@earendil-works", "pi-ai", "dist");
const PI_CODING = join(process.cwd(), "node_modules", "@earendil-works", "pi-coding-agent", "dist");

function jsFiles(dir: string): { file: string; content: string }[] {
	const out: { file: string; content: string }[] = [];
	try {
		for (const f of readdirSync(dir)) {
			if (f.endsWith(".js")) out.push({ file: f, content: readFileSync(join(dir, f), "utf8") });
		}
	} catch {}
	return out;
}

// SystemMessage declaration in pi-ai's types.d.ts
const typesDts = readFileSync(join(PI_AI, "types.d.ts"), "utf8");
const sysMatch = typesDts.match(/export interface SystemMessage \{[\s\S]*?\n\}/);
const systemMessageDeclaration = sysMatch ? sysMatch[0] : "";
const declarationHasReplace = /\breplace\s*[?:]/.test(systemMessageDeclaration);

// Does any shipped JavaScript read a `replace` member on a system message?
const allJs = [...jsFiles(PI_AI), ...jsFiles(PI_CODING)];
const jsReadsReplace = allJs
	.filter(({ content }) => /SystemMessage[\s\S]{0,160}?\.replace\s*\(/.test(content))
	.map(({ file }) => file);

// Confirm the four roles the chapter declares are the four in the exported union.
const declaredSrc = readFileSync(new URL("../ch26-message-types/declared.ts", import.meta.url), "utf8");
const declaredRoles = ["system", "user", "assistant", "toolResult"].filter((r) => declaredSrc.includes(`role: "${r}"`));

console.log(JSON.stringify({
	systemMessageDeclaration: systemMessageDeclaration.split("\n").map((l) => l.trim()).join(" "),
	declarationHasReplace,
	jsFilesScanned: allJs.length,
	jsReadsReplace,
	declaredRoles,
}));