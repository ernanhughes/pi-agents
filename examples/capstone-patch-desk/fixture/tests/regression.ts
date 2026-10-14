import assert from "node:assert/strict";
import { test } from "node:test";
import { parseRecords } from "../src/records.ts";

test("valid records", () => {
  assert.deepEqual(parseRecords("name=Ada\nrole=developer"), { name: "Ada", role: "developer" });
});

test("blank lines between records are ignored (the reported bug)", () => {
  assert.deepEqual(parseRecords("name=Ada\n\nrole=developer"), { name: "Ada", role: "developer" });
});

test("malformed nonblank records are rejected", () => {
  for (const input of ["broken", "Name=Ada", "name=", "name=Ada=extra"]) {
    assert.throws(() => parseRecords(input), /Invalid record/);
  }
});
