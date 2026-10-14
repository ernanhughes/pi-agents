// Independent host-owned checks: changing the fixture tests cannot weaken these.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";

const { parseRecords } = await import(pathToFileURL(process.argv[2]).href);
for (const blank of ["", " ", "\t", "  \t"]) {
  assert.deepEqual(parseRecords(`\n${blank}\nname=Ada\r\n${blank}\r\nrole=developer\n`), { name: "Ada", role: "developer" });
  assert.deepEqual(parseRecords(blank), {});
}
for (const invalid of ["broken", "Name=Ada", "name=", "name=Ada=extra", " name=Ada", "name=Ada "]) {
  // Trailing whitespace in a VALUE remains valid under the original grammar.
  if (invalid === "name=Ada ") assert.deepEqual(parseRecords(invalid), { name: "Ada " });
  else assert.throws(() => parseRecords(invalid), /Invalid record/);
}
console.log("Host acceptance checks passed: blank lines and original nonblank grammar.");
