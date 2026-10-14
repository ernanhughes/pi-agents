"""Chapter 03 - Models and Thinking Level."""

from _common import canonical_tests, establishes, heading, setup_cells, sources_and_limits

TITLE = "Models and Thinking Level"
QUESTION = """Four credential sources are configured at once. **Which one does Pi
actually use** — and does *how* you wrote the key change anything the agent does?

The second question is the chapter's real one. It is easy to believe that a key
fetched by a shell command is somehow a different agent from a key typed into a
file. The chapter's evidence says otherwise, and that is checkable."""

CELLS = [
    ("md", heading(3, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "Credential resolution is **first-source-wins** in a fixed order: a "
                "runtime key, then `auth.json`, then an `apiKey` in `models.json`, then "
                "the environment variable. The sources after the winner are never "
                "consulted.",
                "A model listed in `models.json` **parses and loads** while remaining "
                "**unavailable** until its provider has some credential — and a dummy "
                "key is enough to change that.",
                "Three ways of *writing* a provider key — a literal, `$NAME` resolved "
                "from the environment, and `!command` executed by a shell — produce three "
                "different credential strings and an **identical agent transcript**: same "
                "requests, same blocked call, same roles.",
            ],
            [
                "**No credential is real.** `ENV-KEY`, `STORED`, `MODELS`, `RUNTIME` and "
                "the three faux-provider keys are literals written by this notebook. No "
                "network request is made and nothing is billed.",
                "**Nothing about model quality, pricing or the model catalogue.** Those "
                "are version-sensitive and are not exercised here.",
                "**Nothing about `samplingParams` per thinking level, virtual models or "
                "cache warming.** The chapter names them; none is run in this notebook.",
            ],
        ),
    ),
    *setup_cells(
        3,
        mode="**Run** — Pi's real `ModelRuntime` against real files, then a real "
        "`AgentSession` with the chapter's guard extension.",
        scope="`in_process_runtime`. The provider is the scripted faux model; the "
        "credential machinery, the model runtime and the tool gate are Pi's.",
    ),
    (
        "md",
        """## Experiment 1: which source wins

Four sources, removed one at a time. The winner's *identity* is the literal string
that source contributed, which makes the result impossible to confuse with a
default.

This is Pi's `ModelRuntime` reading real `auth.json` and `models.json` files from
a fresh temporary directory — the same call path the chapter's test uses.""",
    ),
    (
        "code",
        'RESOLVE_SRC = r"""\n'
        'import { mkdtempSync, writeFileSync } from "node:fs";\n'
        'import { tmpdir } from "node:os";\n'
        'import { join } from "node:path";\n'
        'import { ModelRuntime } from "@earendil-works/pi-coding-agent";\n'
        "\n"
        'const ENV = { ANTHROPIC_API_KEY: "ENV-KEY" };\n'
        "export async function resolved(src: any) {\n"
        '\tconst dir = mkdtempSync(join(tmpdir(), "pinb-ch03-"));\n'
        '\tif (src.auth) writeFileSync(join(dir, "auth.json"), JSON.stringify({ anthropic: { type: "api_key", key: src.auth } }));\n'
        '\tif (src.models) writeFileSync(join(dir, "models.json"), JSON.stringify({ providers: { anthropic: { apiKey: src.models } } }));\n'
        "\tconst rt = await ModelRuntime.create({\n"
        '\t\tauthPath: join(dir, "auth.json"),\n'
        "\t\tmodelsPath: src.models ? join(dir, 'models.json') : null,\n"
        "\t\trefreshOnCreate: false,\n"
        "\t});\n"
        "\tif (src.runtime) await rt.setRuntimeApiKey('anthropic', src.runtime);\n"
        "\tconst r: any = await rt.getAuth('anthropic', { env: src.env ? ENV : {} } as any);\n"
        "\treturn (r?.auth?.apiKey ?? null) as string | null;\n"
        "}\n"
        '"""\n'
        "\n"
        'DRIVER = RESOLVE_SRC + r"""\n'
        "const all = { runtime: 'RUNTIME', auth: 'STORED', models: 'MODELS', env: true };\n"
        "const ladder: [string, string | null][] = [\n"
        "\t['all four sources', await resolved(all)],\n"
        "\t['drop the runtime key', await resolved({ ...all, runtime: undefined })],\n"
        "\t['drop auth.json too', await resolved({ ...all, runtime: undefined, auth: undefined })],\n"
        "\t['drop models.json too', await resolved({ ...all, runtime: undefined, auth: undefined, models: undefined })],\n"
        "\t['drop the environment too', await resolved({})],\n"
        "];\n"
        "\n"
        "// A model that parses but cannot be selected until its provider authenticates.\n"
        'const dir = mkdtempSync(join(tmpdir(), "pinb-ch03-avail-"));\n'
        "const write = (apiKey?: string) =>\n"
        "\twriteFileSync(\n"
        '\t\tjoin(dir, "models.json"),\n'
        '\t\tJSON.stringify({ providers: { mylocal: { baseUrl: "http://localhost:1/v1", api: "openai-completions", ...(apiKey ? { apiKey } : {}), models: [{ id: "my-model" }] } } }),\n'
        "\t);\n"
        "const probe = async () => {\n"
        "\tconst rt = await ModelRuntime.create({ authPath: join(dir, 'auth.json'), modelsPath: join(dir, 'models.json'), refreshOnCreate: false });\n"
        "\treturn { modelLoads: Boolean(rt.getModel('mylocal', 'my-model')), available: (await rt.getAvailable('mylocal')).map((m: any) => m.id) };\n"
        "};\n"
        "write();\n"
        "const withoutKey = await probe();\n"
        "write('ollama');\n"
        "const withDummyKey = await probe();\n"
        "\n"
        'console.log(JSON.stringify({ ladder, withoutKey, withDummyKey }));\n'
        '"""\n'
        "\n"
        'creds = pinb.driver(DRIVER, label="ch03-credentials", timeout=180)\n'
        'print(pinb.table(["sources configured", "resolved apiKey"],\n'
        '                 [[label, value if value is not None else "(none)"] for label, value in creds["ladder"]], indent=""))',
    ),
    (
        "md",
        """Read the ladder top to bottom: each row removes one source and the winner
changes. That is **first-source-wins**, and it is not a merge or a fallback with
preferences — once a source yields a credential, nothing below it is consulted.

The second experiment is the quieter one. A model in `models.json` with no
`apiKey` **loads** — `getModel` returns it — and is still absent from the
available list. Adding the string `ollama` changes nothing about the model and
everything about whether you can select it.""",
    ),
    (
        "code",
        'print("models.json entry, before and after a credential is added:")\n'
        'print(pinb.table(["models.json", "getModel() returns it", "getAvailable() lists it"],\n'
        '                 [["no apiKey", creds["withoutKey"]["modelLoads"], creds["withoutKey"]["available"] or "(empty)"],\n'
        '                  ["apiKey: ollama", creds["withDummyKey"]["modelLoads"], creds["withDummyKey"]["available"]]], indent=""))\n'
        "\n"
        "winners = [v for _, v in creds[\"ladder\"]]\n"
        "print()\n"
        "pinb.show_checks([\n"
        '    pinb.check("runtime wins when all four are present", winners[0] == "RUNTIME", str(winners[0])),\n'
        '    pinb.check("auth.json wins once the runtime key is gone", winners[1] == "STORED", str(winners[1])),\n'
        '    pinb.check("models.json wins next", winners[2] == "MODELS", str(winners[2])),\n'
        '    pinb.check("the environment is the last resort", winners[3] == "ENV-KEY", str(winners[3])),\n'
        '    pinb.check("with nothing configured there is no credential", winners[4] is None, str(winners[4])),\n'
        '    pinb.check("a model with no provider credential loads but is not available",\n'
        '               creds["withoutKey"]["modelLoads"] and not creds["withoutKey"]["available"],\n'
        '               f"loads={creds[\'withoutKey\'][\'modelLoads\']}, available={creds[\'withoutKey\'][\'available\']}"),\n'
        '    pinb.check("adding a dummy apiKey makes it available",\n'
        '               "my-model" in creds["withDummyKey"]["available"],\n'
        '               str(creds["withDummyKey"]["available"])),\n'
        "])",
    ),
    (
        "md",
        """## Experiment 2: provider configuration is not agent behaviour

This is the chapter's sharper claim, and it needs a real agent to test. The same
extension — the chapter 16 guard that refuses a force push — is loaded into three
real `AgentSession`s that differ **only** in how the faux provider's key is
spelled.

Three credential strings. One transcript.""",
    ),
    (
        "code",
        'DRIVER2 = r"""\n'
        'import { fauxAssistantMessage, fauxText, fauxToolCall } from "@earendil-works/pi-ai";\n'
        'import { makeSession } from "../harness/session.ts";\n'
        'import guard from "../ch16-events/guard.ts";\n'
        "\n"
        "const bash = (command: string) => fauxAssistantMessage([fauxToolCall('bash', { command })], { stopReason: 'toolUse' });\n"
        "\n"
        "async function transcriptShape(apiKey: string, env: Record<string, string>) {\n"
        "\tObject.assign(process.env, env);\n"
        "\tconst h = await makeSession({ extensions: [guard], apiKey });\n"
        "\th.faux.setResponses([bash('git push --force origin main'), bash('echo allowed'), fauxAssistantMessage([fauxText('done')])]);\n"
        "\tawait h.session.prompt('go');\n"
        "\tconst key = ((await h.modelRuntime.getAuth('faux')) as any)?.auth?.apiKey as string;\n"
        "\tconst results = h.session.messages.filter((m) => m.role === 'toolResult')\n"
        "\t\t.map((m: any) => ({ isError: m.isError, text: m.content[0].text.slice(0, 60) }));\n"
        "\tconst roles = h.session.messages.map((m) => m.role);\n"
        "\tconst requests = h.faux.state.callCount;\n"
        "\th.dispose();\n"
        "\treturn { key, shape: { results, roles, requests } };\n"
        "}\n"
        "\n"
        "const literal = await transcriptShape('a-literal-key', {});\n"
        "const fromEnv = await transcriptShape('$PINB_TEST_KEY', { PINB_TEST_KEY: 'from-the-environment' });\n"
        "const fromCommand = await transcriptShape('!echo from-a-command', {});\n"
        "\n"
        'console.log(JSON.stringify({ literal, fromEnv, fromCommand }));\n'
        '"""\n'
        'shapes = pinb.driver(DRIVER2, label="ch03-key-spelling", timeout=240)\n'
        'print(pinb.table(["key written as", "resolved credential", "requests", "tool results (in order)"],\n'
        '                 [[label, shapes[k]["key"].strip(), shapes[k]["shape"]["requests"],\n'
        '                   " | ".join(("ERR " if r["isError"] else "ok  ") + r["text"].splitlines()[0][:38] for r in shapes[k]["shape"]["results"])]\n'
        '                  for label, k in [("literal", "literal"), ("$NAME", "fromEnv"), ("!command", "fromCommand")]], indent=""))',
    ),
    (
        "code",
        'credentials = {"literal": shapes["literal"]["key"], "$NAME": shapes["fromEnv"]["key"], "!command": shapes["fromCommand"]["key"].strip()}\n'
        "\n"
        "pinb.show_checks([\n"
        '    pinb.check("three spellings produced three different credentials",\n'
        '               len(set(credentials.values())) == 3, str(credentials)),\n'
        '    pinb.check("the force push was blocked under every spelling",\n'
        '               all(s["shape"]["results"][0]["isError"] for s in shapes.values()), "blocked in all three"),\n'
        '    pinb.check("the ordinary command was allowed under every spelling",\n'
        '               not any(s["shape"]["results"][1]["isError"] for s in shapes.values()), "allowed in all three"),\n'
        '    pinb.check("the three transcripts are identical",\n'
        '               shapes["literal"]["shape"] == shapes["fromEnv"]["shape"] == shapes["fromCommand"]["shape"],\n'
        '               "roles, results and request count all equal"),\n'
        "])",
    ),
    (
        "md",
        """## Contrasting case: the credential is not the policy

The blocked force push is the visible part. What is interesting is that the
*credential string itself* never appears anywhere in the transcript. A key read
from a shell command, a key from an environment variable and a typed literal are
indistinguishable from the agent's point of view — which is the point. The guard
decided on the command, not on where the key came from.

### The chapter's own tests

Everything above is a focused driver. The chapter's seven tests assert the same
boundaries plus the availability result, and they run in about a second.""",
    ),
    *canonical_tests(
        3,
        "ch03-credentials/credentials.test.ts",
        what="The chapter's canonical evidence",
        show="credential",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** `LADDER` keeps the runtime key present in the first three rows.
What should the resolved key be in each row, and does anything else change?

**Then change one input.** Add `models` to the last row, or remove the runtime key
from the first, and re-run.

**Predict the boundary.** Which row is the first at which the resolved value is
`None`?""",
    ),
    (
        "code",
        "LADDER = [\n"
        '    ("runtime + auth", {"runtime": "RUNTIME", "auth": "STORED", "env": True}),\n'
        '    ("runtime only", {"runtime": "RUNTIME"}),\n'
        '    ("runtime + models", {"runtime": "RUNTIME", "models": "MODELS", "env": True}),\n'
        "    (\"nothing at all\", {}),\n"
        "]\n"
        'print("predicted winners:", [src or "(none)" for _, src in LADDER])\n'
        "\n"
        "import json as _json\n"
        "\n"
        "EXERCISE = RESOLVE_SRC + r\"\"\"\n"
        'const LADDER: [string, any][] = JSON.parse(process.env.NB_LADDER ?? "[]");\n'
        "const out: [string, string | null][] = [];\n"
        "for (const [label, src] of LADDER) out.push([label, await resolved(src)]);\n"
        "console.log(JSON.stringify(out));\n"
        '\"\"\"\n'
        "\n"
        "out = pinb.driver(\n"
        "    EXERCISE,\n"
        '    label="ch03-ladder",\n'
        "    timeout=180,\n"
        '    env={"NB_LADDER": _json.dumps([[label, src] for label, src in LADDER])},\n'
        ")\n"
        "print()\n"
        "for label, value in out:\n"
        '    print(f"  {label:22s} -> {value if value is not None else \'(none)\'}")\n'
        "\n"
        'assert all(v == "RUNTIME" for _, v in out[:3]), "a runtime key outranks every file and the environment"\n'
        "assert out[3][1] is None\n"
        'print("\\nheld: while a runtime key exists, nothing else is consulted at all")',
    ),
    (
        "md",
        """## Interpretation: two different questions

The chapter's material separates cleanly, and conflating them is the mistake it
is written against.

| Question | Where it is answered | What decides it |
|---|---|---|
| *Which credential does Pi use?* | experiment 1 | a fixed four-step order, first match wins |
| *What does the agent do?* | experiment 2 | the transcript: policy, tools and the model |

Nothing in the second table mentions credentials. That is the finding: how you
supply a key is an operational detail, and the moment you start reasoning about
what an agent will *do*, you have left that question behind.

The practical decisions this supports:

1. **Debug the key, not the agent.** A provider that will not authenticate is a
   configuration question; the resolution order tells you which file to look at.
2. **Beware the "loads but is unavailable" state.** A model parsing out of
   `models.json` is not the same as a model you can select. The dummy-key row is
   the cheapest way to see the difference.
3. **Version-sensitive parts are named, not exercised.** `samplingParams` per
   thinking level arrived in 1.0.2 and applies to three APIs; the classifier list
   changed in 1.0.1; the `azure-openai-responses` *provider* was renamed to
   `azure` in 1.0.4 while the *API* id stayed. None of that is run here.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=3,
            mode="**Run** — Pi's `ModelRuntime` against real files, and a real `AgentSession` "
            "with the chapter 16 guard, plus the chapter's own test file.",
            scope="`in_process_runtime`. Credential resolution, the model runtime and the tool "
            "gate are Pi's; the model is the scripted faux provider.",
            provenance=[
                "**Ran** `ModelRuntime.create` + `getAuth` over fresh temporary `auth.json` / "
                "`models.json` files, varying which sources exist.",
                "**Ran** three real `AgentSession`s through `makeSession`, loading "
                "`ch16-events/guard.ts` unmodified.",
                "**Ran** `ch03-credentials/credentials.test.ts`.",
                "**Read** `examples/evidence.json`, chapter 3 rows (7 claims).",
            ],
            limits=[
                "**No credential here is real.** Each is a literal string written by this "
                "notebook; `!echo from-a-command` runs a shell echo. Nothing reaches a provider "
                "and nothing is billed.",
                "**The model is scripted**, so the identical-transcript result is a claim about "
                "the code around a model, not about model behaviour under three keys. This book "
                "does not claim a real model would behave identically, only that nothing in Pi's "
                "design gives it a reason to differ.",
                "**Model ids, the catalogue and pricing are version-sensitive** and are not "
                "exercised. The `ollama` row is a literal string used as a credential, not a "
                "connection to an Ollama instance.",
            ],
        ),
    ),
]