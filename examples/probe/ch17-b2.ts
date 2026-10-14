import { exec } from "node:child_process";
import { promisify } from "node:util";

const execAsync = promisify(exec);

async function runCommand(command: string): Promise<{ output: string; exit_code: number }> {
	try {
		const { stdout, stderr } = await execAsync(command, { maxBuffer: 1024 * 1024 });
		return { output: stdout + stderr, exit_code: 0 };
	} catch (err: any) {
		// exec rejects on a non-zero exit. That is a result, not a tool failure.
		return { output: `${err.stdout ?? ""}${err.stderr ?? ""}`, exit_code: err.code ?? 1 };
	}
}
