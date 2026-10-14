import { test } from "node:test";
import assert from "node:assert/strict";
import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";

type H = Awaited<ReturnType<typeof makeSession>>;

/** Have the scripted model call the real bash tool, and return the tool result text. */
async function viaModel(h: H, command: string): Promise<{ text: string; isError: boolean }> {
	h.faux.setResponses([fauxAssistantMessage([fauxToolCall("bash", { command })], { stopReason: "toolUse" }), fauxAssistantMessage([fauxText("done")])]);
	await h.session.prompt("run it");
	const r = [...h.session.messages].reverse().find((m) => m.role === "toolResult") as any;
	return { text: r.content.map((c: any) => c.text ?? "").join(""), isError: r.isError };
}

test("session variables are injected into the model's bash tool", async () => {
	const h = await makeSession({ extensions: [], persist: true });
	const { text } = await viaModel(h, 'echo "id=$PI_SESSION_ID provider=$PI_PROVIDER model=$PI_MODEL level=$PI_REASONING_LEVEL file=$PI_SESSION_FILE"');
	assert.match(text, new RegExp(`id=${h.session.sessionManager.getSessionId()}`));
	assert.match(text, /provider=faux/);
	assert.match(text, /level=off/);
	assert.ok(text.includes(h.session.sessionManager.getSessionFile()!.split("\\").join("/")) || /file=\S+\.jsonl/.test(text), "PI_SESSION_FILE is the JSONL path");
	h.dispose();
});

test("PI_SESSION_FILE is unset for an ephemeral session, which is how a script can tell", async () => {
	const h = await makeSession({ extensions: [] });
	const { text } = await viaModel(h, 'echo "file=[$PI_SESSION_FILE]"');
	assert.match(text, /file=\[\]/);
	h.dispose();
});

test("the values are resolved when each command starts, so a change of thinking level shows up in the next command", async () => {
	const h = await makeSession({ extensions: [], fauxOptions: { models: [{ id: "faux-thinker", reasoning: true }] } });
	h.session.setThinkingLevel("low");
	assert.match((await viaModel(h, "echo level=$PI_REASONING_LEVEL")).text, /level=low/);
	h.session.setThinkingLevel("high");
	assert.match((await viaModel(h, "echo level=$PI_REASONING_LEVEL")).text, /level=high/, "no restart needed");
	h.dispose();
});

test("session variables are NOT injected into a user-entered ! command", async () => {
	const h = await makeSession({ extensions: [] });
	const user = await h.session.executeBash('echo "id=[$PI_SESSION_ID]"');
	assert.match(user.output, /id=\[\]/, "a check you run by hand sees a different environment from the model's");
	const model = await viaModel(h, 'echo "id=[$PI_SESSION_ID]"');
	assert.doesNotMatch(model.text, /id=\[\]/);
	h.dispose();
});

test("shellCommandPrefix runs before every command, for the model's tool and for ! commands", async () => {
	const h = await makeSession({ extensions: [], settings: { shellCommandPrefix: "export FROM_PREFIX=yes" } });
	assert.match((await viaModel(h, "echo prefix=$FROM_PREFIX")).text, /prefix=yes/);
	assert.match((await h.session.executeBash("echo prefix=$FROM_PREFIX")).output, /prefix=yes/);
	h.dispose();
});

test("aliases: absent in a non-interactive shell, present once the prefix enables and sources them", async () => {
	const none = await makeSession({ extensions: [] });
	assert.equal((await viaModel(none, "myalias")).isError, true, "an alias that lives in an interactive profile does not exist here");
	none.dispose();

	const prefix = "shopt -s expand_aliases\nalias myalias='echo aliased-ok'";
	const h = await makeSession({ extensions: [], settings: { shellCommandPrefix: prefix } });
	const r = await viaModel(h, "myalias");
	assert.match(r.text, /aliased-ok/);
	h.dispose();
});

test("a non-zero exit is reported by the built-in tool as a result the model can read", async () => {
	const h = await makeSession({ extensions: [] });
	const r = await viaModel(h, "echo about-to-fail; exit 3");
	assert.match(r.text, /about-to-fail/);
	assert.match(r.text, /3/, "the exit code is in the result");
	h.dispose();
});
