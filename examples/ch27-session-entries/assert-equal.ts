import type { BranchSummaryEntry, CompactionEntry, SessionEntryBase } from "@earendil-works/pi-coding-agent";
import type { Declared } from "./declared.ts";

type Same<A, B> = [A] extends [B] ? ([B] extends [A] ? true : false) : false;
type SameKeys<A, B> = [keyof A] extends [keyof B] ? ([keyof B] extends [keyof A] ? true : false) : false;
const assertTrue = <_T extends true>() => {};

assertTrue<Same<Declared.SessionEntryBase, SessionEntryBase>>();
assertTrue<SameKeys<Declared.SessionEntryBase, SessionEntryBase>>();
assertTrue<Same<Declared.CompactionEntry, CompactionEntry>>();
assertTrue<SameKeys<Declared.CompactionEntry, CompactionEntry>>();
assertTrue<Same<Declared.BranchSummaryEntry, BranchSummaryEntry>>();
assertTrue<SameKeys<Declared.BranchSummaryEntry, BranchSummaryEntry>>();

export {};
