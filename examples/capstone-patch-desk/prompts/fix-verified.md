---
description: Walk through the offline Pi Patch Desk capstone and review its evidence
argument-hint: "[success|injection]"
---
Guide me through the Pi Patch Desk teaching fixture using scenario ${1:-success}.
Read examples/capstone-patch-desk/README.md from the repository root first.
Run the deterministic host with `npm run capstone -- --scenario ${1:-success}`
from examples/, or tell me to enter `/patch-desk ${1:-success}` if that extension
is loaded. Do not edit the original fixture or use a real provider to solve it.
Read the generated review.md, patch.diff, tests.json, and evidence.json.
Explain the reproduced failure, completed Pi tools, host checks, source references,
and which properties were not measured. The model's prose cannot approve a patch.
Ask for a separate human decision before applying a patch anywhere.
