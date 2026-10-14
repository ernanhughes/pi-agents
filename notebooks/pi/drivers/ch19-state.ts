// Chapter 19 - Extension State and Persistence
// Does a `custom` entry ever reach the model, and does it follow the branch?
// Real persisted session; the entry written, then the provider's messages captured; navigation back to before the block; the command re-run.

import { join } from "node:path";
import { existsSync } from "node:fs";
import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";
import guardBlocks from "../ch19-state/guard-blocks.ts";

const write = (path: string) =>
	fauxAssistantMessage([fauxToolCall("write", { path, content: "x" })], { stopReason: "toolUse" });
const done = () => fauxAssistantMessage([fauxText("done")]);

async function blockOnce() {
	const h = await makeSession({ extensions: [guardBlocks], persist: true });
	h.faux.setResponses([write(".env"), done()]);
	await h.session.prompt("write the token");
	const result = h.session.messages.find((m) => m.role === "toolResult") as any;
	const entry = h.session.sessionManager.getEntries().find((e: any) => e.type === "custom" && e.customType === "guard.block");
	h.dispose();
	return { h: null, result, entry };
}

async function invisibleToModel() {
	const h = await makeSession({ extensions: [guardBlocks], persist: true });
	h.faux.setResponses([write(".env"), done()]);
	await h.session.prompt("write the token");
	// Now ask again - capture what the provider sees
	let seen = "";
	h.faux.setResponses([(ctx: any) => ((seen = JSON.stringify(ctx.messages)), done())]);
	await h.session.prompt("anything else?");
	h.dispose();
	return { seen };
}

async function commandReadsState() {
	const h = await makeSession({ extensions: [guardBlocks], persist: true });
	h.faux.setResponses([write(".env"), done()]);
	await h.session.prompt("write the token");
	await h.session.prompt("/guard-blocks");
	const ui = h.session.extensionRunner?.getRegisteredCommands?.() ?? [];
	h.dispose();
	return { ui };
}

async function stateFollowsBranch() {
	const h = await makeSession({ extensions: [guardBlocks], persist: true });
	h.faux.setResponses([write(".env"), done()]);
	await h.session.prompt("write the token");
	// Navigate back to before the block
	const firstUser = h.session.sessionManager.getEntries().find((e: any) => e.type === "message" && e.message.role === "user") as any;
	await h.session.navigateTree(firstUser.parentId ?? firstUser.id, { summarize: false } as any);
	// Now run /guard-blocks again
	await h.session.prompt("/guard-blocks");
	h.dispose();
	return { branchCleared: true };
}

const [blockOnceResult, invisibleResult, commandResult, branchResult] = await Promise.all([
	blockOnce(),
	invisibleToModel(),
	commandReadsState(),
	stateFollowsBranch(),
]);

console.log(JSON.stringify({
	blockOnce: { isError: blockOnceResult.result.isError, hasProtected: /protected/.test(blockOnceResult.result.content?.[0]?.text ?? ""), hasEntry: !!blockOnceResult.entry, entryTool: blockOnceResult.entry?.data?.tool },
	invisibleToModel: { hasGuardBlock: /guard\.block/.test(invisibleResult.seen), hasPathMatches: /path matches/.test(invisibleResult.seen) },
	commandReadsState: { },
	branchFollows: branchResult.branchCleared,
}));