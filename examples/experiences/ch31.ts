// Chapter 31: the interface is not the agent. One scripted run through the SHIPPED binary,
// driven three ways, then the same failure three ways.
import { RpcClient, runPi, type Step } from "../harness/cli.ts";
import { Recorder, finish, type Observation, type Run, type Trace } from "./envelope.ts";

const OK: Step[] = [{ tool: "bash", args: { command: "echo from-the-tool" } }, { text: "the answer is forty-two" }];
const FAIL: Step[] = [{ error: "provider exploded" }];

const LIFECYCLE = new Set(["agent_start", "turn_start", "tool_execution_start", "tool_execution_end", "turn_end", "agent_end", "agent_settled"]);
const jsonRecords = (stdout: string) => stdout.trim().split("\n").filter(Boolean).map((l) => JSON.parse(l));
const finalText = (records: any[]) => {
	const m = records.filter((r) => r.type === "message_end" && r.message.role === "assistant").at(-1);
	return m?.message.content.filter((b: any) => b.type === "text").map((b: any) => b.text).join("") ?? "";
};

async function rpc(script: Step[]) {
	const c = new RpcClient({ script });
	c.send({ id: "p1", type: "prompt", message: "go" });
	await c.waitFor((r) => r.type === "agent_settled");
	const status = await c.close();
	return { records: c.records, status };
}

export async function ch31(): Promise<Trace> {
	const runs: Run[] = [];
	const obs: Observation[] = [];
	const o = (id: string, label: string, expected: string, observed: string, pass: boolean | null) => obs.push({ id, label, expected, observed, pass });

	// ---- a successful run, three interfaces
	const printOk = runPi({ script: OK, args: ["--print", "go"] });
	const jsonOk = runPi({ script: OK, args: ["--mode", "json", "go"] });
	const rpcOk = await rpc(OK);
	const jsonRecs = jsonRecords(jsonOk.stdout);

	const r1 = new Recorder();
	r1.log("driver", "process.exit", `print mode exits ${printOk.status}`, { status: printOk.status });
	r1.log("observer", "stdout", `stdout is one string: "${printOk.stdout.trim()}"`, { lines: printOk.stdout.trim().split("\n").length });
	runs.push({ id: "print-ok", label: "Print mode, success", description: "The whole interface is the final text and an exit status.", events: r1.events });

	const r2 = new Recorder();
	for (const e of jsonRecs.filter((x) => LIFECYCLE.has(x.type))) r2.log("agent", e.type, e.type === "tool_execution_start" ? `tool_execution_start (${e.toolName})` : e.type);
	r2.log("driver", "process.exit", `JSON mode exits ${jsonOk.status}`, { status: jsonOk.status });
	runs.push({ id: "json-ok", label: "JSON mode, success", description: "Events on stdout. No command responses.", events: r2.events });

	const r3 = new Recorder();
	for (const e of rpcOk.records.filter((x) => x.type === "response" || LIFECYCLE.has(x.type))) {
		if (e.type === "response") r3.log("driver", "response", `response to ${e.command} (id ${e.id}): success=${e.success}, disposition=${e.data?.disposition}`);
		else r3.log("agent", e.type, e.type === "tool_execution_start" ? `tool_execution_start (${e.toolName})` : e.type);
	}
	r3.log("driver", "process.exit", `RPC exits ${rpcOk.status} when stdin is closed`, { status: rpcOk.status });
	runs.push({ id: "rpc-ok", label: "RPC, success", description: "A response arrives first and means accepted. Events follow. The process stays up until stdin closes.", events: r3.events });

	// ---- the same failure, three interfaces
	const printBad = runPi({ script: FAIL, args: ["--print", "go"] });
	const jsonBad = runPi({ script: FAIL, args: ["--mode", "json", "go"] });
	const rpcBad = await rpc(FAIL);
	const badInStream = (recs: any[]) => recs.find((r) => r.type === "message_end" && r.message.role === "assistant")?.message.stopReason;

	const r4 = new Recorder();
	r4.log("driver", "process.exit", `print mode exits ${printBad.status}`, { status: printBad.status });
	r4.log("observer", "stderr", `the message is on stderr: "${printBad.stderr.trim()}"`);
	r4.log("observer", "stdout", `stdout is empty: ${JSON.stringify(printBad.stdout)}`);
	runs.push({ id: "print-fail", label: "Print mode, failed response", description: "The failure is the exit status.", events: r4.events });

	const r5 = new Recorder();
	r5.log("agent", "message_end", `the stream carries stopReason: ${badInStream(jsonRecords(jsonBad.stdout))}`);
	r5.log("driver", "process.exit", `JSON mode exits ${jsonBad.status}. A script that checks only $? calls this a success`, { status: jsonBad.status });
	runs.push({ id: "json-fail", label: "JSON mode, failed response", description: "The failure is in the stream, and the exit status is 0.", events: r5.events });

	const r6 = new Recorder();
	const promptResp = rpcBad.records.find((r) => r.type === "response" && r.command === "prompt");
	r6.log("driver", "response", `the prompt command itself succeeded: success=${promptResp?.success}`);
	r6.log("agent", "message_end", `the stream carries stopReason: ${badInStream(rpcBad.records)}`);
	runs.push({ id: "rpc-fail", label: "RPC, failed response", description: "The command succeeded; the model call did not. The failure is in the stream.", events: r6.events });

	// ---- observations
	const same = finalText(jsonRecs) === "the answer is forty-two" && finalText(rpcOk.records) === "the answer is forty-two" && printOk.stdout.trim() === "the answer is forty-two";
	o("same-answer", "All three interfaces end with the same final answer", "identical", same ? "identical" : "different", same);

	const kinds = (recs: any[]) => recs.map((r) => r.type).filter((t) => LIFECYCLE.has(t)).join(",");
	const sameEvents = kinds(jsonRecs) === kinds(rpcOk.records);
	o("same-events", "JSON and RPC show the same lifecycle events in the same order", "identical", sameEvents ? "identical" : "different", sameEvents);
	o("tool-ran", "The tool ran under the driver", "yes", jsonRecs.some((r) => r.type === "tool_execution_end" && !r.isError) ? "yes" : "no", jsonRecs.some((r) => r.type === "tool_execution_end" && !r.isError));

	o("print-fail", "A failed response, print mode: exit status", "non-zero", String(printBad.status), printBad.status !== 0);
	o("json-fail", "A failed response, JSON mode: exit status", "0", String(jsonBad.status), jsonBad.status === 0);
	o("json-stream", "A failed response, JSON mode: the failure is in the stream", "stopReason error", String(badInStream(jsonRecords(jsonBad.stdout))), badInStream(jsonRecords(jsonBad.stdout)) === "error");
	o("rpc-cmd", "A failed response, RPC: the prompt command succeeded", "true", String(promptResp?.success), promptResp?.success === true);
	o("rpc-stream", "A failed response, RPC: the failure is in the stream", "stopReason error", String(badInStream(rpcBad.records)), badInStream(rpcBad.records) === "error");
	o("rpc-started", "RPC acknowledges before the run: disposition", "started", String(rpcOk.records.find((r) => r.id === "p1")?.data?.disposition), rpcOk.records.find((r) => r.id === "p1")?.data?.disposition === "started");

	return finish({
		chapter: { number: 31, title: "The Interface Is Not the Agent" },
		experiment: { id: "pi/chapter-31/one-agent-three-drivers", title: "One agent, three drivers" },
		evidenceScope: "shipped_binary",
		claim: "The same agent behind print, JSON and RPC does the same thing and gives the same answer. What differs is the observer and the failure contract.",
		prediction: "The final answer and the lifecycle events match across drivers. A failed response is an exit status in print mode, and lives only in the stream in JSON mode and in RPC.",
		source: { test: "examples/ch31-interface/binary.test.ts", exporter: "examples/experiences/ch31.ts" },
		runs,
		observations: obs,
		limits: [
			"The model is scripted. This shows what the process does with a response, not how a real model answers.",
			"Run on the shipped pi binary under the platform in the environment panel. Shell behaviour may differ on other platforms.",
		],
	});
}
