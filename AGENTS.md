# AGENTS.md — instructions for Pi (and for you)

This is the development and executable examples repository for *Pi Agents:
Building on the Coding Agent*. The manuscript and Hugo site live in the separate
`pi` repository. Keep it beginner-readable and tied to the book.

## Grounding and evidence

- Preserve the **Pi 1.0.4** pins in `examples/package.json`. A version change requires coordination with the manuscript's drift protocol.
- Before revising a Pi API claim, read the pinned `pi-coding-agent/docs/` and exported declarations under `examples/node_modules/@earendil-works/`. Declarations win over prose.
- Check `pi --version` and report a mismatch; do not silently ground claims against a newer global install.
- Keep documented contracts, observed results (with run version), and proposed patterns distinct. Narrow unverified claims or record limitations with the corresponding manuscript chapter.
- Tests must exercise Pi rather than reimplement its rules. Faux-provider results are not evidence of real-model quality.
- Add chapter examples where execution backs a book claim; identify other resources as development aids.
- Run `npm run typecheck` and `npm test` from `examples/` for example changes.
- Manuscript checks, evidence regeneration, metadata synchronisation, and notebooks still need book files at repository-relative paths. Read the examples and notebook guides before using those workflows.
- Preserve historical reports; record new evidence only after actual runs with the required inputs.

## Rules for changes here

- Prefer small, commented examples over clever code.
- One concept per file (tool vs event vs command).
- After adding a resource, update README.md layout + learn path if needed.
- Do not add secrets. `auth.json` never belongs in this repo.
- `.pi/` loads only after project trust — keep project skills/prompts safe to trust.
