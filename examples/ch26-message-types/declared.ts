// The message types exactly as chapter 26 declares them, in a namespace so they can be
// compared with the exported ones by assert-equal.ts.
import type { AgentMessage as RealAgentMessage } from "@earendil-works/pi-agent-core";
import type {
	AssistantMessageDiagnostic,
	DeferredHandle,
	JsonValue,
	ModelThinkingLevel,
	NestedToolCalls,
	Tool,
	ToolReference,
} from "@earendil-works/pi-ai";
// pi-coding-agent adds four roles to AgentMessage by declaration merging.
import "@earendil-works/pi-coding-agent";

export namespace Declared {
	type BashExecutionMessage = Extract<RealAgentMessage, { role: "bashExecution" }>;
	type CustomMessage = Extract<RealAgentMessage, { role: "custom" }>;
	type BranchSummaryMessage = Extract<RealAgentMessage, { role: "branchSummary" }>;
	type CompactionSummaryMessage = Extract<RealAgentMessage, { role: "compactionSummary" }>;

	export type AgentMessage =
	  | SystemMessage
	  | UserMessage
	  | AssistantMessage
	  | ToolResultMessage
	  | BashExecutionMessage
	  | CustomMessage
	  | BranchSummaryMessage
	  | CompactionSummaryMessage;

	export interface TextContent { type: "text"; text: string; textSignature?: string; }
	export interface ImageContent { type: "image"; data: string; mimeType: string; }
	export interface ThinkingContent { type: "thinking"; thinking: string; thinkingSignature?: string; redacted?: boolean; }
	export interface ToolCall { type: "toolCall"; id: string; name: string; arguments: Record<string, any>; thoughtSignature?: string; namespace?: string; }

	export interface Usage {
	  input: number; output: number; cacheRead: number; cacheWrite: number;
	  cacheWrite1h?: number; reasoning?: number; totalTokens: number;
	  cost: { input: number; output: number; cacheRead: number; cacheWrite: number; total: number; };
	}

	export interface SystemMessage {
	  role: "system";
	  content: string | TextContent[];
	  sections?: Record<string, string | null>;
	  toolsAdded?: Tool[];
	  toolsRemoved?: ToolReference[];
	  timestamp: number;
	}

	export interface UserMessage {
	  role: "user";
	  content: string | (TextContent | ImageContent)[];
	  timestamp: number;
	}

	export interface AssistantMessage {
	  role: "assistant";
	  content: (TextContent | ThinkingContent | ToolCall)[];
	  api: string;
	  provider: string;
	  model: string;
	  responseModel?: string;
	  responseId?: string;
	  providerThinkingLevel?: string;
	  thinkingLevel?: ModelThinkingLevel;
	  diagnostics?: AssistantMessageDiagnostic[];
	  usage: Usage;
	  stopReason: "pending" | "stop" | "length" | "toolUse" | "error" | "aborted" | "deferred";
	  deferred?: DeferredHandle;
	  errorMessage?: string;
	  rawStopReason?: string;
	  endTurn?: boolean;
	  timestamp: number;
	}

	export interface ToolResultMessage<TDetails = JsonValue> {
	  role: "toolResult";
	  toolCallId: string;
	  toolName: string;
	  content: (TextContent | ImageContent)[];
	  details?: TDetails;
	  usage?: Usage;
	  nestedCalls?: NestedToolCalls;
	  isError: boolean;
	  timestamp: number;
	}
}
