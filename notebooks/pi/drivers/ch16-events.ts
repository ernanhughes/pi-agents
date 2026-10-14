// Chapter 16 - Events and the Extension Lifecycle
// With no UI to ask, does a guard leave the filesystem untouched?
// Real sessions with the chapter's guard and its counting variant; ran.flag checked in every case; the throwing-handler fail-safe.

import { join } from "node:path";
import { existsSync } from "node:fs";
import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession, UiRecorder } from "../harness/session.ts";
import guard from "../ch16-events/guard.ts";
import guardStatus from "../ch16-events/guard-status.ts";

const bash = (command: string) =>
	fauxAssistantMessage([fauxToolCall("bash", { command })], { stopReason: "toolUse" });

async function run(ext: typeof guard, command: string, label: string) {
	const h = await makeSession({ extensions: [ext] });
	h.faux.setResponses([bash(command), fauxAssistantMessage([fauxText("done")])]);
	await h.session.prompt("go");
	const result = h.session.messages.find((m) => m.role === "toolResult") as any;
	const ran = existsSync(join(h.cwd, "ran.flag"));
	h.dispose();
	return { label, result, ran };
}

async function runWithUI(ext: typeof guard, command: string, label: string, answer: boolean) {
	const ui = new UiRecorder();
	ui.confirmAnswers = [answer];
	const h = await makeSession({ extensions: [ext], ui });
	h.faux.setResponses([bash(command), fauxAssistantMessage([fauxText("done")])]);
	await h.session.prompt("go");
	const result = h.session.messages.find((m) => m.role === "toolResult") as any;
	const ran = existsSync(join(h.cwd, "ran.flag"));
	h.dispose();
	return { label, result, ran, confirmed: answer };
}

async function throwing() {
	const throwing: typeof guard = (pi) => {
		pi.on("tool_call", async () => {
			throw new Error("handler bug");
		});
	};
	const h = await makeSession({ extensions: [throwing] });
	h.faux.setResponses([bash("touch ran.flag"), fauxAssistantMessage([fauxText("done")])]);
	await h.session.prompt("go");
	const result = h.session.messages.find((m) => m.role === "toolResult") as any;
	const ran = existsSync(join(h.cwd, "ran.flag"));
	h.dispose();
	return { result, ran };
}

const [
	noUIForcePush,
	noUIOrdinary,
	noUIResetHard,
	noUIMultiHook,
	withUIApproved,
	withUIDeclined,
	throwingResult,
] = await Promise.all([
	run(guard, "touch ran.flag && git push --force origin main", "noUI-force-push"),
	run(guard, "touch ran.flag", "noUI-ordinary"),
	run(guard, "git reset --hard HEAD~1", "noUI-reset-hard"),
	run(guardStatus, "touch ran.flag && git push -f origin main", "noUI-multi-hook"),
	runWithUI(guard, "touch ran.flag && echo approved", "withUI-approved", true),
	runWithUI(guard, "touch ran.flag && git push --force origin main", "withUI-declined", false),
	throwing(),
]);

console.log(JSON.stringify({
	noUIForcePush: { isError: noUIForcePush.result.isError, hasGuardBlocked: /Guard blocked/.test(noUIForcePush.result.content?.[0]?.text ?? ""), ran: noUIForcePush.ran },
	noUIOrdinary: { isError: noUIOrdinary.result.isError, ran: noUIOrdinary.ran },
	noUIResetHard: { isError: noUIResetHard.result.isError },
	noUIMultiHook: { isError: noUIMultiHook.result.isError, hasForceWithLease: /--force-with-lease/.test(noUIMultiHook.result.content?.[0]?.text ?? ""), ran: noUIMultiHook.ran },
	withUIApproved: { isError: withUIApproved.result.isError, ran: withUIApproved.ran },
	withUIDeclined: { isError: withUIDeclined.result.isError, ran: withUIDeclined.ran },
	throwing: { isError: throwingResult.result.isError, ran: throwingResult.ran },
}));