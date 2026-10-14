import type { Component } from "@earendil-works/pi-tui";
import { matchesKey, truncateToWidth, visibleWidth } from "@earendil-works/pi-tui";

export interface GuardBlock {
	tool: string;
	reason: string;
	at: number;
}

// The theme methods this component uses. pi-tui passes the real theme in.
export interface BlockListTheme {
	fg(color: string, text: string): string;
	bold(text: string): string;
}

// A custom component renders an array of lines for a width, and must say when
// its cached output is stale.
export class BlockListComponent implements Component {
	private cachedWidth?: number;
	private cachedLines?: string[];
	private readonly blocks: readonly GuardBlock[];
	private readonly theme: BlockListTheme;
	private readonly close: () => void;

	// Explicit fields rather than constructor parameter properties, so the file
	// also runs under Node's type stripping.
	constructor(blocks: readonly GuardBlock[], theme: BlockListTheme, close: () => void) {
		this.blocks = blocks;
		this.theme = theme;
		this.close = close;
	}

	render(width: number): string[] {
		// Cache by width: re-laying-out on every keystroke is what makes a terminal feel slow.
		if (this.cachedLines && this.cachedWidth === width) return this.cachedLines;

		const lines = [this.theme.fg("accent", this.theme.bold("Blocked calls")), ""];
		if (this.blocks.length === 0) lines.push(this.theme.fg("dim", "none on this branch"));
		for (const b of this.blocks) lines.push(`${b.tool}: ${b.reason}`);
		lines.push("", this.theme.fg("dim", "press q or Escape to close"));

		// Every line must fit the width, measured in display columns, not string length.
		this.cachedLines = lines.map((l) => (visibleWidth(l) > width ? truncateToWidth(l, width) : l));
		this.cachedWidth = width;
		return this.cachedLines;
	}

	handleInput(data: string): void {
		if (data === "q" || matchesKey(data, "escape")) this.close();
	}

	invalidate(): void {
		this.cachedWidth = undefined;
		this.cachedLines = undefined;
	}
}
