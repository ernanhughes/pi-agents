import { runDesk } from "./run.ts";
import { SCENARIOS, type Scenario } from "./script.ts";

const args = process.argv.slice(2);
const json = args.includes("--json");
const scenarioAt = args.indexOf("--scenario");
const scenario = (scenarioAt < 0 ? "success" : args[scenarioAt + 1]) as Scenario;
const allowed = json ? ["--json"] : [];
if (scenarioAt >= 0) allowed.push("--scenario", scenario);
if (!SCENARIOS.includes(scenario) || args.some((a) => !allowed.includes(a))) {
  console.error(`Usage: npm run capstone -- [--json] [--scenario ${SCENARIOS.join("|")}]`);
  process.exitCode = 2;
} else {
  const controller = new AbortController();
  process.once("SIGINT", () => controller.abort());
  const result = await runDesk({ scenario, signal: controller.signal, onEvent(event) {
    if (json) console.log(JSON.stringify(event));
    else if (event.type === "host_check_end") console.log(`${event.phase} ${event.kind}: exit ${event.exitCode}`);
    else if (event.type === "tool_execution_end") console.log(`Pi completed ${event.tool}${event.isError ? " (error)" : ""}`);
  } });
  if (json) console.log(JSON.stringify({ type: "desk_completed", status: result.status, directory: result.directory }));
  else console.log(`\nPi Patch Desk: ${result.status}\nReview: ${result.directory}\nOriginal fixture unchanged; no patch applied.`);
  process.exitCode = result.status === "verified" ? 0 : 1;
}
