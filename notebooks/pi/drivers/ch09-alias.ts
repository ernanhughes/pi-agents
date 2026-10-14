// Chapter 9 - the alias case, which is the chapter's title.
//
// An alias defined in an operator's interactive profile is absent from Pi's fresh
// non-interactive shell, and present once shellCommandPrefix enables aliases.

import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";
import { bashPath, bashWorks } from "../harness/bash.ts";

async function viaModel(h: any, command: string) {
	h.faux.setResponses([
		fauxAssistantMessage([fauxToolCall("bash", { command })], { stopReason: "toolUse" }),
		fauxAssistantMessage([fauxText("done")]),
	]);
	await h.session.prompt("run it");
	const last = h.session.messages.filter((m: any) => m.role === "toolResult").at(-1) as any;
	return { text: last.content[0].text.trim(), isError: last.isError };
}

async function attempt(command: string, options: any = {}) {
	const h = await makeSession({ extensions: [], ...options });
	const r = await viaModel(h, command);
	h.dispose();
	return r;
}

const shell = { bashPath: bashPath(), bashWorks: bashWorks() };

// The notebook's exercise supplies COMMAND, PREFIX and PLAIN_PREFIX through the
// environment, so it never has to edit this file. Unset means: the chapter's case.
const COMMAND = process.env.NB_COMMAND ?? "myalias";
const with_ = (prefix?: string) => (prefix ? { settings: { shellCommandPrefix: prefix } } : {});

const withoutPrefix = await attempt(COMMAND, with_(process.env.NB_PLAIN_PREFIX));
const withPrefix = await attempt(
	COMMAND,
	with_(process.env.NB_PREFIX ?? "shopt -s expand_aliases\nalias myalias='echo aliased-ok'"),
);

console.log(JSON.stringify({ shell, command: COMMAND, withoutPrefix, withPrefix }));