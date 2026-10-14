// Chapter 7 - how settings merge, through Pi's own SettingsManager over real files.
//
// Nothing here re-implements a resolution rule. `SettingsManager.create` is Pi's,
// pointed at two real settings.json files: one in the agent directory (user scope)
// and one in <cwd>/.pi (project scope).

import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { SettingsManager } from "@earendil-works/pi-coding-agent";

function files(user: object, project: object | null, trusted = true) {
	const root = mkdtempSync(join(tmpdir(), "pinb-ch07-"));
	const agentDir = join(root, "agent");
	const cwd = join(root, "repo");
	mkdirSync(agentDir, { recursive: true });
	mkdirSync(join(cwd, ".pi"), { recursive: true });
	writeFileSync(join(agentDir, "settings.json"), JSON.stringify(user));
	if (project) writeFileSync(join(cwd, ".pi", "settings.json"), JSON.stringify(project));
	return SettingsManager.create(cwd, agentDir, { projectTrusted: trusted } as any);
}

const row = (label: string, s: any) => ({
	label,
	defaultTools: s.getDefaultTools(),
	reserveTokens: s.getCompactionSettings().reserveTokens,
	keepRecentTokens: s.getCompactionSettings().keepRecentTokens,
	skillPaths: s.getSkillPaths(),
	defaultProjectTrust: s.getDefaultProjectTrust(),
});

const USER = {
	defaultTools: ["read", "bash", "edit", "write"],
	compaction: { reserveTokens: 1000, keepRecentTokens: 5000 },
	skills: ["~/shared-skills"],
};

// The notebook's exercise supplies one project list through the environment so it
// never has to edit this file. NB_PROJECT unset means: report the four shapes.
const candidate: string[] | null = process.env.NB_PROJECT ? JSON.parse(process.env.NB_PROJECT) : null;

const grammar = candidate
	? [{ label: `project: ${JSON.stringify(candidate)}`, ...row("", files(USER, { defaultTools: candidate })) }]
	: [
			row("project: [+grep, +find, +ls]", files(USER, { defaultTools: ["+grep", "+find", "+ls"] })),
			row("project: [read, powershell]", files(USER, { defaultTools: ["read", "powershell"] })),
			row("project: [read, bash, -bash, +grep]", files(USER, { defaultTools: ["read", "bash", "-bash", "+grep"] })),
			row("project: [-bash]", files(USER, { defaultTools: ["-bash"] })),
		];

const out: any = {
	defaultToolsGrammar: grammar,
	scalars: {
		bothSet: row("user 1000 / project 2000", files(USER, { compaction: { reserveTokens: 2000 } })),
		projectTrustGrantedLater: (() => {
			const s = files(USER, { compaction: { reserveTokens: 2000 } }, false);
			const before = row("untrusted", s);
			s.setProjectTrusted(true);
			return { before, after: row("trusted afterwards", s) };
		})(),
		defaultProjectTrustCannotComeFromProject: row(
			"project says always",
			files(USER, { defaultProjectTrust: "always" }),
		),
	},
};

console.log(JSON.stringify(out));