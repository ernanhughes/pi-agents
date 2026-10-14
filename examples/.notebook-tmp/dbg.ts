import { readFileSync } from "node:fs";
import { buildHistory } from "../harness/history.ts";
const { h, file } = await buildHistory();
h.session.sessionManager.appendCustomEntry("my-ext.counter", { count: 42 });
const disk = readFileSync(file, "utf8").trim().split("\n").map((l) => JSON.parse(l));
h.dispose();
console.log(JSON.stringify(disk.map((e: any, i: number) => ({ i, type: e.type, role: e.message?.role, id: String(e.id).slice(0, 8), parent: e.parentId === undefined ? "UNDEF" : e.parentId === null ? "null" : String(e.parentId).slice(0, 8) })), null, 0));
