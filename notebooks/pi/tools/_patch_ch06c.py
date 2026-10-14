"""One-shot patch: chapter 6 exercise should not string-replace the driver."""

from pathlib import Path

path = Path(__file__).resolve().parents[1] / "cells" / "06-chapter.py"
lines = path.read_text(encoding="utf-8").splitlines()

start = next(i for i, l in enumerate(lines) if "DRIVER.replace(" in l and "tools?:" in l)
end = next(i for i in range(start, len(lines)) if '["narrowed"]' in lines[i])
print("replacing lines", start + 1, "..", end + 1)
q = chr(39)
lines[start : end + 1] = [
    f"        'import json as _json{n}'",
    f'        {q}declared = pinb.driver(DRIVER, label="ch06-exercise", timeout=240,{n}\'[:-1] + "'",
    f'        {q}                     env={{"NB_TOOLS": _json.dumps(TOOLS)}})["narrowed"]{n}\'',
]
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("patched", path)