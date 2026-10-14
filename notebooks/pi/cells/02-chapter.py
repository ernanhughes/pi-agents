"""Chapter 02 - Install, First Session, First Task."""

from _common import establishes, heading, setup_cells, sources_and_limits

TITLE = "Install, First Session, First Task"
QUESTION = """The working directory is the identity key. **What does it decide** —
and can you see it decide the same thing twice, from two runs?

The chapter opens with installing Pi, logging in, and running a first task. The
install is the least interesting part and the one you cannot check without a
network. The identity key is the part you *can*: it decides what Pi discovers
underneath you and which saved conversation `--continue` resumes."""

CELLS = [
    ("md", heading(2, TITLE, QUESTION)),
    (
        "md",
        establishes(
            [
                "The bundled `pi` executable in `examples/node_modules/` reports the "
                "pinned version. This is the same file `npm exec pi` runs, resolved "
                "through the package's own `bin` mapping.",
                "A session is written to a directory whose name is derived from the "
                "working directory: the leading separator is dropped and `/`, `\\` and "
                "`:` become `-`.",
                "Two runs in two different working directories, sharing one agent "
                "directory, land in **two different session groups** — so `--continue` "
                "cannot cross between them.",
            ],
            [
                "**Nothing about installing Pi for a reader.** No npm registry, no "
                "`npm install -g`, no version-check service. This notebook exercises "
                "the pinned package already in the repository.",
                "**Nothing about logging in.** There is no credential and no OAuth "
                "flow here; chapter 3 is where a credential's source matters.",
                "**Nothing about task phrasing.** The chapter contrasts *\"Fix the "
                "bug.\"* with a scoped task, and `metadata/10-chapter.yaml` records "
                "that the effect of phrasing on completion rate **is not measured**. "
                "It cannot be measured with a scripted model, and it is not measured "
                "here.",
            ],
        ),
    ),
    *setup_cells(
        2,
        mode="**Run** — the shipped `pi` binary, offline, with the book's scripted provider.",
        scope="`shipped_binary`. This chapter has no example directory of its own; it runs "
        "against the bundled executable through `examples/harness/cli.ts`.",
    ),
    (
        "md",
        """## Baseline: which executable, and which version

`harness/cli.ts` resolves the binary through the pinned package's own `bin`
mapping rather than hard-coding a path into `dist/`. That matters: `dist/cli.js`
is an internal module the bundle happens to contain, so running it would test a
different program from the one you install.""",
    ),
    (
        "code",
        'ABOUT = pinb.driver_source("ch02-version.ts")\n'
        'about = pinb.driver(ABOUT, label="ch02-version", timeout=120)\n'
        'print(pinb.table(["property", "value"], [[k, v] for k, v in about.items()], indent=""))\n'
        'print()\n'
        'assert about["exit"] == 0 and about["reportedVersion"] == pinb.PIN, (\n'
        '    f"the bundled binary reported {about[\'reportedVersion\']!r}, not the pin {pinb.PIN}")\n'
        'print(f"the shipped executable in this repository is Pi {about[\'reportedVersion\']}")',
    ),
    (
        "md",
        """## Experiment: the working directory as identity key

Two runs, same agent directory, **different working directories**. The
question is not whether both succeed — it is whether the session files land in
different places, and what that makes `--continue` mean.

The run below is offline (`PI_OFFLINE=1`), writes nothing to your own Pi
configuration (`PI_CODING_AGENT_DIR` points at a fresh temporary directory) and
uses the book's scripted provider.""",
    ),
    (
        "code",
        'IDENTITY = pinb.driver_source("ch02-identity.ts")\n'
        'identity = pinb.driver(IDENTITY, label="ch02-identity", timeout=240)\n'
        "for r in identity[\"runs\"]:\n"
        '    print(f"run in cwd \\"{r[\'cwdShape\']}\\": exit={r[\'exit\']}, stdout={r[\'stdout\']!r}")\n'
        '    print(f"  session groups afterwards: {r[\'groupNames\']}")\n'
        "\n"
        "print()\n"
        'print(pinb.table(["session group", "file"], [[f["group"], f["file"]] for f in identity["sessionFiles"]], indent=""))',
    ),
    (
        "md",
        """Both runs printed their answer and exited 0. The interesting row is the
group directory name: it is the working directory with its separators flattened,
and the two runs produced **two** of them.

That is the whole answer to "which conversation does `--continue` resume?" —
it resumes the one belonging to *this directory*, and there is no global "last
session" to fall back on.""",
    ),
    (
        "code",
        'groups = sorted({g["group"] for g in identity["sessionFiles"]})\n'
        'names = sorted({f["file"] for f in identity["sessionFiles"]})\n'
        'filename_pattern = __import__("re").compile(r"^\\d{4}-\\d\\d-\\d\\dT[\\d:-]+Z_[0-9a-f-]{36}\\.jsonl$")\n'
        "\n"
        "pinb.show_checks([\n"
        '    pinb.check("both runs succeeded", all(r["exit"] == 0 for r in identity["runs"]),\n'
        '               str([r["exit"] for r in identity["runs"]])),\n'
        '    pinb.check("each run produced its own session group", len(groups) == 2, str(len(groups)) + " groups"),\n'
        '    pinb.check("no group name contains a path separator or a colon",\n'
        '               not any(set(g) & set("/\\\\:") for g in groups), "separators flattened"),\n'
        '    pinb.check("every session file name matches the documented shape",\n'
        '               all(filename_pattern.match(n) for n in names), "ISO timestamp + UUID"),\n'
        "])",
    ),
    (
        "md",
        """## Contrasting case: the rule is not injective

The group names above are derived from temporary paths that differ by more than
their label. Strip both back to the label and the rule is visible:
`^[/\\\\]` removed, then every `/`, `\\` and `:` replaced with `-`, wrapped in `--`.

A collision is therefore *possible*: `a/b` and `a-b` flatten to the same string.
The book states the rule; it does not claim the rule is injective. The cell below
checks that, and it is the reason a session directory name is not something to
parse.""",
    ),
    (
        "md",
        """## Your turn: predict, then run

**Predict first.** If two temporary working directories differed only by one
character — `a-b` and `a/b` — how many session groups would there be?

**Then run it.** The cell applies the documented flattening rule to the two names.""",
    ),
    (
        "code",
        'LABELS = ["a-b", "a/b"]\n'
        "\n"
        "\n"
        "def flatten(path: str) -> str:\n"
        '    """The documented session-group rule, restated so the collision is visible.\n'
        "\n"
        "    The authority for the rule is the session file written above; this only\n"
        "    applies it to names the notebook chose.\n"
        '    """\n'
        "    import re\n"
        "\n"
        '    body = re.sub(r"^[/\\\\]", "", path.replace("\\\\", "/"))\n'
        '    return "--" + re.sub(r"[/\\\\:]", "-", body) + "--"\n'
        "\n"
        "\n"
        'flat = [flatten(f"/tmp/proj/{x}") for x in LABELS]\n'
        'print("paths         :", [f"/tmp/proj/{x}" for x in LABELS])\n'
        'print("flattened     :", flat)\n'
        'print("distinct      :", sorted(set(flat)))\n'
        'print("predicted groups:", len(set(flat)))\n'
        "print()\n"
        'assert len(set(flat)) == 1, "the rule is not injective: two paths, one session group"\n'
        'print("held: the rule is documented, injectivity is not. Two paths can share a group.")',
    ),
    (
        "md",
        """## Interpretation

The practical decision this chapter supports: **treat the directory as part of
the task's identity**. Two repositories are two conversations, and switching
directories mid-task means starting a new session rather than continuing the old
one. That is also why chapter 8's project trust, chapter 7's settings layering
and chapter 28's context-file discovery are all keyed on the same directory — the
identity key is chosen before any of them run.

### What this chapter does not settle

* The install itself. Three installers exist (npm, a managed installer, a nix
  profile since 1.0.1); choosing between them is a packaging decision this
  notebook has no opinion about.
* Task shape. *\"Fix the bug.\"* and a scoped task differ, but no measurement in
  this book establishes by how much, and the faux provider could not produce one.
* Native Windows and Termux setup, which `metadata/02-chapter.yaml` records as
  outside the chapter's scope.""",
    ),
    (
        "md",
        sources_and_limits(
            chapter=2,
            mode="**Run** — the bundled `pi` executable and two offline runs through "
            "`examples/harness/cli.ts`.",
            scope="`shipped_binary`. This chapter has no example directory, so there are no "
            "ledger rows for it; the evidence here is this notebook's own execution, which is "
            "reported as such.",
            provenance=[
                "**Ran** `pi --version` and `pi --help` on the binary resolved through the "
                "pinned package's `bin` mapping (`shipped_binary`).",
                "**Ran** two scripted `--print` runs with `session: true`, in two fresh working "
                "directories, sharing one fresh `PI_CODING_AGENT_DIR`, with `PI_OFFLINE=1`.",
                "**Read** the session-file naming rule in chapter 5's example assertions and "
                "the harness source that implements it.",
            ],
            limits=[
                "**The temporary paths are machine-shaped.** The flattening rule is the "
                "chapter's; the specific group names depend on where the OS put the temporary "
                "directory. That is why only the *count* and the *character set* are asserted, "
                "not the names.",
                "**No session was resumed.** Two runs in two directories show that sessions are "
                "kept apart. Showing that `--continue` picks the right one needs a third run "
                "in a directory that already has a session, which is left as the reader's "
                "exercise rather than asserted here.",
                "**The model is scripted.** Every run answered `ok from <label>` because the "
                "faux provider said so. Nothing here is evidence about model behaviour, and "
                "nothing about a real task.",
            ],
            unrun=[
                "**Installing Pi** from npm, the managed installer, or the nix profile. "
                "Documented in the chapter; not run here.",
                "**Logging in** via `/login` or an OAuth flow. No credential is used anywhere "
                "in this set.",
                "**A `--continue` invocation** in a directory that already holds a session.",
            ],
        ),
    ),
]
