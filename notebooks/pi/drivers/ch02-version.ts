// Chapter 2 part 1 - which executable, and which version.
//
// The binary is resolved through the pinned package's own `bin` mapping, which is
// what `npm exec pi` and the published bin stub use. Running a path inside dist/
// instead would exercise a different program.

import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { PI_BIN, PI_BIN_RELATIVE, runRaw } from "../harness/cli.ts";

const agentDir = mkdtempSync(join(tmpdir(), "pinb-ch02-"));
const version = runRaw(["--version"], { agentDir, cwd: agentDir });
const help = runRaw(["--help"], { agentDir, cwd: agentDir });

console.log(
	JSON.stringify({
		binMapping: PI_BIN_RELATIVE,
		exit: version.status,
		reportedVersion: version.stdout.trim(),
		helpIsAvailable: /--print/.test(help.stdout),
	}),
);