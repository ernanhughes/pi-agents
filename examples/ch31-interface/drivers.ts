import type { Agent } from "@earendil-works/pi-agent-core";

// Interface 1: streaming. What a terminal does: draw text as it arrives.
export async function drive_streaming(agent: Agent, prompt: string, draw: (chunk: string) => void): Promise<void> {
	const off = agent.subscribe((e) => {
		if (e.type === "message_update" && e.assistantMessageEvent.type === "text_delta") {
			draw(e.assistantMessageEvent.delta);
		}
	});
	try {
		await agent.prompt(prompt);
	} finally {
		off();
	}
}

// Interface 2: one-shot. What print mode does: no events, the final text and a status.
export async function drive_oneshot(agent: Agent, prompt: string): Promise<{ text: string; ok: boolean }> {
	await agent.prompt(prompt);
	const last = [...agent.state.messages].reverse().find((m) => m.role === "assistant") as any;
	const text = last.content.filter((b: any) => b.type === "text").map((b: any) => b.text).join("");
	return { text, ok: last.stopReason !== "error" && last.stopReason !== "aborted" };
}
