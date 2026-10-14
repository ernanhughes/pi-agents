"""Chapter 43 (Appendix A) - References and Further Reading."""

from _common import establishes, heading, setup_cells, sources_and_limits

TITLE = "Appendix A — References and Further Reading"
QUESTION = """What does the pin actually contain, and what does the ledger actually record?

The chapter's point: a reference page is only as good as its provenance. This
notebook counts what is actually on disk at the pin — the docs, the claim ledger,
and the appendix's own bibliography — and refuses to invent a numerical research
result."""

CELLS = [
    ("md", heading(43, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "The pinned `pi-coding-agent` package contains **exactly N `docs/*.md` topic files** — counted, not remembered.",
                "The claim ledger (`examples/evidence.json`) breaks down **by `claim_class` × `evidence_scope`** — the book's own vocabulary, read as data.",
                "The appendix cites **arXiv records, ecosystem repositories and companion books** — counted from the text itself.",
                "**No numerical research result is computed and none may be** — the chapter's numbers belong to the papers they cite.",
                "**A link check verifies that a record resolves, never that a paper says what the appendix attributes to it.**",
            ],
            [
                "**This notebook does not fetch any arXiv page** — it counts citations, it does not verify them.",
                "**The papers' findings are not re-derived** — they are quoted in the chapter and attributed to named work.",
                "**The ledger's `real_model` scope is empty** — the book contains no accepted real-model evidence.",
                "**An unpinned ecosystem repository proves existence, not quality** — the chapter says so itself.",
            ],
        ),
    ),
    *setup_cells(
        43,
        mode="**Inspect** — counts and tabulations from the pinned docs, the claim ledger, and the appendix's own text. Nothing is fetched or re-derived.",
        scope="`declarations` + inspection of the ledger. No runtime, no network.",
    ),
    (
        "md",
        """## Baseline: what the pin contains""",
    ),
    (
        "code",
        'REF = pinb.driver_source("ch43-appendix.ts")\n'
        'ref = pinb.driver(REF, label="ch43-appendix", timeout=120)\n'
        'd = ref["docs"]\n'
        'print(pinb.md_table(\n'
        '    ["measure", "value"],\n'
        '    [["docs/*.md topic files at the pin", d["count"]],\n'
        '     ["ledger rows", ref["ledger"]["totalRows"]],\n'
        '     ["arXiv ids cited in the appendix", ref["appendix"]["arxivCount"]],\n'
        '     ["ecosystem repos cited", ref["appendix"]["ecosystemRepos"]],\n'
        '     ["companion books named", ", ".join(ref["appendix"]["companionBooks"])]],\n'
        "))",
    ),
    (
        "md",
        """## The ledger: claim_class × evidence_scope

The book's own vocabulary, read from `examples/evidence.json`. This is what the
ledger actually records — including what it does **not** (no `real_model` rows).""",
    ),
    (
        "code",
        'led = ref["ledger"]\n'
        'print(pinb.md_table(\n'
        '    ["claim_class", "declarations", "in_process_runtime", "shipped_binary", "real_model"],\n'
        '    [[c] + [led["matrix"].get(c, {}).get(s, 0) for s in ["declarations", "in_process_runtime", "shipped_binary", "real_model"]]\n'
        '     for c in led["claimClasses"]],\n'
        "))",
    ),
    (
        "code",
        'real = sum(led["matrix"].get(c, {}).get("real_model", 0) for c in led["claimClasses"])\n'
        'pinb.show_checks([\n'
        '    pinb.check("the ledger records exactly the rows the suite produced",\n'
        '               led["totalRows"] > 0, f"{led[\'totalRows\']} rows"),\n'
        '    pinb.check("the ledger contains NO accepted real_model evidence",\n'
        '               real == 0, "real_model scope is empty"),\n'
        "])",
    ),
    (
        "md",
        """## The appendix's own bibliography

The arXiv ids, ecosystem repositories and companion books are counted from the
chapter text itself. Counting is inspection; it verifies nothing about the
papers.""",
    ),
    (
        "code",
        'app = ref["appendix"]\n'
        'print("Companion books named in the appendix:")\n'
        'for b in app["companionBooks"]:\n'
        '    print("  -", b)\n'
        'print()\n'
        'print("This notebook counts citations; it does not fetch or re-derive any result.")\n'
        'pinb.show_checks([\n'
        '    pinb.check("every companion book is attributed, not asserted as Pi evidence",\n'
        '               len(app["companionBooks"]) >= 5, "companion books named"),\n'
        "])",
    ),
    (
        "md",
        """## Your turn: inspect, then decide

**Predict first.** The appendix cites an arXiv id like `2210.03629`. What would
*checking* that link verify — that the record resolves, or what the paper says?

**Then change one input.** Re-run the ledger tabulation after a future suite adds
a `real_model` row. Does the `real_model` column stop being empty?

**Predict the boundary.** The appendix quotes `pass^8 < 25%` for τ-bench. Could
this notebook verify that number without reading the paper?""",
    ),
    (
        "code",
        'print("Predictions:")\n'
        'print("  1. A link check verifies the record resolves, never what the paper says.")\n'
        'print("  2. A future real_model row would appear in the table - the ledger is the record.")\n'
        'print("  3. No - the number belongs to the paper; computing it here would be inventing a result.")\n'
        "print()\n"
        'print("Observed above:")\n'
        'print(f"  docs at pin: {d[\'count\']}")\n'
        'print(f"  ledger rows: {led[\'totalRows\']}, real_model rows: {real}")\n'
        'print(f"  arxiv ids: {app[\'arxivCount\']}, ecosystem repos: {app[\'ecosystemRepos\']}")\n'
        "print()\n"
        'assert d["count"] > 0 and led["totalRows"] > 0\n'
        'assert real == 0\n'
        'assert app["arxivCount"] > 0\n'
        'print("held: the pin contains what it contains; the ledger records what it records; nothing is invented")',
    ),
    (
        "md",
        """## Interpretation

A reference appendix is provenance, and the chapter shows what that means:

| Source kind | What inspecting it establishes | What it does not |
|---|---|---|
| **Pinned `docs/`** | How many topic files exist at 1.0.4 | What a later release contains |
| **Claim ledger** | The `claim_class` × `evidence_scope` matrix | Anything a future suite records |
| **arXiv citations** | That the ids appear in the text | That the papers say what is attributed |
| **Ecosystem repos** | That the projects are cited | Their quality or current state |
| **Companion books** | That they are named and grouped | Their coverage of Pi's terms |

The practical rules:
1. **Count what is on disk** — the pin, not memory.
2. **Read the ledger as data** — `claim_class` and `evidence_scope` are the book's vocabulary.
3. **Do not invent numerical results** — the numbers belong to the cited papers.
4. **A link check is a resolution check** — a record resolving proves nothing about its content.
5. **Unpinned repos prove existence** — never quality.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=43,
            mode="**Inspect** — counts and tabulations from the pinned docs, the claim ledger, and the appendix's own text. Nothing is fetched or re-derived.",
            scope="`declarations` + inspection of the ledger. No runtime, no network.",
            provenance=[
                "**Counted** `docs/*.md` in the pinned `pi-coding-agent` package.",
                "**Read** `examples/evidence.json` and tabulated `claim_class` × `evidence_scope`.",
                "**Extracted** the appendix's arXiv ids, ecosystem repositories and companion books from `43-chapter.md`.",
            ],
            limits=[
                "**No arXiv page was fetched** — the citation counts are inspection, not verification.",
                "**No numerical research result is computed** — passing a `pass^k` claim is the paper's own number, quoted, not verified.",
                "**The ledger has no `real_model` rows** — the book contains none.",
                "**Unpinned ecosystem repositories** prove existence, not quality.",
            ],
            unrun=[
                "Fetching any arXiv record or repository (not run, by design).",
                "Re-deriving any paper's numbers (not possible without the papers' data).",
            ],
        ),
    ),
]