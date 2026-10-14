# PI Agents — book development and examples

This is the development and executable examples repository for
[*Pi Agents: Building on the Coding Agent*](https://programmer.ie/books/pi/).
Use it alongside the book to read chapter code, run tests, and explore notebooks.
The manuscript and Hugo site are maintained separately in the `pi` repository.

## Start with the book's examples

The book targets **Pi 1.0.4**. The three Pi dependencies in
`examples/package.json` are pinned to that release; use them even when your
global Pi installation is newer.

```bash
git clone https://github.com/ernanhughes/pi-agents.git
cd pi-agents/examples
npm ci
npm run typecheck
npm test
```

See [the examples guide](examples/README.md) for prerequisites and evidence
limits, and [the notebook guide](notebooks/pi/README.md) for chapter companions.
Manuscript checks, evidence regeneration, metadata synchronisation, and notebooks
still expect book files at repository-relative paths. Those files are not
included here; a sibling manuscript checkout alone does not satisfy the current
scripts. The standalone commands above check code without comparing chapter snippets.

## Book development resources

| Path | Role |
|---|---|
| `examples/` | Chapter examples, tests, pinned packages, and evidence ledger |
| `notebooks/pi/` | Jupyter companions, planning notes, and historical execution reports |
| `.pi/` | Project-local learning and development resources |
| `docs/extensions/` | Supporting documentation for local extensions |
| `docker/` | Supporting environment and container setup notes |
| [AGENTS.md](AGENTS.md) | Contributor rules and evidence standards |

Chapter numbers connect the examples and notebooks to the book. Recorded reports
retain the scope and version of their original runs; the move is not a new run.
The resources below support hands-on development alongside the pinned examples.

## Layout

```text
.pi/
├── APPEND_SYSTEM.md        # project instructions appended to every system prompt
├── settings.json           # project settings (tools, resources)
├── mcp.json                # project MCP servers (example, disabled)
├── extensions/
│   ├── hello-tool.ts       # 1. custom tool  -> try: ask "use hello tool"
│   ├── postgres-tool.ts    # 6. service tool -> try: ask "use pg_query to list tables"
│   └── session-greeter.ts  # 2. events + /command -> try: /greet, watch session_start
├── skills/
│   └── pi-learning/
│       ├── SKILL.md        # 3. lazy-loaded skill -> try: /skill:pi-learning
│       └── references/
│           └── pi-concepts.md
└── prompts/
    ├── review.md           # 4. template -> try: /review, /review "API safety"
    └── plan.md             # 4. template with args -> try: /plan "add caching"
```

## Prerequisites

- Node.js 22.19+
- For interactive book development, install the book's release: `npm install -g --ignore-scripts @earendil-works/pi-coding-agent@1.0.4`
- A provider: run `/login` once inside Pi

## Run it

```bash
cd C:/Projects/pi-agents
pi
```

Pi auto-discovers `.pi/extensions`, `.pi/skills`, `.pi/prompts` after you
grant **project trust** (it will ask on first run).

Useful variants while learning:

```bash
pi --extension ./.pi/extensions/hello-tool.ts  # explicitly load this extension
pi config          # inspect which resources actually loaded
pi --help          # CLI flags
```

After editing any `.pi` file, run `/reload` inside Pi — no restart needed.

## Learn path (30 minutes)

1. **Tool** — open `.pi/extensions/hello-tool.ts`.
   Ask Pi: `use the hello tool to greet Ada`.
   Then change the greeting text, `/reload`, ask again.
2. **Events + command** — open `.pi/extensions/session-greeter.ts`.
   Run `/greet Ada`, then look at the `before_agent_start` handler.
   Try changing the injected guideline.
3. **Prompts** — run `/review` and `/plan "add caching"`.
   Open `.pi/prompts/review.md` to see `$1` / `${1:-default}` substitution.
4. **Skills** — run `/skill:pi-learning`.
   Compare with prompts: skills load lazily by *description match*,
   prompts are explicit `/commands`. Edit the skill description and see routing change.
5. **Settings + system** — open `.pi/settings.json` and `.pi/APPEND_SYSTEM.md`.
   Toggle `defaultTools`, run `/reload`, observe the tool list change.
6. **Service (Postgres)** — open `.pi/extensions/postgres-tool.ts`. See [docs/extensions/postgres-extension.md](docs/extensions/postgres-extension.md) for detailed documentation and setup.
   Ask Pi: `use pg_query to show tables`. DB `postgresql://pi:pi@localhost:5432/pi`
   already answers `SELECT 1` (verified). Set `DATABASE_URL`, `/reload`, ask again.

## Postgres

```bash
# start local DB matching postgresql://pi:pi@localhost:5432/pi
docker run --name pi-pg -e POSTGRES_USER=pi -e POSTGRES_PASSWORD=pi -e POSTGRES_DB=pi -p 5432:5432 -d postgres:16
npm run agent
# then ask: use pg_query to run SELECT 1
```

## Next steps

- Copy the smallest matching file from the built-in examples as your next experiment:
  `~/.pi/agent/install/.../examples/extensions/*.ts`
  (e.g. `todo.ts` for state, `confirm-destructive.ts` for `tool_call` gating).
- Read in this order: `configuration.md` → `extensions.md` → `skills.md` →
  `prompt-templates.md` → `packages.md` (paths in the Pi docs folder).
- Carry useful findings back to the corresponding chapter examples and coordinate
  any manuscript changes with the separate book repository.

## Scripts

| Command | Purpose |
|---|---|
| `npm run agent` | start Pi in this project |
| `npm run agent:hello` | start Pi with an explicit hello-extension argument |

## Contributing to the book's development

Keep changes tied to a chapter or clearly identified development aid. Ground Pi
API claims in the installed documentation and exported declarations at **1.0.4**;
declarations take precedence over prose. Distinguish documented contracts,
observed results, and proposed patterns. Faux-provider tests establish behaviour
around a model, not real-model quality.

For example changes, run `npm run typecheck` and `npm test` in `examples/`.
Coordinate manuscript snippets and metadata with the separate book repository.
Never commit credentials or local authentication files.
