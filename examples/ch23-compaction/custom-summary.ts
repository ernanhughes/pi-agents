import { serializeConversation, convertToLlm, type ExtensionAPI } from "@earendil-works/pi-coding-agent";

// Take over compaction: keep Pi's own cut point, but supply the summary text.
// A real extension would send `serialized` to a model of its choice (a cheaper
// one, for instance) and use the reply. Here the summary is built locally so the
// handler is complete and runnable without a second model.
export default function (pi: ExtensionAPI) {
	pi.on("session_before_compact", async (event) => {
		const { preparation } = event;

		// preparation.messagesToSummarize : the messages that are about to be replaced
		// preparation.previousSummary     : the last compaction's summary, if any
		// preparation.firstKeptEntryId    : where the kept messages start
		const serialized = serializeConversation(convertToLlm(preparation.messagesToSummarize));

		return {
			compaction: {
				summary: `Custom summary of ${preparation.messagesToSummarize.length} message(s):\n${serialized.slice(0, 500)}`,
				firstKeptEntryId: preparation.firstKeptEntryId,
				tokensBefore: preparation.tokensBefore,
			},
		};
	});
}
