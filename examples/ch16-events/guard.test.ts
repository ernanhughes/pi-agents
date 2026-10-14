import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { join } from "node:path";
import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";
import guard from "./guard.ts";
import guardStatus from "./guard-status.ts";

const bash = (command: string) =>
	fauxAssistantMessage([fauxToolCall("bash", { command })], { stopReason: "toolUse" });

async function run(ext: typeof guard, command: string) {
	const h = await makeSession({ extensions: [ext] });
	h.faux.setResponses([bash(command), fauxAssistantMessage([fauxText("done")])]);
	await h.session.prompt("go");
	const result = h.session.messages.find((m) => m.role === "toolResult") as any;
	return { h, result };
}

test("with no UI to ask, the guard refuses a force push and the command never runs", async () => {
	const { h, result } = await run(guard, "touch ran.flag && git push --force origin main");
	assert.equal(result.isError, true);
	assert.match(result.content[0].text, /Guard blocked/);
	assert.equal(existsSync(join(h.cwd, "ran.flag")), false, "a blocked call must have no effect");
	h.dispose();
});

test("an ordinary command is left alone and does run", async () => {
	const { h, result } = await run(guard, "touch ran.flag");
	assert.equal(result.isError, false);
	assert.equal(existsSync(join(h.cwd, "ran.flag")), true);
	h.dispose();
});

test("the guard also covers reset --hard", async () => {
	const { h, result } = await run(guard, "git reset --hard HEAD~1");
	assert.equal(result.isError, true);
	h.dispose();
});

test("the multi-hook version blocks with a reason the model can act on", async () => {
	const { h, result } = await run(guardStatus, "touch ran.flag && git push -f origin main");
	assert.equal(result.isError, true);
	assert.match(result.content[0].text, /--force-with-lease/);
	assert.equal(existsSync(join(h.cwd, "ran.flag")), false);
	h.dispose();
});

test("a tool_call handler that throws blocks the tool as a fail-safe", async () => {
	const throwing: typeof guard = (pi) => {
		pi.on("tool_call", async () => {
			throw new Error("handler bug");
		});
	};
	const { h, result } = await run(throwing, "touch ran.flag");
	assert.equal(result.isError, true);
	assert.equal(existsSync(join(h.cwd, "ran.flag")), false, "the failure must fail closed");
	h.dispose();
});
