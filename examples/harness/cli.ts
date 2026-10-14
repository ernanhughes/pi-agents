// Run the shipped `pi` binary as a child process with a scripted model.
import { spawn, spawnSync, type ChildProcessWithoutNullStreams } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const PACKAGE_DIR = join(here, "..", "node_modules", "@earendil-works", "pi-coding-agent");

// Resolve the executable through the pinned package's own `bin` mapping rather
// than hard-coding a path into dist/. That mapping is what `npm exec pi` and the
// published bin stub use, and it points at the bundled build. dist/cli.js is an
// internal module that the bundle happens to contain, so testing it would
// exercise a different program from the shipped executable.
const pkg = JSON.parse(readFileSync(join(PACKAGE_DIR, "package.json"), "utf8")) as { bin: Record<string, string> };
export const PI_BIN = join(PACKAGE_DIR, pkg.bin.pi);
export const PI_BIN_RELATIVE = pkg.bin.pi;
const EXTENSION = join(here, "faux-extension.ts");

export type Step = { text?: string; tool?: string; args?: Record<string, unknown>; error?: string };

export interface CliOptions {
	script: Step[];
	args?: string[];
	cwd?: string;
	stdin?: string;
	tokensPerSecond?: number;
	env?: Record<string, string>;
	/** Keep the session file (the default is --no-session). */
	session?: boolean;
	/** --approve, --no-approve, or neither. The default is --approve, so project resources do not get in the way. */
	approve?: "yes" | "no" | "none";
	/** Load AGENTS.md and CLAUDE.md (the default is --no-context-files). */
	contextFiles?: boolean;
	/** Files created in the agent directory before the run (user level), and in the working directory (project level). */
	agentFiles?: Record<string, string>;
	projectFiles?: Record<string, string>;
	/** Extra --extension paths. */
	extraExtensions?: string[];
	/** Use this agent directory instead of a fresh one (to share a trust.json made with ProjectTrustStore). */
	agentDir?: string;
}

function seed(base: string, files?: Record<string, string>) {
	for (const [rel, content] of Object.entries(files ?? {})) {
		const t = join(base, rel);
		mkdirSync(dirname(t), { recursive: true });
		writeFileSync(t, content);
	}
}

export function cliEnv(o: Pick<CliOptions, "script" | "tokensPerSecond" | "env">, agentDir: string): NodeJS.ProcessEnv {
	return {
		...process.env,
		PI_CODING_AGENT_DIR: agentDir,
		PI_OFFLINE: "1",
		PI_SKIP_VERSION_CHECK: "1",
		PI_TELEMETRY: "0",
		PI_FAUX_SCRIPT: JSON.stringify(o.script),
		...(o.tokensPerSecond ? { PI_FAUX_TPS: String(o.tokensPerSecond) } : {}),
		...o.env,
	};
}

export function baseArgs(o: Pick<CliOptions, "session" | "approve" | "contextFiles">): string[] {
	return [
		"--extension", EXTENSION, "--provider", "faux", "--model", "faux-1",
		...(o.contextFiles ? [] : ["--no-context-files"]),
		...(o.session ? [] : ["--no-session"]),
		...(o.approve === "yes" ? ["--approve"] : o.approve === "no" ? ["--no-approve"] : []),
	];
}

export function runPi(o: CliOptions) {
	const agentDir = o.agentDir ?? mkdtempSync(join(tmpdir(), "pi-cli-agent-"));
	const cwd = o.cwd ?? mkdtempSync(join(tmpdir(), "pi-cli-cwd-"));
	seed(agentDir, o.agentFiles);
	seed(cwd, o.projectFiles);
	const ext = (o.extraExtensions ?? []).flatMap((e) => ["--extension", e]);
	const r = spawnSync(process.execPath, [PI_BIN, ...baseArgs({ approve: "yes", ...o }), ...ext, ...(o.args ?? [])], {
		cwd,
		env: cliEnv(o, agentDir),
		input: o.stdin,
		encoding: "utf8",
		timeout: 60_000,
	});
	return { status: r.status, stdout: r.stdout, stderr: r.stderr, cwd, agentDir };
}

export function startPi(o: CliOptions): { child: ChildProcessWithoutNullStreams; cwd: string } {
	const agentDir = mkdtempSync(join(tmpdir(), "pi-cli-agent-"));
	const cwd = o.cwd ?? mkdtempSync(join(tmpdir(), "pi-cli-cwd-"));
	const child = spawn(process.execPath, [PI_BIN, ...baseArgs({ approve: "yes", ...o }), ...(o.args ?? [])], { cwd, env: cliEnv(o, agentDir) });
	return { child, cwd };
}

/** A line-framed JSONL client for `pi --mode rpc`. Splits on LF only, as the protocol requires. */
export class RpcClient {
	records: any[] = [];
	stderr = "";
	private buffer = "";
	private waiters: { test: (r: any) => boolean; resolve: (r: any) => void }[] = [];
	readonly child: ChildProcessWithoutNullStreams;
	readonly cwd: string;
	exited: Promise<number | null>;

	constructor(o: CliOptions & { extraExtensions?: string[] }) {
		const agentDir = mkdtempSync(join(tmpdir(), "pi-rpc-agent-"));
		this.cwd = o.cwd ?? mkdtempSync(join(tmpdir(), "pi-rpc-cwd-"));
		const ext = (o.extraExtensions ?? []).flatMap((e) => ["--extension", e]);
		this.child = spawn(process.execPath, [PI_BIN, ...baseArgs({ approve: "yes", ...o }), ...ext, "--mode", "rpc", ...(o.args ?? [])], { cwd: this.cwd, env: cliEnv(o, agentDir) });
		this.child.stdout.setEncoding("utf8");
		this.child.stderr.setEncoding("utf8");
		this.child.stdout.on("data", (chunk: string) => {
			this.buffer += chunk;
			let i: number;
			while ((i = this.buffer.indexOf("\n")) >= 0) {
				const line = this.buffer.slice(0, i).replace(/\r$/, "");
				this.buffer = this.buffer.slice(i + 1);
				if (!line) continue;
				const rec = JSON.parse(line);
				this.records.push(rec);
				this.waiters = this.waiters.filter((w) => (w.test(rec) ? (w.resolve(rec), false) : true));
			}
		});
		this.child.stderr.on("data", (c: string) => (this.stderr += c));
		this.exited = new Promise((r) => this.child.on("close", (code) => r(code)));
	}

	send(command: object): void {
		this.child.stdin.write(JSON.stringify(command) + "\n");
	}

	sendRaw(text: string): void {
		this.child.stdin.write(text);
	}

	/** Resolve with the first record, already seen or yet to arrive, that satisfies `test`. */
	waitFor(test: (r: any) => boolean, ms = 15000): Promise<any> {
		const seen = this.records.find(test);
		if (seen) return Promise.resolve(seen);
		return new Promise((resolve, reject) => {
			const t = setTimeout(() => reject(new Error(`timed out waiting; saw ${this.records.map((r) => r.type + (r.command ? ":" + r.command : "")).join(",")}`)), ms);
			this.waiters.push({ test, resolve: (r) => (clearTimeout(t), resolve(r)) });
		});
	}

	async close(): Promise<number | null> {
		this.child.stdin.end();
		return this.exited;
	}
}

/** Run the shipped binary with exactly these arguments (no faux provider), for package and config subcommands. */
export function runRaw(args: string[], o: { agentDir: string; cwd: string; env?: Record<string, string>; input?: string }) {
	const r = spawnSync(process.execPath, [PI_BIN, ...args], {
		cwd: o.cwd,
		env: { ...process.env, PI_CODING_AGENT_DIR: o.agentDir, PI_OFFLINE: "1", PI_SKIP_VERSION_CHECK: "1", PI_TELEMETRY: "0", ...o.env },
		encoding: "utf8",
		input: o.input ?? "",
		timeout: 90_000,
	});
	return { status: r.status, stdout: r.stdout, stderr: r.stderr };
}
