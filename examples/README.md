# Running this book's examples

Every `typescript` block in the manuscript carries a marker naming the file it came
from, and `npm run verify-examples` fails if the chapter and the source have drifted
apart. That is how the book stays honest: the code you read is the code that ran.

This page is how you get that code. It is the repository-local version of the book's
[Run This Book's Examples](https://programmer.ie/books/pi/run-the-examples/) page, which is where a browser
reader should start.

## Get the code

These examples now live in the [PI Agents development repository](../README.md).
The manuscript and Hugo site remain in the separate `pi` repository.

```bash
git clone https://github.com/ernanhughes/pi-agents.git
cd pi-agents
cd examples
npm install
npm run typecheck
npm test
```

For a specific revision rather than `main`, check out the corresponding commit or tag before installing. It is worth doing
when a check fails, because it separates "the examples are wrong" from "the repository
has moved on".

Old manuscript-repository commit IDs are not revision selectors for this repository.

## Prerequisites

| Requirement | Why | Check |
|---|---|---|
| **Node.js 22.19+** | What Pi requires, and what the examples use | `node --version` |
| **A POSIX shell** (`bash`) | Two tests in `ch14-skill-files/` run real shell scripts | `bash --version` |
| **Git** | The chapter 14 check script discovers the repository with `git rev-parse` | `git --version` |
| **npm** | To install the pinned packages | `npm --version` |

The shell requirement is the one that surprises people on Windows. `bash` on `PATH`
there is usually `C:\WINDOWS\system32\bash.exe`, the WSL launcher, which fails with
`execvpe(/bin/bash) failed` when no distribution is installed — and that failure looks
exactly like a failing test script. The test harness prefers Git Bash
(`C:\Program Files\Git\bin\bash.exe`) when it finds it, and skips those two tests with
a reason if no usable shell exists. To install Git Bash, install Git for Windows.

## Install

```bash
cd examples
npm install
```

`package.json` pins all three Pi packages to the exact release this book is written
against:

```json
"@earendil-works/pi-agent-core": "1.0.4",
"@earendil-works/pi-ai": "1.0.4",
"@earendil-works/pi-coding-agent": "1.0.4"
```

**This pin is deliberate and it is not cosmetic.** The manuscript is written against
1.0.4, so running the examples against any other release tests code the book does not
describe. Changing the pin is the same deliberate act as re-grounding the manuscript
and requires re-checking every chapter that cites a changed document.

The pin fixes these three packages directly. It does not pin their transitive
dependencies — see chapter 2 for why that distinction matters and which installer does
pin them. Use `npm ci` rather than `npm install` for a reproducible tree, since a
committed `package-lock.json` exists.

## Verify

For a standalone clone, run `npm run typecheck` and `npm test` from `examples/`.
The full command below still needs `content/books/pi/*.md` at this repository's
root. Those manuscript files are not included here; a sibling `pi` checkout alone
does not satisfy the scripts' current relative paths.

```bash
npm run verify-examples
```

Three stages, in order:

1. **`typecheck`** — `tsc` over the whole suite. Catches an example that no longer
   matches the pinned types.
2. **`check-embedded`** — compares all 65 embedded TypeScript blocks against their
   source files. `--fix` resynchronises the chapters from the sources; run it after
   changing an example that a chapter embeds.
3. **`test`** — the suite itself, through `node --test`.

The recorded pre-migration run at the pinned release was green: **279 tests, 279 pass, 0 fail**, plus a clean
typecheck and 65 matching embedded blocks. This is a historical result, not a
rerun after the move. If a test fails, the failure is usually one
of three things: a Pi version other than the pin, no usable POSIX shell, or a genuine
regression you have found.

## Regenerate the evidence

This workflow also needs the manuscript: `evidence` reads `content/books/pi/`,
and `sync-metadata` writes `metadata/*-chapter.yaml`, both relative to this root.
Use the combined development layout until the scripts support separate checkout
locations. The marker check's `--fix` option also writes manuscript chapters.

```bash
npm run evidence      # rewrites examples/EVIDENCE.md and evidence.json
npm run sync-metadata # writes executable_evidence into metadata/*-chapter.yaml
```

Run both after a batch of changes, not after each one. Every row in the ledger carries
a `claim_class` — `DOCUMENTED`, `OBSERVED` or `PROPOSED` — and an `evidence_scope`:
`declarations`, `in_process_runtime`, `shipped_binary` or `real_model`. That pair is
the book's method in machine-readable form, and it is what lets a reader tell a
property of Pi's types from a behaviour that was watched.

Note that a ledger row count and a test-case count are different numbers and are not
expected to match. Rows are claims; test cases are executions.

## Layout

Each directory is one chapter's runnable evidence, named for the chapter:

```text
examples/
├── harness/            shared test infrastructure (sessions, CLI, RPC, faux provider)
├── capstone-patch-desk/ public end-to-end capstone: parser fixture → Pi patch → host verification → review
├── ch01-…  ch02-…      one directory per chapter that has code
├── ch38-typed-step/    the typed step, with its 14 tests
├── ch40-composition/   the escalate-only-if-needed pipeline
├── evidence.json       machine-readable claim ledger
├── EVIDENCE.md         the same ledger as prose
└── check-embedded.mjs  manuscript marker checker
```

The `harness/` directory is infrastructure rather than a chapter's code, with two
things worth knowing about:

- **Every session is isolated.** Each test gets a fresh `PI_CODING_AGENT_DIR` and
  `PI_OFFLINE=1`, so running the suite never reads or writes your own Pi
  configuration.
- **The CLI harness runs the real executable.** `harness/cli.ts` resolves the binary
  through the pinned package's own `bin` mapping — the bundled build that `npm exec pi`
  runs — rather than hard-coding a path into `dist/`. A test asserts that mapping, so
  the "shipped binary" evidence cannot quietly downgrade to some other module.

## Running a single chapter

```bash
node --test ch38-typed-step/step.test.ts
```

Individual example files are plain modules with no build step, so you can also read one
and run it directly. TypeScript runs natively on Node 22.19+ via type stripping; that
is why `npm install` is the only setup step.

## Run the capstone

```bash
npm run capstone
npm run capstone -- --scenario injection
npm run test:capstone
```

[Pi Patch Desk](capstone-patch-desk/README.md) composes the book's mechanisms into
one public application. A scripted **actual Pi 1.0.4 loop** investigates and edits
a disposable parser fixture; fixed host tests, typecheck, and an independent grader
determine the outcome. The host writes a patch and seven-file review dossier under
the gitignored `capstone-patch-desk/runs/` directory. It never applies a patch to
the original fixture. The injection demonstration deliberately exits **1**.

The capstone guide includes the JSON driver and optional Pi interactive command.
It is self-contained in this public repository; a future private book chapter can
reference it. Scripted success does not measure real-model quality, and its
temporary directory and policy hooks do not provide OS containment.

## The faux provider

Most tests substitute a scripted provider (`fauxProvider` from `pi-ai`) for the real
model. This is what makes the suite free, fast and deterministic — and it is also its
main limit, which the book states wherever a result could be mistaken for more than it
is:

> Tests that use the faux provider show that the code *around* a model is correct.
> They are never evidence about how a real model behaves.

You can script a refusal, a rambling answer, a wrong tool call or a malformed
submission. You cannot script an autonomous surprise: every case a scripted test
exercises is behaviour you anticipated. Chapter 41 is the chapter about this, and about
what level 3 — evaluation against a real model — is for.

## Real-model evidence

There is none. The ledger contains no accepted `real_model` result, and
`examples/evidence.json` records one retained attempt that was refused by the provider
before the model saw a prompt, marked explicitly as not a result.

The contract for any future real-model run was frozen in advance — five inputs per
experiment and a stop rule — precisely so that a run could not be designed around
whatever it happened to return. Consult `planning/real-model-plan.md` in the
separate manuscript repository before adding one; that plan is not included here.
