"""Lint the cell sources for the `""` typo at the end of a markdown cell."""

import glob
from pathlib import Path

Q = chr(34)
bad = 0
for f in sorted(glob.glob("cells/*.py")):
    for i, line in enumerate(Path(f).read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.rstrip()
        if stripped.endswith(Q + Q + ",") and Q * 3 not in stripped:
            print(f"{f}:{i}  {stripped!r}")
            bad += 1
print("suspicious lines:", bad)