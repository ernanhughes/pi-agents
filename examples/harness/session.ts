// Test harness for the extension chapters (15 to 21).
//
// It builds a real AgentSession from pi-coding-agent 1.0.2: a real extension
// runtime, real built-in tools, and a real session manager, with an in-memory
// session and the faux provider standing in for the model. Extension code under
// test is loaded exactly as Pi loads it, through an inline extension factory.
//
// Nothing here re-implements a Pi rule. The only substitution is the model.
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import {
	createAgentSession,
	DefaultResourceLoader,
	ModelRuntime,
	SessionManager,
	SettingsManager,
	type AgentSession,
	type ExtensionFactory,
	type ExtensionUIContext,
} from "@earendil-works/pi-coding-agent";
import { fauxProvider, type FauxProviderHandle } from "@earendil-works/pi-ai";

export interface Harness {
	session: AgentSession;
	agentDir: string;
	modelRuntime: ModelRuntime;
	faux: FauxProviderHandle;
	cwd: string;
	dispose(): void;
}

/**
 * A recording stand-in for the interface (chapter 31: the interface is not the agent).
 * Dialogs return the answers you queue, and everything shown to the user is recorded.
 * Method names not listed are no-ops, which is how a mode with no terminal behaves.
 */
export class UiRecorder {
	notifications: { message: string; type?: string }[] = [];
	confirms: { title: string; message: string }[] = [];
	confirmAnswers: boolean[] = [];
	selectAnswers: (string | undefined)[] = [];
	selects: { title: string; options: string[] }[] = [];

	asContext(): ExtensionUIContext {
		const self = this;
		const impl: Record<string, unknown> = {
			notify: (message: string, type?: string) => void self.notifications.push({ message, type }),
			confirm: async (title: string, message: string) => {
				self.confirms.push({ title, message });
				return self.confirmAnswers.shift() ?? false;
			},
			select: async (title: string, options: string[]) => {
				self.selects.push({ title, options });
				return self.selectAnswers.shift();
			},
		};
		return new Proxy(impl, { get: (t, k) => (k in t ? t[k as string] : () => undefined) }) as unknown as ExtensionUIContext;
	}
}

export interface HarnessOptions {
	extensions: ExtensionFactory[];
	tools?: string[];
	/** Denylist passed to createAgentSession, the same option `--exclude-tools` sets. */
	excludeTools?: string[];
	cwd?: string;
	/** Bind a UI. Without it the session behaves as print or JSON mode: no UI at all. */
	ui?: UiRecorder;
	/** Settings merged over the defaults (compaction and retry are off unless you say otherwise). */
	settings?: Record<string, unknown>;
	/** Write the session to a real JSONL file instead of keeping it in memory. */
	persist?: boolean;
	/** The provider's apiKey as written in a config: a literal, $NAME, ${NAME} or !command. */
	apiKey?: string;
	/** Files to create before the session starts, relative to the agent directory (user level). */
	agentFiles?: Record<string, string>;
	/** Files to create before the session starts, relative to the working directory (project level). */
	projectFiles?: Record<string, string>;
	/** Passed through to DefaultResourceLoader, overriding the harness defaults. */
	resourceOptions?: Record<string, unknown>;
	/** Options for the faux provider, for example tokensPerSecond to make a response take real time. */
	fauxOptions?: Parameters<typeof fauxProvider>[0];
}

export async function makeSession(options: HarnessOptions): Promise<Harness> {
	const root = mkdtempSync(join(tmpdir(), "pi-harness-"));
	const cwd = options.cwd ?? root;
	const agentDir = join(root, "agent");

	for (const [base, files] of [[agentDir, options.agentFiles], [cwd, options.projectFiles]] as const) {
		for (const [rel, content] of Object.entries(files ?? {})) {
			const target = join(base, rel);
			mkdirSync(dirname(target), { recursive: true });
			writeFileSync(target, content);
		}
	}

	const faux = fauxProvider(options.fauxOptions);
	const modelRuntime = await ModelRuntime.create({
		authPath: join(agentDir, "auth.json"),
		modelsPath: null,
		refreshOnCreate: false,
	});
	const model = faux.getModel();
	modelRuntime.registerProvider("faux", {
		baseUrl: "http://faux.invalid",
		apiKey: options.apiKey ?? "not-a-real-key",
		api: faux.api as any,
		streamSimple: (m, c, o) => faux.provider.streamSimple!(m, c, o),
		models: [
			{
				id: model.id,
				name: "Faux",
				input: ["text"],
				cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
				reasoning: Boolean((model as { reasoning?: boolean }).reasoning),
				contextWindow: 100_000,
				maxTokens: 4096,
			},
		],
	});

	const resourceLoader = new DefaultResourceLoader({
		cwd,
		agentDir,
		extensionFactories: options.extensions,
		noContextFiles: true,
		noSkills: true,
		noPromptTemplates: true,
		noThemes: true,
		...options.resourceOptions,
	} as any);
	await resourceLoader.reload();

	const { session } = await createAgentSession({
		cwd,
		agentDir,
		modelRuntime,
		model: modelRuntime.getModel("faux", model.id) as any,
		thinkingLevel: "off",
		resourceLoader,
		sessionManager: options.persist ? SessionManager.create(cwd, join(root, "sessions")) : SessionManager.inMemory(cwd),
		settingsManager: SettingsManager.inMemory({ compaction: { enabled: false }, retry: { enabled: false }, ...options.settings } as any),
		tools: options.tools,
		excludeTools: options.excludeTools,
	});
	await session.bindExtensions(options.ui ? { uiContext: options.ui.asContext(), mode: "rpc" } : {});

	return { session, faux, cwd, agentDir, modelRuntime, dispose: () => session.dispose() };
}

/** What the provider actually receives as its system message, as one string, for one scripted turn. */
export async function systemPromptSeenByProvider(h: Harness, userText = "go"): Promise<string> {
	const { fauxAssistantMessage, fauxText, getSystemMessageText, getCurrentSystemMessage } = await import("@earendil-works/pi-ai");
	let seen: any;
	h.faux.appendResponses([
		(ctx) => {
			seen = ctx;
			return fauxAssistantMessage([fauxText("ok")]);
		},
	]);
	await h.session.prompt(userText);
	const sys = getCurrentSystemMessage(seen.messages);
	return sys ? getSystemMessageText(sys) : "";
}
