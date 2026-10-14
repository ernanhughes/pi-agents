// Chapter 9 - two entry points into the same shell.
//
// The model's `bash` tool and the operator's `!` command are different callers with
// different environments. This driver runs the same command string through both and
// compares what each one saw.

import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";

const SESSION_VARS =
	'echo "id=$PI_SESSION_ID provider=$PI_PROVIDER model=$PI_MODEL level=$PI_REASONING_LEVEL file=$PI_SESSION_FILE"';

async function viaModel(h: any, command: string) {
	h.faux.setResponses([
		fauxAssistantMessage([fauxToolCall("bash", { command })], { stopReason: "toolUse" }),
		fauxAssistantMessage([fauxText("done")]),
	]);
	await h.session.prompt("run it");
	const last = h.session.messages.filter((m: any) => m.role === "toolResult").at(-1) as any;
	return { text: last.content[0].text.trim(), isError: last.isError };
}

async function compare(label: string, command: string, options: any = {}) {
	const h = await makeSession({ extensions: [], persist: true, ...options });
	const model = await viaModel(h, command);
	const bang = await h.session.executeBash(command);
	const result = {
		label,
		viaModel: model,
		viaBang: { output: bang.output.trim() },
		sameOutput: model.text === bang.output.trim(),
	};
	h.dispose();
	return result;
}

const probe = (text: string) => (/id=\S+/.exec(text)?.[0] ?? "(no id)");
const file = (text: string) => (/file=\S*/.exec(text)?.[0] ?? "(no file)");

const rows: any[] = [];
{
	const h = await makeSession({ extensions: [], persist: true });
	const model = await viaModel(h, SESSION_VARS);
	const bang = await h.session.executeBash(SESSION_VARS);
	// Booleans are computed here, before the notebook masks machine paths, so the
	// assertions do not depend on a path surviving masking.
	rows.push({
		label: "both entry points, session variables",
		id: probe(model.text),
		file: file(model.text),
		bangId: probe(bang.output.trim()),
		bangFile: file(bang.output.trim()),
		modelSawSessionId: /id=[0-9a-f-]{8,}/.test(model.text),
		modelSawSessionFile: /\.jsonl/.test(model.text),
		bangSawSessionId: /id=[0-9a-f-]{8,}/.test(bang.output),
		bangSawSessionFile: false,
	});
	h.dispose();
}

rows.push(await compare("a plain echo", "echo hello-from-both"));

// A non-zero exit is data in a successful result, not a failed tool.
{
	const h = await makeSession({ extensions: [], persist: true });
	const model = await viaModel(h, "echo about-to-fail; exit 3");
	h.dispose();
	rows.push({ label: "a command that exits 3", isError: model.isError, text: model.text });
}

// shellCommandPrefix runs for both entry points.
rows.push(
	await compare("with shellCommandPrefix set", "echo $FROM_PREFIX", {
		settings: { shellCommandPrefix: "export FROM_PREFIX=yes" },
	}),
);

console.log(JSON.stringify(rows));