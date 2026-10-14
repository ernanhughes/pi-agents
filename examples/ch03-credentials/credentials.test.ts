// Chapter 3: how a credential is resolved, through Pi's real model runtime and real files.
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { ModelRuntime } from "@earendil-works/pi-coding-agent";
import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";
import guard from "../ch16-events/guard.ts";

const ENV = { ANTHROPIC_API_KEY: "ENV-KEY" };

type Sources = { runtime?: string; auth?: string; models?: string; env?: boolean };

async function resolved(src: Sources): Promise<string | undefined> {
	const dir = mkdtempSync(join(tmpdir(), "pi-cred-"));
	if (src.auth) writeFileSync(join(dir, "auth.json"), JSON.stringify({ anthropic: { type: "api_key", key: src.auth } }));
	if (src.models) writeFileSync(join(dir, "models.json"), JSON.stringify({ providers: { anthropic: { apiKey: src.models } } }));
	const rt = await ModelRuntime.create({ authPath: join(dir, "auth.json"), modelsPath: src.models ? join(dir, "models.json") : null, refreshOnCreate: false });
	if (src.runtime) await rt.setRuntimeApiKey("anthropic", src.runtime);
	const r: any = await rt.getAuth("anthropic", { env: src.env ? ENV : {} } as any);
	return r?.auth?.apiKey;
}

test("the environment variable is used when nothing else is configured", async () => {
	assert.equal(await resolved({ env: true }), "ENV-KEY");
	assert.equal(await resolved({}), undefined, "and with nothing at all there is no credential");
});

test("a stored auth.json credential beats the environment variable", async () => {
	assert.equal(await resolved({ auth: "STORED", env: true }), "STORED");
});

test("an apiKey in models.json beats the environment variable", async () => {
	assert.equal(await resolved({ models: "MODELS", env: true }), "MODELS");
});

test("a runtime key beats everything", async () => {
	assert.equal(await resolved({ runtime: "RUNTIME", auth: "STORED", models: "MODELS", env: true }), "RUNTIME");
});

test("the first source that yields a credential wins, and the rest are never consulted: runtime, then auth.json, then models.json, then environment", async () => {
	const all = { runtime: "RUNTIME", auth: "STORED", models: "MODELS", env: true };
	assert.equal(await resolved(all), "RUNTIME");
	assert.equal(await resolved({ ...all, runtime: undefined }), "STORED");
	assert.equal(await resolved({ ...all, runtime: undefined, auth: undefined }), "MODELS");
	assert.equal(await resolved({ ...all, runtime: undefined, auth: undefined, models: undefined }), "ENV-KEY");
});

test("a model can load from models.json and still be unavailable until its provider has usable authentication", async () => {
	const dir = mkdtempSync(join(tmpdir(), "pi-avail-"));
	writeFileSync(join(dir, "models.json"), JSON.stringify({
		providers: { mylocal: { baseUrl: "http://localhost:1/v1", api: "openai-completions", models: [{ id: "my-model" }] } },
	}));
	const rt = await ModelRuntime.create({ authPath: join(dir, "auth.json"), modelsPath: join(dir, "models.json"), refreshOnCreate: false });
	assert.ok(rt.getModel("mylocal", "my-model"), "the entry parsed and the model exists");
	const before = (await rt.getAvailable("mylocal")).map((m) => m.id);
	assert.ok(!before.includes("my-model"), "but it is not in the available list: nothing authenticates it");

	writeFileSync(join(dir, "models.json"), JSON.stringify({
		providers: { mylocal: { baseUrl: "http://localhost:1/v1", api: "openai-completions", apiKey: "ollama", models: [{ id: "my-model" }] } },
	}));
	const rt2 = await ModelRuntime.create({ authPath: join(dir, "auth.json"), modelsPath: join(dir, "models.json"), refreshOnCreate: false });
	assert.ok((await rt2.getAvailable("mylocal")).map((m) => m.id).includes("my-model"), "a dummy key is enough to make it available");
});

// ---- provider configuration is not agent behaviour ----

const bash = (command: string) => fauxAssistantMessage([fauxToolCall("bash", { command })], { stopReason: "toolUse" });

async function transcriptShape(apiKey: string, env: Record<string, string>) {
	Object.assign(process.env, env);
	const h = await makeSession({ extensions: [guard], apiKey });
	h.faux.setResponses([bash("git push --force origin main"), bash("echo allowed"), fauxAssistantMessage([fauxText("done")])]);
	await h.session.prompt("go");
	const key = ((await h.modelRuntime.getAuth("faux")) as any)?.auth?.apiKey as string;
	const results = h.session.messages.filter((m) => m.role === "toolResult").map((m: any) => ({ isError: m.isError, text: m.content[0].text.slice(0, 40) }));
	const roles = h.session.messages.map((m) => m.role);
	h.dispose();
	return { key, shape: { results, roles, requests: h.faux.state.callCount } };
}

test("the same policy and the same script behave identically whichever way the provider's key is written", async () => {
	const literal = await transcriptShape("a-literal-key", {});
	const fromEnv = await transcriptShape("$PI_TEST_KEY", { PI_TEST_KEY: "from-the-environment" });
	const fromCommand = await transcriptShape("!echo from-a-command", {});

	// The three really were three different credentials, resolved three different ways...
	assert.equal(literal.key, "a-literal-key");
	assert.equal(fromEnv.key, "from-the-environment");
	assert.equal(fromCommand.key.trim(), "from-a-command");

	// ...and the agent did exactly the same thing under all of them.
	assert.deepEqual(fromEnv.shape, literal.shape);
	assert.deepEqual(fromCommand.shape, literal.shape);
	assert.equal(literal.shape.results[0].isError, true, "the guard blocked the force push under all three");
	assert.equal(literal.shape.results[1].isError, false);
});
