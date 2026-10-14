"""Shared support code for the Pi Agents notebook companions.

Standard library only. This module is *notebook orchestration*, not a Pi
implementation: it locates the book repository, calls the real pinned Pi
examples through Node, and formats what they returned. Every Pi rule it
demonstrates is demonstrated by the book's own code under ``examples/``.

Locating things
---------------
Two markers, both documented in ``README.md``:

* the **repository root** is the nearest ancestor of the current working
  directory that contains *both* ``content/books/pi`` and
  ``examples/node_modules/@earendil-works/pi-coding-agent``. Override with
  the ``PIN_REPO`` environment variable.
* the **notebook directory** is the nearest ancestor containing this file
  (``pinb.py``). Override with ``PIN_NOTEBOOKS``.

Because both searches walk upwards from ``Path.cwd()``, a notebook runs
correctly with the working directory set either to the notebook directory or
to the repository root.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

# --------------------------------------------------------------------------
# The pin. The manuscript is written against this release (see AGENTS.md).
# --------------------------------------------------------------------------
PIN = "1.0.4"
PACKAGES = ("pi-ai", "pi-agent-core", "pi-coding-agent")

JSON_BEGIN = "<<<PINB_JSON"
JSON_END = "PINB_JSON>>>"

REPO_MARKER = Path("content") / "books" / "pi"
EXAMPLES_MARKER = Path("examples") / "node_modules" / "@earendil-works" / "pi-coding-agent"


# --------------------------------------------------------------------------
# Path discovery
# --------------------------------------------------------------------------
class NotebookSetupError(RuntimeError):
    """Raised when the repository cannot be located, with the fix in the message."""


def find_notebook_dir(start: Path | None = None) -> Path:
    override = os.environ.get("PIN_NOTEBOOKS")
    if override:
        p = Path(override).expanduser().resolve()
        if (p / "pinb.py").is_file():
            return p
        raise NotebookSetupError(f"PIN_NOTEBOOKS={p} does not contain pinb.py")
    here = (start or Path.cwd()).resolve()
    for c in (here, *here.parents):
        if (c / "pinb.py").is_file():
            return c
        # Also accept the repository root, so a notebook run from the top of the
        # checkout finds notebooks/pi/ without any configuration.
        nested = c / "notebooks" / "pi"
        if (nested / "pinb.py").is_file():
            return nested
    raise NotebookSetupError(
        "Could not find the notebook directory: neither an ancestor of "
        f"{here} nor its notebooks/pi/ contains pinb.py.\n"
        "Run the notebook from notebooks/pi/, or set PIN_NOTEBOOKS to that directory."
    )


def find_repo_root(start: Path | None = None) -> Path:
    override = os.environ.get("PIN_REPO")
    if override:
        p = Path(override).expanduser().resolve()
        if (p / REPO_MARKER).is_dir() and (p / EXAMPLES_MARKER).is_dir():
            return p
        raise NotebookSetupError(
            f"PIN_REPO={p} is not a Pi book checkout: it must contain "
            f"{REPO_MARKER.as_posix()} and {EXAMPLES_MARKER.as_posix()}.\n"
            "If you have not installed the examples yet:  cd examples && npm ci"
        )
    here = (start or Path.cwd()).resolve()
    for c in (here, *here.parents):
        if (c / REPO_MARKER).is_dir() and (c / EXAMPLES_MARKER).is_dir():
            return c
    raise NotebookSetupError(
        "Could not find the Pi book repository from "
        f"{here}.\n"
        "Expected an ancestor containing both "
        f"{REPO_MARKER.as_posix()} and {EXAMPLES_MARKER.as_posix()}.\n"
        "Fix it with one of:\n"
        "  cd examples && npm ci        # installs the pinned packages\n"
        "  set PIN_REPO=<path to checkout of the pi repository>"
    )


NB_DIR = find_notebook_dir()
REPO = find_repo_root(NB_DIR)
EXAMPLES = REPO / "examples"
MANUSCRIPT = REPO / "content" / "books" / "pi"
METADATA = REPO / "metadata"
EVIDENCE_JSON = EXAMPLES / "evidence.json"
EVIDENCE_MD = EXAMPLES / "EVIDENCE.md"
NODE_MODULES = EXAMPLES / "node_modules" / "@earendil-works"
PI_PKG = NODE_MODULES / "pi-coding-agent"
# Drivers are written here so Node resolves `@earendil-works/*` from
# examples/node_modules. The directory is scratch and is removed by `driver()`.
SCRATCH = EXAMPLES / ".notebook-tmp"


def rel(path: Path) -> str:
    """Repository-relative path, or a `<tmp>/...` label. Never an absolute path."""
    p = Path(path)
    try:
        return p.resolve().relative_to(REPO).as_posix()
    except ValueError:
        pass
    t = Path(tempfile.gettempdir()).resolve()
    try:
        return "<tmp>/" + p.resolve().relative_to(t).as_posix()
    except ValueError:
        return "<path>"


def _flatten_path(path: Path | str) -> str:
    """Reproduce Pi's session-group naming rule, for masking purposes only.

    The rule is documented in chapter 5 and asserted in chapter 2's notebook.
    It is re-implemented here for one narrow reason: a group name is an absolute
    path with its separators replaced, so printing it leaks the machine's layout.
    """
    s = Path(path).as_posix()
    s = re.sub(r"^[/\\]", "", s)
    return re.sub(r"[/\\:]", "-", s)


def mask(text: str) -> str:
    """Replace machine-specific absolute paths in *text* with portable labels."""
    if not text:
        return text
    out = text.replace(str(REPO).replace("\\", "/"), "<repo>").replace(str(REPO), "<repo>")
    t = str(Path(tempfile.gettempdir()))
    out = re.sub(re.escape(t) + r"[\\/][\w.\-]+(?:[\\/][\w.\-]+)*", "<tmp>", out)
    out = out.replace(_flatten_path(t), "<tmp-root>")
    home = os.environ.get("USERPROFILE") or os.environ.get("HOME") or ""
    if home:
        out = out.replace(_flatten_path(Path(home)), "<home>").replace(home, "<home>")
    return out


def mask_obj(value: Any) -> Any:
    """Recursively mask strings in a JSON-shaped payload."""
    if isinstance(value, str):
        return mask(value)
    if isinstance(value, dict):
        return {k: mask_obj(v) for k, v in value.items()}
    if isinstance(value, list):
        return [mask_obj(v) for v in value]
    return value


# --------------------------------------------------------------------------
# Versions and provenance
# --------------------------------------------------------------------------
def node_bin() -> str:
    exe = os.environ.get("PIN_NODE") or shutil.which("node")
    if not exe:
        raise NotebookSetupError(
            "Node.js was not found on PATH.\n"
            "The Pi examples are TypeScript run by Node; this notebook calls them, "
            "it does not reimplement them.\n"
            "Install Node 22.19+ and re-run, or set PIN_NODE to a node executable."
        )
    return exe


def node_version() -> str:
    r = subprocess.run([node_bin(), "--version"], capture_output=True, text=True, timeout=30)
    return r.stdout.strip() or "unknown"


def pi_versions() -> dict[str, str]:
    out: dict[str, str] = {}
    for name in PACKAGES:
        pkg = NODE_MODULES / name / "package.json"
        out[name] = json.loads(pkg.read_text(encoding="utf-8"))["version"] if pkg.is_file() else "missing"
    return out


def pin_holds() -> bool:
    return all(v == PIN for v in pi_versions().values())


def python_version() -> str:
    return sys.version.split()[0]


@dataclass(frozen=True)
class Environment:
    pi: dict[str, str]
    node: str
    python: str
    platform: str

    @property
    def pinned(self) -> bool:
        return all(v == PIN for v in self.pi.values())

    @property
    def evidence_scope(self) -> str:
        """Honest label: what class of thing this notebook produces."""
        return "in_process_runtime + shipped_binary (scripted model)"


def environment() -> Environment:
    return Environment(pi=pi_versions(), node=node_version(), python=python_version(), platform=sys.platform)


def show_environment(title: str = "Environment") -> None:
    env = environment()
    rows = [["manuscript pin (AGENTS.md)", PIN]] + [[f"@earendil-works/{k}", v] for k, v in env.pi.items()]
    rows += [["node", env.node], ["python", env.python], ["platform", env.platform]]
    rows += [
        ["examples tree", "installed" if env.pinned else "DIFFERS FROM PIN"],
        ["model used", "faux (scripted) - no network, no credential, no cost"],
    ]
    print(f"== {title} ==")
    print(table(["component", "value"], rows, indent=""))
    if not env.pinned:
        print()
        print("!" * 72)
        print("The installed Pi packages are NOT the release this book is written against.")
        print("Everything below describes Pi 1.0.4. Re-run with `cd examples && npm ci`.")
        print("!" * 72)


# --------------------------------------------------------------------------
# Subprocess plumbing
# --------------------------------------------------------------------------
@dataclass
class RunResult:
    argv: list[str]
    status: int | None
    stdout: str
    stderr: str
    ms: float
    timed_out: bool = False
    cwd: str = ""

    @property
    def ok(self) -> bool:
        return not self.timed_out and self.status == 0

    def describe(self, limit: int = 1200) -> str:
        head = f"$ {mask(' '.join(self.argv))}\n  exit={self.status} in {self.ms:.0f} ms"
        if self.timed_out:
            head += "  [TIMED OUT]"
        body = ""
        if self.stdout.strip():
            body += "\n--- stdout ---\n" + _clip(self.stdout, limit)
        if self.stderr.strip():
            body += "\n--- stderr ---\n" + _clip(self.stderr, limit)
        return head + body

    def assert_ok(self, what: str) -> "RunResult":
        if self.timed_out:
            raise TimeoutError(f"{what}: the command exceeded its budget\n{self.describe()}")
        if self.status != 0:
            raise RuntimeError(f"{what}: exit status {self.status}\n{self.describe()}")
        return self


def _clip(s: str, limit: int) -> str:
    s = mask(s.rstrip())
    return s if len(s) <= limit else s[:limit] + f"\n... [{len(s) - limit} more characters]"


def _kill_tree(proc: subprocess.Popen) -> None:
    """Kill a subprocess and anything it started (pi spawns no children, but be safe)."""
    if proc.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    else:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(os.getpgid(proc.pid), 9)  # type: ignore[attr-defined]
    with contextlib.suppress(Exception):
        proc.kill()
    with contextlib.suppress(Exception):
        proc.wait(timeout=10)


def run_node(
    args: Sequence[str],
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    stdin: str | None = None,
    timeout: float = 120.0,
) -> RunResult:
    """Run `node <args...>`. Bounded: a timeout kills the whole process tree."""
    argv = [node_bin(), *args]
    full_env = {**os.environ, **(env or {})}
    t0 = time.perf_counter()
    proc = subprocess.Popen(
        argv,
        cwd=str(cwd or EXAMPLES),
        env=full_env,
        stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    timed_out = False
    try:
        out, err = proc.communicate(input=stdin, timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_tree(proc)
        try:
            out, err = proc.communicate(timeout=15)
        except Exception:  # pragma: no cover - the process is gone
            out, err = "", ""
    return RunResult(
        argv=argv,
        status=None if timed_out else proc.returncode,
        stdout=out or "",
        stderr=err or "",
        ms=(time.perf_counter() - t0) * 1000,
        timed_out=timed_out,
        cwd=str(cwd or EXAMPLES),
    )


def node_cwd() -> Path:
    return EXAMPLES


def extract_json(stdout: str) -> Any:
    """Pull the single JSON payload a driver emitted between the PINB markers."""
    i = stdout.find(JSON_BEGIN)
    j = stdout.rfind(JSON_END)
    if i < 0 or j < 0:
        raise ValueError(
            "The driver did not emit a PINB_JSON block. It probably threw before "
            "its last statement.\n" + _clip(stdout, 2000)
        )
    payload = stdout[i + len(JSON_BEGIN) : j].strip()
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:  # pragma: no cover - driver bug
        raise ValueError(f"PINB_JSON payload was not valid JSON: {exc}\n{_clip(payload, 2000)}") from exc


_DRIVER_PREAMBLE = """// Generated at run time by notebooks/pi/pinb.py. Not part of the book; deleted on success.
// It imports the book's own harness. The only substitution anywhere is the model.
//
// Contract: the driver communicates by calling console.log with JSON. Everything it
// logs is captured; one value is returned as-is, several are returned as a list.
const __pinbOut: string[] = [];
const __pinbLog = console.log.bind(console);
console.log = (...a: unknown[]) => { __pinbOut.push(a.map((x) => typeof x === "string" ? x : JSON.stringify(x)).join(" ")); };
"""

_DRIVER_EPILOGUE = """
console.log = __pinbLog;
const __pinbPayload = __pinbOut.length === 1 ? JSON.parse(__pinbOut[0]) : __pinbOut.map((s) => JSON.parse(s));
process.stdout.write(JSON_BEGIN + "\\n" + JSON.stringify(__pinbPayload) + "\\n" + JSON_END + "\\n");
"""


def driver_source(name: str) -> str:
    """Read a driver from ``notebooks/pi/drivers/``.

    Drivers live as real ``.ts`` files so they can be read, reviewed and
    syntax-highlighted as TypeScript rather than as an escaped Python string.
    The cell only chooses the filename; it never contains the driver text.
    """
    path = NB_DIR / "drivers" / name
    if not path.is_file():
        raise FileNotFoundError(f"No driver at {rel(path)}. Drivers live in notebooks/pi/drivers/.")
    return path.read_text(encoding="utf-8")


def driver(
    source: str,
    *,
    label: str = "driver",
    timeout: float = 180.0,
    env: dict[str, str] | None = None,
    keep: bool = False,
) -> Any:
    """Write a TypeScript driver into examples/, run it with Node, return its JSON.

    The driver runs in the same Node package context as the book's tests, so it
    exercises the pinned `@earendil-works` packages and the book's harness
    rather than a Python re-implementation. Its `console.log(JSON.stringify(...))`
    is the return channel; see `_DRIVER_PREAMBLE`.
    """
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", label).strip("-") or "driver"
    SCRATCH.mkdir(parents=True, exist_ok=True)
    path = SCRATCH / f"nb-{slug}.ts"
    banner = (
        f'const JSON_BEGIN = "{JSON_BEGIN}";\nconst JSON_END = "{JSON_END}";\n'
    )
    path.write_text(_DRIVER_PREAMBLE + banner + source.rstrip() + "\n" + _DRIVER_EPILOGUE, encoding="utf-8")
    try:
        result = run_node([rel_to_examples(path)], timeout=timeout, env=env)
        if result.timed_out:
            raise TimeoutError(f"driver '{label}' exceeded {timeout:.0f}s\n{result.describe()}")
        if result.status != 0:
            raise RuntimeError(f"driver '{label}' failed (exit {result.status})\n{result.describe()}")
        payload = extract_json(result.stdout)
        if isinstance(payload, list) and not payload:
            raise ValueError(f"driver '{label}' logged nothing; a driver must console.log its JSON result")
        return mask_obj(payload)
    finally:
        if not keep and path.is_file():
            path.unlink()


def rel_to_examples(path: Path) -> str:
    """A path Node can open, relative to examples/ (handles Windows and POSIX)."""
    return Path(os.path.relpath(path, EXAMPLES)).as_posix()


# --------------------------------------------------------------------------
# Running the book's own tests
# --------------------------------------------------------------------------
@dataclass
class TapResult:
    tests: list[dict] = field(default_factory=list)
    ms: float = 0.0
    timed_out: bool = False
    status: int | None = 0
    raw: str = ""

    @property
    def passed(self) -> int:
        return sum(1 for t in self.tests if t["ok"])

    @property
    def failed(self) -> int:
        return sum(1 for t in self.tests if not t["ok"] and not t.get("skip"))

    @property
    def skipped(self) -> int:
        return sum(1 for t in self.tests if t.get("skip"))

    @property
    def ok(self) -> bool:
        return not self.timed_out and self.failed == 0

    def find(self, fragment: str) -> dict | None:
        frag = fragment.lower()
        for t in self.tests:
            if frag in t["name"].lower():
                return t
        return None


_TAP_LINE = re.compile(r"^(ok|not ok)\s+(\d+)\s*-\s*(.*)$")


def parse_tap(text: str) -> TapResult:
    tests: list[dict] = []
    pending_skip = False
    for line in text.splitlines():
        if line.strip().startswith("# SKIP") or line.strip().startswith("# skip"):
            pending_skip = True
            continue
        m = _TAP_LINE.match(line)
        if m:
            tests.append({"ok": m.group(1) == "ok", "name": m.group(3).strip(), "skip": pending_skip})
            pending_skip = False
        elif line.strip().startswith("1.."):
            continue
    return TapResult(tests=tests, raw=text)


def run_tests(patterns: str | Iterable[str], *, timeout: float = 300.0, label: str = "") -> TapResult:
    """Run one or more of the book's test files with Node's own test runner.

    `patterns` are paths relative to examples/, e.g.
    ``"ch04-budget/*.test.ts"``. This is the chapter's canonical evidence
    executed, not a re-implementation of it.
    """
    if isinstance(patterns, str):
        patterns = [patterns]
    files: list[str] = []
    for pat in patterns:
        if "*" in pat:
            base = EXAMPLES / pat.split("*")[0].rstrip("/\\")
            hits = sorted(base.glob("*.test.ts")) if base.is_dir() else []
            files += [rel_to_examples(h) for h in hits]
        else:
            files.append(pat)
    if not files:
        raise FileNotFoundError(f"No test files matched {patterns!r} under examples/")
    missing = [f for f in files if not (EXAMPLES / f).is_file()]
    if missing:
        raise FileNotFoundError(f"Not found under examples/: {missing}")

    with tempfile.TemporaryDirectory(prefix="pinb-tap-") as td:
        dest = Path(td) / "report.tap"
        r = run_node(
            [
                "--test",
                "--test-reporter=tap",
                f"--test-reporter-destination={dest}",
                *files,
            ],
            timeout=timeout,
        )
        text = dest.read_text(encoding="utf-8", errors="replace") if dest.is_file() else ""
    out = parse_tap(text)
    out.timed_out = r.timed_out
    out.status = r.status
    out.ms = r.ms
    return out


def show_tap(result: TapResult, *, files: str, show: str | None = None, limit: int = 40) -> None:
    """Report a canonical test run, optionally highlighting tests matching `show`."""
    files_label = files if isinstance(files, str) else ", ".join(files)
    print(f"$ node --test {files_label}")
    verdict = "PASS" if result.ok else ("FAIL" if not result.timed_out else "TIMED OUT")
    print(
        f"  {verdict}  {result.passed} passed, {result.failed} failed, "
        f"{result.skipped} skipped  in {result.ms:.0f} ms"
    )
    if show:
        frag = show.lower()
        print()
        print(f"  tests matching {show!r}:")
        for t in result.tests:
            if frag in t["name"].lower():
                print(f"    {'ok ' if t['ok'] else 'NOT ok'}  {t['name']}")
    if result.raw.strip():
        bad = [ln for ln in result.raw.splitlines() if ln.startswith("not ok")]
        for ln in bad[:10]:
            print("    " + mask(ln))
    assert result.ok, f"the book's own tests for {files_label} did not pass"


# --------------------------------------------------------------------------
# Evidence ledger
# --------------------------------------------------------------------------
def evidence_rows(chapter: str | None = None) -> list[dict]:
    """Rows from examples/evidence.json - the book's claim ledger, read as data."""
    if not EVIDENCE_JSON.is_file():
        raise FileNotFoundError(f"Missing {rel(EVIDENCE_JSON)}. Run `npm run evidence` in examples/.")
    data = json.loads(EVIDENCE_JSON.read_text(encoding="utf-8"))
    rows = data.get("rows", [])
    if chapter is None:
        return rows
    key = str(chapter).zfill(2)
    return [r for r in rows if str(r.get("chapter", "")).zfill(2) == key]


def evidence_versions() -> dict[str, str]:
    data = json.loads(EVIDENCE_JSON.read_text(encoding="utf-8"))
    return data.get("versions", {})


# --------------------------------------------------------------------------
# Manuscript access
# --------------------------------------------------------------------------
def chapter_file(number: int | str) -> Path:
    return MANUSCRIPT / f"{int(number):02d}-chapter.md"


def chapter_text(number: int | str) -> str:
    return chapter_file(number).read_text(encoding="utf-8")


def chapter_title(number: int | str) -> str:
    m = re.search(r'^title\s*=\s*"([^"]+)"', chapter_text(number), re.M)
    return m.group(1) if m else f"chapter {int(number):02d}"


def chapter_headings(number: int | str) -> list[str]:
    return re.findall(r"^(#{2,3})\s+(.*)$", chapter_text(number), re.M).__iter__().__length_hint__() if False else [
        m.group(2).strip() for m in re.finditer(r"^#{2,3}\s+(.*)$", chapter_text(number), re.M)
    ]


def chapter_metadata(number: int | str) -> str:
    p = METADATA / f"{int(number):02d}-chapter.yaml"
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def metadata_block(number: int | str, key: str) -> str:
    """Return the verbatim text of a top-level block in the chapter's metadata.

    Deliberately text, not parsed YAML: the notebook shows the file as it is,
    rather than a lossy dict that hides what the file actually says.
    """
    text = chapter_metadata(number)
    m = re.search(rf"^{re.escape(key)}:\s*$", text, re.M)
    if not m:
        return ""
    rest = text[m.end() :].lstrip("\n")
    lines = rest.splitlines()
    out: list[str] = []
    for line in lines:
        if line.strip() and not line.startswith((" ", "\t", "-")):
            break
        out.append(line)
    return "\n".join(out).rstrip()


# --------------------------------------------------------------------------
# Published browser experiences (chapters 31 and 39)
# --------------------------------------------------------------------------
def experience_dir(chapter: int | str) -> Path | None:
    """The published browser-experience directory for a chapter, if present.

    The two experiences live in the site repository (``programmer.ie``), which is
    not part of this checkout. Set ``PIN_EXPERIENCES`` to that repo's
    ``content/tools/ai/pi`` directory; otherwise a sibling checkout is tried and,
    if it is absent, the notebook reports the historical recording as NOT
    INSPECTED rather than inventing it.

    A returned directory is a *recording*. It is evidence about the release it was
    captured on (1.0.2 for both published experiences), not about this pin.
    """
    override = os.environ.get("PIN_EXPERIENCES")
    candidates: list[Path] = []
    if override:
        candidates.append(Path(override).expanduser().resolve())
    candidates.append(REPO.parent / "programmer.ie" / "content" / "tools" / "ai" / "pi")
    candidates.append(REPO.parent / "programmer.ie.notebooks" / ".." / "programmer.ie" / "content" / "tools" / "ai" / "pi")
    for base in candidates:
        d = base / f"{int(chapter):02d}-chapter"
        if (d / "recorded-trace.json").is_file():
            return d
    return None


def read_trace(path: Path) -> dict:
    """Read a ``book-evidence-trace/1`` recording without interpreting it."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# Presentation
# --------------------------------------------------------------------------
def table(headers: Sequence[str], rows: Sequence[Sequence[Any]], *, indent: str = "", max_width: int = 74) -> str:
    """A fixed-width table. Small enough to read in a notebook output."""
    cells = [[("" if c is None else str(c)) for c in r] for r in rows]
    widths = [len(h) for h in headers]
    for r in cells:
        for i, c in enumerate(r):
            if i < len(widths):
                widths[i] = max(widths[i], len(c))
    widths = [min(w, max_width) for w in widths]

    def fit(s: str, w: int) -> str:
        return s if len(s) <= w else s[: max(0, w - 1)] + "\u2026"

    lines = [indent + "  ".join(fit(h, w) for h, w in zip(headers, widths)).rstrip()]
    lines.append(indent + "  ".join("-" * w for w in widths).rstrip())
    for r in cells:
        padded = [fit(c, w) for c, w in zip(r, widths)]
        lines.append(indent + "  ".join(padded).rstrip())
    return "\n".join(lines)


def md_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    """A GitHub-flavoured Markdown table, for markdown cells and reports."""
    out = ["| " + " | ".join(str(h) for h in headers) + " |"]
    out.append("|" + "|".join("---" for _ in headers) + "|")
    for r in rows:
        out.append("| " + " | ".join("" if c is None else str(c).replace("|", "\\|") for c in r) + " |")
    return "\n".join(out)


@dataclass
class Check:
    label: str
    passed: bool
    detail: str = ""


def check(label: str, condition: bool, detail: str = "") -> Check:
    return Check(label, bool(condition), detail)


def show_checks(checks: Sequence[Check], *, title: str = "Assertions", strict: bool = True) -> None:
    rows = [[("PASS" if c.passed else "FAIL"), c.label, c.detail] for c in checks]
    print(f"== {title} ==")
    print(table(["", "assertion", "observed"], rows, indent=""))
    failed = [c for c in checks if not c.passed]
    print(f"\n{len(checks) - len(failed)}/{len(checks)} assertions held.")
    if strict:
        assert not failed, "assertions failed: " + "; ".join(c.label for c in failed)


def diagram(lines: Iterable[str], *, title: str = "") -> str:
    """Print a fixed-width ASCII diagram.

    Markdown cells carry the Mermaid source as well; this is the fallback that
    renders in every notebook viewer, including ones without Mermaid support.
    """
    body = list(lines)
    width = max((len(x) for x in body), default=0)
    print()
    if title:
        print(f"+-- {title} " + "-" * max(0, width - len(title) - 1) + "+")
    print("+" + "-" * (width + 2) + "+")
    for line in body:
        print("| " + line.ljust(width) + " |")
    print("+" + "-" * (width + 2) + "+")


def note(title: str, body: str = "") -> None:
    bar = "=" * min(74, max(20, len(title) + 4))
    print()
    print(bar)
    print(f"  {title}")
    if body:
        for line in body.strip().splitlines():
            print(f"  {line}")
    print(bar)


def bars(rows: Sequence[tuple[str, float]], *, width: int = 34, unit: str = "") -> str:
    """A fixed-width bar chart.

    Used where a quantity genuinely grows across a sequence. Where a number is
    the point and its shape is not, `table` is the clearer choice - a plot is
    not required by anything in this set.
    """
    if not rows:
        return "(no rows)"
    top = max(abs(v) for _, v in rows) or 1.0
    out = []
    for label, v in rows:
        n = max(1, int(round(abs(v) / top * width))) if v else 0
        out.append(f"{label:>10} | {'#' * n:<{width}} {v:g}{unit}")
    return "\n".join(out)


def mermaid(source: str) -> str:
    """A markdown cell: the Mermaid source, fenced so it is always readable."""
    return (
        "```mermaid\n" + source.strip() + "\n```\n\n"
        "*Not every notebook renderer draws Mermaid. The cell below draws the same "
        "thing as fixed-width text, which always renders.*"
    )


# --------------------------------------------------------------------------
# Isolation
# --------------------------------------------------------------------------
@contextlib.contextmanager
def workspace(prefix: str = "pinb-"):
    """A fresh temporary directory. Every notebook write goes inside one of these."""
    p = Path(tempfile.mkdtemp(prefix=prefix))
    try:
        yield p
    finally:
        shutil.rmtree(p, ignore_errors=True)


def isolated_env(agent_dir: Path, extra: dict[str, str] | None = None) -> dict[str, str]:
    """The environment the book's CLI harness uses.

    PI_CODING_AGENT_DIR keeps a run away from the reader's own Pi configuration,
    PI_OFFLINE=1 keeps it off the network, and PI_FAUX_SCRIPT is how the shipped
    binary is given a scripted model instead of a real one.
    """
    return {
        "PI_CODING_AGENT_DIR": str(agent_dir),
        "PI_OFFLINE": "1",
        "PI_SKIP_VERSION_CHECK": "1",
        "PI_TELEMETRY": "0",
        **(extra or {}),
    }


# --------------------------------------------------------------------------
# Optional live-provider sections
# --------------------------------------------------------------------------
def live_credentials() -> dict[str, bool]:
    """Which provider keys are *present*. Values are never read or printed."""
    names = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "GEMINI_API_KEY", "PIN_LIVE")
    return {n: bool(os.environ.get(n)) for n in names}


def live_status() -> tuple[bool, str]:
    """(enabled, reason). Optional sections must call this and report honestly."""
    if os.environ.get("PIN_LIVE") != "1":
        creds = [k for k, v in live_credentials().items() if v]
        why = "PIN_LIVE=1 is not set" + (f" (keys present: {', '.join(creds)})" if creds else "")
        return False, why
    if not any(live_credentials().values()):
        return False, "PIN_LIVE=1 is set but no provider key is present"
    return True, "PIN_LIVE=1 and a provider key is present"


def unrun(title: str, reason: str) -> None:
    print(f"NOT RUN - {title}")
    print(f"  reason: {reason}")
    print("  No output is shown because none was produced. This cell makes no claim.")


# --------------------------------------------------------------------------
# Self-check, used by every notebook's setup cell
# --------------------------------------------------------------------------
def self_check(*, need_node: bool = True) -> dict[str, Any]:
    env = environment()
    status = {
        "repo_root": "resolved",
        "notebook_dir": "resolved",
        "pin_matches_manuscript": env.pinned,
        "node": node_version() if need_node else "not needed",
        "python": env.python,
        "claim_ledger": EVIDENCE_JSON.is_file(),
        "credentials_required": False,
    }
    assert env.pinned, (
        f"installed Pi packages {env.pi} are not the pinned {PIN}. "
        "Run `cd examples && npm ci` before trusting anything in this notebook."
    )
    return status