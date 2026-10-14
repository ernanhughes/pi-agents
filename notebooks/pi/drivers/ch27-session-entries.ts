// Chapter 27 - The Session File Format
// A real session file parsed directly; the entry-id chain; both timestamp formats; the chapter's own reader run as a child process; the declaration check.

import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { fauxAssistantMessage, fauxText } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";

const reader = fileURLToPath(new URL("../ch27-session-entries/read-session.ts", import.meta.url));

async function writtenSession() {
	const h = await makeSession({ extensions: [], persist: true });
	h.faux.setResponses([fauxAssistantMessage([fauxText("hello back")])]);
	await h.session.prompt("hello");
	return { h, file: h.session.sessionManager.getSessionFile()! };
}

const { h, file } = await writtenSession();
const text = readFileSync(file, "utf8");
const rows = text.trim().split("\n").map((l) => JSON.parse(l));

const header = rows[0];
const entries = rows.slice(1);
const messageEntry = entries.find((e) => e.type === "message");
const baseFieldsOk = entries.every((e) => "id" in e && "parentId" in e && typeof e.timestamp === "string");

// The entry-id chain: for a linear conversation, each parent is the entry before.
const linearChain = entries.every((e, i) => (i === 0 ? e.parentId === null : e.parentId === entries[i - 1].id));

// Both timestamp formats.
const isoOnEntry = /^\d{4}-\d\d-\d\dT/.test(messageEntry?.timestamp ?? "");
const unixOnMessage = typeof messageEntry?.message?.timestamp === "number";

// The chapter's reader run as a child process.
const r = spawnSync(process.execPath, [reader, file], { encoding: "utf8" });

h.dispose();

console.log(JSON.stringify({
	header: { type: header?.type, version: header?.version, hasParentId: "parentId" in header },
	entries: {
		count: entries.length,
		types: entries.map((e) => e.type),
		baseFieldsOk,
		linearChain,
	},
	timestamps: { isoOnEntry, unixOnMessage },
	reader: { status: r.status, stdout: r.stdout, hasSessionLine: /^Session v\d+: /m.test(r.stdout), hasUser: /user: .*hello/.test(r.stdout), hasAssistant: /assistant: .*hello back/.test(r.stdout) },
}));