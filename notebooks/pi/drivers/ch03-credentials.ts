// Chapter 3 part 1 - which credential source wins.
//
// Pi's real ModelRuntime, pointed at real auth.json / models.json files written
// into a fresh temporary directory. The winner is identified by the literal string
// that source contributed, so a default can never be mistaken for a resolution.

import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { ModelRuntime } from "@earendil-works/pi-coding-agent";

const ENV = { ANTHROPIC_API_KEY: "ENV-KEY" };
type Sources = { runtime?: string; auth?: string; models?: string; env?: boolean };

async function resolved(src: Sources) {
	const dir = mkdtempSync(join(tmpdir(), "pinb-ch03-"));
	if (src.auth) writeFileSync(join(dir, "auth.json"), JSON.stringify({ anthropic: { type: "api_key", key: src.auth } }));
	if (src.models) writeFileSync(join(dir, "models.json"), JSON.stringify({ providers: { anthropic: { apiKey: src.models } } }));
	const rt = await ModelRuntime.create({
		authPath: join(dir, "auth.json"),
		modelsPath: src.models ? join(dir, "models.json") : null,
		refreshOnCreate: false,
	});
	if (src.runtime) await rt.setRuntimeApiKey("anthropic", src.runtime);
	const r: any = await rt.getAuth("anthropic", { env: src.env ? ENV : {} } as any);
	return (r?.auth?.apiKey ?? null) as string | null;
}

// The notebook's exercise supplies one ladder through the environment.
const candidate: [string, Sources][] = process.env.NB_LADDER ? JSON.parse(process.env.NB_LADDER) : [];

const all: Sources = { runtime: "RUNTIME", auth: "STORED", models: "MODELS", env: true };
const candidate: [string, Sources][] = process.env.NB_LADDER ? JSON.parse(process.env.NB_LADDER) : [];

const resolvedLadder: [string, string | null][] = candidate.length
	? []
	: [
			["all four sources", await resolved(all)],
			["drop the runtime key", await resolved({ ...all, runtime: undefined })],
			["drop auth.json too", await resolved({ ...all, runtime: undefined, auth: undefined })],
			["drop models.json too", await resolved({ ...all, runtime: undefined, auth: undefined, models: undefined })],
			["drop the environment too", await resolved({})],
		];
for (const [label, src] of candidate) resolvedLadder.push([label, await resolved(src)]);

// A model that parses but cannot be selected until its provider authenticates.
const dir = mkdtempSync(join(tmpdir(), "pinb-ch03-avail-"));
const write = (apiKey?: string) =>
	writeFileSync(
		join(dir, "models.json"),
		JSON.stringify({
			providers: {
				mylocal: {
					baseUrl: "http://localhost:1/v1",
					api: "openai-completions",
					...(apiKey ? { apiKey } : {}),
					models: [{ id: "my-model" }],
				},
			},
		}),
	);
const probe = async () => {
	const rt = await ModelRuntime.create({ authPath: join(dir, "auth.json"), modelsPath: join(dir, "models.json"), refreshOnCreate: false });
	return {
		modelLoads: Boolean(rt.getModel("mylocal", "my-model")),
		available: (await rt.getAvailable("mylocal")).map((m: any) => m.id),
	};
};
write();
const withoutKey = await probe();
write("ollama");
const withDummyKey = await probe();

console.log(JSON.stringify({ ladder: resolvedLadder, withoutKey, withDummyKey }));