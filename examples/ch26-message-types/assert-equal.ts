// Chapter 26 declares the message types by hand. This file is the check that the
// declarations are the real ones: each declared type must be assignable to the
// exported type and the other way round. A drift in either direction fails
// `npm run typecheck`, which is how "the declaration wins" is enforced.
import type { AgentMessage } from "@earendil-works/pi-agent-core";
import type { JsonValue, AssistantMessage, TextContent, ImageContent, ThinkingContent, ToolCall, ToolResultMessage, Usage, UserMessage, SystemMessage } from "@earendil-works/pi-ai";
import "@earendil-works/pi-coding-agent";
import type { Declared } from "./declared.ts";

type Same<A, B> = [A] extends [B] ? ([B] extends [A] ? true : false) : false;
const assertTrue = <_T extends true>() => {};

assertTrue<Same<Declared.AgentMessage, AgentMessage>>();
assertTrue<Same<Declared.TextContent, TextContent>>();
assertTrue<Same<Declared.ImageContent, ImageContent>>();
assertTrue<Same<Declared.ThinkingContent, ThinkingContent>>();
assertTrue<Same<Declared.ToolCall, ToolCall>>();
assertTrue<Same<Declared.Usage, Usage>>();
assertTrue<Same<Declared.SystemMessage, SystemMessage>>();
assertTrue<Same<Declared.UserMessage, UserMessage>>();
assertTrue<Same<Declared.AssistantMessage, AssistantMessage>>();
assertTrue<Same<Declared.ToolResultMessage<JsonValue>, ToolResultMessage<JsonValue>>>();

// Assignability alone tolerates a field that is missing on one side when it is
// optional. Comparing the key sets closes that gap.
type SameKeys<A, B> = [keyof A] extends [keyof B] ? ([keyof B] extends [keyof A] ? true : false) : false;
assertTrue<SameKeys<Declared.TextContent, TextContent>>();
assertTrue<SameKeys<Declared.ImageContent, ImageContent>>();
assertTrue<SameKeys<Declared.ThinkingContent, ThinkingContent>>();
assertTrue<SameKeys<Declared.ToolCall, ToolCall>>();
assertTrue<SameKeys<Declared.Usage, Usage>>();
assertTrue<SameKeys<Declared.SystemMessage, SystemMessage>>();
assertTrue<SameKeys<Declared.UserMessage, UserMessage>>();
assertTrue<SameKeys<Declared.AssistantMessage, AssistantMessage>>();
assertTrue<SameKeys<Declared.ToolResultMessage<JsonValue>, ToolResultMessage<JsonValue>>>();

export {};
