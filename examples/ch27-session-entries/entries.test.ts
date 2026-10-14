import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { fauxAssistantMessage, fauxText } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";

const reader = fileURLToPath(new URL("./read-session.ts", import.meta.url));

async function writtenSession() {
	const h = await makeSession({ extensions: [], persist: true });
	h.faux.setResponses([fauxAssistantMessage([fauxText("hello back")])]);
	await h.session.prompt("hello");
	return { h, file: h.session.sessionManager.getSessionFile()! };
}

test("the file is JSONL with a header first, then entries linked by id and parentId", async () => {
	const { h, file } = await writtenSession();
	const rows = readFileSync(file, "utf8").trim().split("\n").map((l) => JSON.parse(l));
	assert.equal(rows[0].type, "session");
	assert.equal(rows[0].version, 3, "the current session version on 1.0.2");
	assert.equal(rows[0].parentId, undefined, "the header is not part of the tree");
	for (const e of rows.slice(1)) assert.ok("id" in e && "parentId" in e && typeof e.timestamp === "string", `${e.type} has the base fields`);
	h.dispose();
});

test("two timestamps, two formats: ISO on the entry, Unix milliseconds on the message", async () => {
	const { h, file } = await writtenSession();
	const msg = readFileSync(file, "utf8").trim().split("\n").map((l) => JSON.parse(l)).find((e) => e.type === "message");
	assert.match(msg.timestamp, /^\d{4}-\d\d-\d\dT/);
	assert.equal(typeof msg.message.timestamp, "number");
	h.dispose();
});

test("the reading program in the chapter runs against a real session file", async () => {
	const { h, file } = await writtenSession();
	const r = spawnSync(process.execPath, [reader, file], { encoding: "utf8" });
	assert.equal(r.status, 0, r.stderr);
	assert.match(r.stdout, /^Session v3: /m);
	assert.match(r.stdout, /user: .*hello/);
	assert.match(r.stdout, /assistant: .*hello back/);
	assert.match(r.stdout, /Model: faux\//);
	h.dispose();
});
