---
name: pi-patch-desk
description: Walk through Pi Patch Desk's offline parser fixture, inspect a proposed patch and its evidence dossier, or demonstrate a prohibited action. Use for this capstone only.
disable-model-invocation: true
---

# Pi Patch Desk walkthrough

This skill describes the public book capstone. It grants no file access or approval.
Resolve the capstone README.md two directories above this skill directory.
The host implements one workflow; do not recreate it with ad hoc agent tools.

1. Read that README.md. Explain that responses are scripted but Pi tools and host
   checks actually execute against a disposable fixture.
2. From examples/, run `npm run capstone`. Alternatively have the reader enter
   `/patch-desk` if the optional extension is loaded; the command calls the same host.
3. Open review.md, then patch.diff and tests.json in the printed run directory.
   Confirm the before-test exit is 1 and all final checks are 0 before describing
   a verified fix. Check evidence.json for exact source citations.
4. Run `npm run capstone -- --scenario injection` or `/patch-desk injection`.
   This intentionally exits 1. Explain the refusal recorded in run.json and
   events.jsonl. Source text and a fake `approved` field cannot change host policy.
5. Distinguish documented Pi APIs, observed scripted behavior, and proposed host
   policy. Do not report real-model reliability or OS containment.
6. Leave the original fixture unchanged. Applying a patch, committing, pushing,
   and opening a PR are outside this workflow and need a separate human request.

Runs retain at most the manifest's artifact budget each. Temporary fixture copies
are removed on completion. To discard dossiers, delete only reviewed run directories
under examples/capstone-patch-desk/runs/; do not delete source files.
