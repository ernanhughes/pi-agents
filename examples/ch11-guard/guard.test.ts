import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { join } from "node:path";
import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession, UiRecorder } from "../harness/session.ts";
import guard from "./guard.ts";
import original from "./guard-original.ts";

async function run(ext: typeof guard, command: string, ui?: UiRecorder) {
	const h = await makeSession({ extensions: [ext], ui });
	h.faux.setResponses([fauxAssistantMessage([fauxToolCall("bash", { command })], { stopReason: "toolUse" }), fauxAssistantMessage([fauxText("done")])]);
	await h.session.prompt("go");
	return { h, result: h.session.messages.find((m) => m.role === "toolResult") as any };
}

test("regression: the first version of this guard missed a plain `git push`", async () => {
	const ui = new UiRecorder();
	await run(original, "git push origin main", ui);
	assert.equal(ui.confirms.length, 0, "the (^|\s) pattern needs whitespace before git, and the command begins with a quote");
	const compound = new UiRecorder();
	await run(original, "cd x && git push origin main", compound);
	assert.equal(compound.confirms.length, 1, "which is why it appeared to work when tested with a compound command");
});

test("the fixed guard asks about a plain git push, and a person can allow or refuse", async () => {
	for (const [answer, blocked] of [[true, false], [false, true]] as const) {
		const ui = new UiRecorder();
		ui.confirmAnswers = [answer];
		// `echo git push` matches the pattern but is harmless, so allowing it can succeed.
		const { h, result } = await run(guard, "echo git push origin main", ui);
		assert.equal(ui.confirms.length, 1);
		assert.equal(result.isError, blocked);
		h.dispose();
	}
});

test("anything under migrations/ is confirmed, and an ordinary command is not", async () => {
	const ui = new UiRecorder();
	ui.confirmAnswers = [false];
	const { h, result } = await run(guard, "touch migrations/001.sql", ui);
	assert.equal(result.isError, true);
	assert.equal(existsSync(join(h.cwd, "migrations", "001.sql")), false);
	h.dispose();

	const quiet = new UiRecorder();
	const ok = await run(guard, "echo hello", quiet);
	assert.equal(quiet.confirms.length, 0);
	assert.equal(ok.result.isError, false);
	ok.h.dispose();
});

test("with no UI to ask, the safe answer is to refuse", async () => {
	const { h, result } = await run(guard, "git push origin main");
	assert.equal(result.isError, true);
	h.dispose();
});

// "No force pushes" is an unconditional prohibition. The earlier version of this
// guard treated every git push as a confirmation, so a person who said yes to a
// force push got one. That satisfies the migrations requirement and fails this one.
test("a force push is refused outright, and no confirmation is offered", async () => {
	for (const command of ["git push --force origin main", "git push -f origin main", "git commit -m x && git push --force-with-lease"]) {
		const ui = new UiRecorder();
		ui.confirmAnswers = [true]; // a person who would say yes, if asked
		const { h, result } = await run(guard, command, ui);
		assert.equal(ui.confirms.length, 0, `"${command}" must not reach a confirmation prompt`);
		assert.equal(result.isError, true, `"${command}" must be blocked`);
		assert.match(result.content[0].text, /Force pushes/);
		h.dispose();
	}
});

test("an ordinary push is still a confirmation, so the two requirements stay distinct", async () => {
	const ui = new UiRecorder();
	ui.confirmAnswers = [true];
	// `echo git push` matches the push pattern but succeeds as a command, so the
	// only thing that can make the result an error is the guard.
	const { h, result } = await run(guard, "echo git push origin main", ui);
	assert.equal(ui.confirms.length, 1, "a plain push asks");
	assert.equal(result.isError, false, "and is allowed once the answer is yes");
	h.dispose();
});
