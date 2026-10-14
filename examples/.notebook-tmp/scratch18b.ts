// scratch: registered-but-not-active, section vs getAllTools
import { makeSession, systemPromptSeenByProvider } from "../harness/session.ts";
import tools from "../ch17-tools/tools.ts";
import reviewGuardSection from "../ch18-knowledge/review-guard-section.ts";
import accessorProbe, { reset, seen } from "../ch18-knowledge/accessor-probe.ts";

reset();
const h = await makeSession({ extensions: [tools, accessorProbe, reviewGuardSection] });
const prompt = await systemPromptSeenByProvider(h);
console.log(
	JSON.stringify(
		{
			probe: { before: seen.beforeNarrow, registered: seen.registered, active: seen.active },
			promptHasSection: prompt.includes("`run_checks` runs this repository's type check"),
			registeredAfter: h.session.getAllTools().map((t: any) => t.name),
			activeAfter: h.session.getActiveToolNames(),
		},
		null,
		2,
	),
);
h.dispose();
