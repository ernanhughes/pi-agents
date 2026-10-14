// Chapter 31 - one agent, three drivers: print, JSON and RPC on the shipped binary.
//
// The chapter's claim is bounded: the same agent produces the same answer and the
// same lifecycle events behind each interface, and what differs is the observer
// and the failure contract. Every assertion below is on a boundary - the exit
// status, a file the tool would create, the presence or absence of a record
// family, the order of lifecycle events, the stop reason in the stream.

import { existsSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { RpcClient, runPi } from "../harness/cli.ts";

const SCRIPT = [{ tool: "bash", args: { command: "echo from-the-tool > ran.flag" } }, { text: "the answer is forty-two" }];
const FAIL = [{ error: "provider exploded" }];
const LIFECYCLE = new Set([
	"agent_start", "turn_start", "tool_execution_start", "tool_execution_end",
	"turn_end", "agent_end", "agent_settled",
]);

const workdir = () => mkdtempSync(join(tmpdir(), "pinb-ch31-"));
const jsonRecords = (stdout: string) => stdout.split("\n").filter(Boolean).map((l) => JSON.parse(l));
const kinds = (recs: any[]) => recs.map((r) => r.type).filter((t) => LIFECYCLE.has(t));
const finalText = (recs: any[]) => {
	const m = recs.filter((r) => r.type === "message_end" && r.message.role === "assistant").at(-1);
	return m?.message.content.filter((b: any) => b.type === "text").map((b: any) => b.text).join("") ?? "";
};
const stopReason = (recs: any[]) =>
	recs.find((r) => r.type === "message_end" && r.message.role === "assistant")?.message.stopReason;

async function rpc(script: any[]) {
	const c = new RpcClient({ script, cwd: workdir() });
	c.send({ id: "p1", type: "prompt", message: "go" });
	await c.waitFor((r) => r.type === "agent_settled");
	const exit = await c.close();
	return {
		records: c.records,
		exit,
		cwd: c.cwd,
		response: c.records.find((r) => r.type === "response" && r.id === "p1"),
	};
}

// ---------------------------------------------------------------- the success
const printCwd = workdir();
const jsonCwd = workdir();
const printOk = runPi({ script: SCRIPT, args: ["--print", "go"], cwd: printCwd });
const jsonOk = runPi({ script: SCRIPT, args: ["--mode", "json", "go"], cwd: jsonCwd });
const rpcOk = await rpc(SCRIPT);
const jsonRecs = jsonRecords(jsonOk.stdout);

const success = {
	print: {
		exit: printOk.status,
		stdoutLines: printOk.stdout.trim().split("\n").length,
		text: printOk.stdout.trim(),
		toolWroteFile: existsSync(join(printCwd, "ran.flag")),
		hasEvents: false,
		hasResponses: false,
	},
	json: {
		exit: jsonOk.status,
		records: jsonRecs.length,
		lifecycle: kinds(jsonRecs),
		text: finalText(jsonRecs),
		toolWroteFile: existsSync(join(jsonCwd, "ran.flag")),
		hasEvents: jsonRecs.length > 0,
		hasResponses: jsonRecs.some((r) => r.type === "response"),
	},
	rpc: {
		exit: rpcOk.exit,
		lifecycle: kinds(rpcOk.records),
		text: finalText(rpcOk.records),
		toolWroteFile: existsSync(join(rpcOk.cwd, "ran.flag")),
		disposition: rpcOk.response?.data?.disposition,
		hasEvents: rpcOk.records.some((r) => r.type !== "response"),
		hasResponses: rpcOk.records.some((r) => r.type === "response"),
		responseBeforeFirstEvent:
			rpcOk.records.findIndex((r) => r.id === "p1") < rpcOk.records.findIndex((r) => r.type === "agent_start"),
	},
};

// ---------------------------------------------------------------- the failure
const printBad = runPi({ script: FAIL, args: ["--print", "go"], cwd: workdir() });
const jsonBad = runPi({ script: FAIL, args: ["--mode", "json", "go"], cwd: workdir() });
const rpcBad = await rpc(FAIL);

const failure = {
	print: {
		exit: printBad.status,
		stdoutEmpty: printBad.stdout === "",
		messageOnStderr: /provider exploded/.test(printBad.stderr),
		streamStopReason: null as string | null,
	},
	json: {
		exit: jsonBad.status,
		streamStopReason: stopReason(jsonRecords(jsonBad.stdout)),
		messageInStream: /provider exploded/.test(jsonBad.stdout),
	},
	rpc: {
		promptCommandSucceeded: rpcBad.response?.success === true,
		disposition: rpcBad.response?.data?.disposition,
		streamStopReason: stopReason(rpcBad.records),
		commandFailed: rpcBad.response?.success === false,
	},
};

console.log(JSON.stringify({ success, failure }));