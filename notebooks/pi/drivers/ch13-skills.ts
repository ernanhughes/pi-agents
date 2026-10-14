// Chapter 13 - what a skill contributes to the model's context.
//
// The question is narrow and checkable: does the provider's system prompt carry the
// skill's name, description and path, and does its body stay out until somebody
// asks for it?

import { makeSession, systemPromptSeenByProvider } from "../harness/session.ts";

const SKILL = (name: string, description: string | null, body: string, extra = "") =>
	`---\nname: ${name}\n${description === null ? "" : `description: ${description}\n`}${extra}---\n\n${body}\n`;

/**
 * Skills installed on the machine running the notebook are discovered too - the
 * chapter says so, and it is why the book's own test filters to its own fixtures.
 * We do the same: only names this driver created are reported.
 */
const OURS = new Set(["review-guard", "no-desc", "manual-only", "nested-skill", "review"]);

async function withSkills(files: Record<string, string>) {
	const h = await makeSession({ extensions: [], agentFiles: files, resourceOptions: { noSkills: false } });
	const prompt = await systemPromptSeenByProvider(h);
	const discovered = h.session.resourceLoader
		.getSkills()
		.skills.map((s: any) => s.name)
		.filter((n: string) => OURS.has(n));
	h.dispose();
	return { prompt, discovered };
}

const loaded = await withSkills({
	"skills/review-guard/SKILL.md": SKILL("review-guard", "Reviews changed code. Use when reviewing a diff.", "SECRET-BODY-TEXT"),
});

const noDescription = await withSkills({
	"skills/no-desc/SKILL.md": SKILL("no-desc", null, "SECRET-BODY-TEXT"),
});

const manualOnly = await withSkills({
	"skills/manual/SKILL.md": SKILL(
		"manual-only",
		"Never call this yourself.",
		"MANUAL-BODY-TEXT",
		"disable-model-invocation: true\n",
	),
});

const nested = await withSkills({
	"skills/group/inner/SKILL.md": SKILL("nested-skill", "Discovered recursively.", "NESTED-BODY-TEXT"),
});

const collision = await withSkills({
	"skills/a/SKILL.md": SKILL("review", "FIRST description.", "FIRST-BODY"),
	"skills/b/SKILL.md": SKILL("review", "SECOND description.", "SECOND-BODY"),
});

// /skill:name loads the body as the request, with arguments appended.
async function explicitLoad() {
	const h = await makeSession({
		extensions: [],
		agentFiles: { "skills/manual/SKILL.md": SKILL("manual-only", "Never call this yourself.", "MANUAL-BODY-TEXT", "disable-model-invocation: true\n") },
		resourceOptions: { noSkills: false },
	});
	let sent = "";
	h.faux.appendResponses([
		(ctx: any) => {
			const u = (ctx.messages as any[]).filter((m: any) => m.role === "user").at(-1);
			sent = [].concat(u.content).map((b: any) => b.text ?? b).join("");
			return fauxAssistantMessage([fauxText("ok")]);
		},
	]);
	await h.session.prompt("/skill:manual-only src/auth only");
	h.dispose();
	return sent;
}

console.log(
	JSON.stringify({
		loaded: {
			carriesName: loaded.prompt.includes("review-guard"),
			carriesDescription: loaded.prompt.includes("Reviews changed code."),
			carriesPath: /SKILL\.md/.test(loaded.prompt),
			carriesBody: loaded.prompt.includes("SECRET-BODY-TEXT"),
			discovered: loaded.discovered,
		},
		noDescription: {
			mentionsName: noDescription.prompt.includes("no-desc"),
			discovered: noDescription.discovered,
		},
		manualOnly: {
			mentionsName: manualOnly.prompt.includes("manual-only"),
			discovered: manualOnly.discovered,
		},
		nested: { mentionsName: nested.prompt.includes("nested-skill"), discovered: nested.discovered },
		collision: {
			discovered: collision.discovered,
			first: collision.prompt.includes("FIRST description."),
			second: collision.prompt.includes("SECOND description."),
		},
		explicitLoad: await explicitLoad(),
	}),
);