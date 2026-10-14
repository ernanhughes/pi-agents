// Session entry shapes exactly as chapters 5, 23 and 24 declare them, compared with the
// exported ones by assert-equal.ts.
import type { SystemMessage, Usage } from "@earendil-works/pi-ai";

export namespace Declared {
	export interface SessionEntryBase {
	  type: string;
	  id: string;                // Usually an 8-char hex ID; may fall back to a full UUID
	  parentId: string | null;   // null for a root entry
	  timestamp: string;         // ISO timestamp
	}

	export interface CompactionEntry<T = unknown> {
	  type: "compaction";
	  id: string;
	  parentId: string | null;
	  timestamp: string;
	  summary: string;
	  firstKeptEntryId: string;
	  tokensBefore: number;
	  usage?: Usage;       // LLM usage that generated the summary
	  fromHook?: boolean;  // true if provided by extension (legacy field name)
	  details?: T;         // implementation-specific data
	  systemMessage?: SystemMessage; // complete prompt and tool state at this boundary
	}

	// Default compaction uses this for details:
	export interface CompactionDetails {
	  readFiles: string[];
	  modifiedFiles: string[];
	}

	export interface BranchSummaryEntry<T = unknown> {
	  type: "branch_summary";
	  id: string;
	  parentId: string | null;
	  timestamp: string;
	  summary: string;
	  fromId: string;      // Entry we navigated from
	  usage?: Usage;       // LLM usage that generated the summary
	  fromHook?: boolean;  // true if provided by extension (legacy field name)
	  details?: T;         // implementation-specific data
	}
}
