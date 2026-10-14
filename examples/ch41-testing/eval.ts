// Level 3 of chapter 41: evaluation. A scripted provider cannot tell you how
// often a real model gets it right. Repeated runs can, and the number to read
// is not the average.

export interface Task<T> {
	id: string;
	run: () => Promise<T>;
	passes: (result: T) => boolean;
}

export interface EvalResult {
	tasks: number;
	k: number;
	/** Mean single-run success rate. What a demo reports. */
	passAt1: number;
	/** Fraction of tasks that succeeded on ALL k independent runs. What a service needs. */
	passPowK: number;
}

export interface EvalOptions {
	/** Wall-clock budget for the whole evaluation. Per-run, not per-task, so a
	 *  task that hangs cannot hang the evaluation past its share of the budget. */
	timeoutMs?: number;
	/** Injected for tests; defaults to the platform timer. */
	timeout?: (fn: () => Promise<unknown>, ms: number) => Promise<unknown>;
}

const defaultTimeout = (fn: () => Promise<unknown>, ms: number) =>
	new Promise((resolve, reject) => {
		const t = setTimeout(() => reject(new Error(`timed out after ${ms}ms`)), ms);
		fn().then(resolve, reject).finally(() => clearTimeout(t));
	});

// An empty task list divides by zero and reports NaN for both rates, which reads
// as a result. A non-positive k makes pass^k vacuously 0 and pass@1 meaningless.
// Both are caller mistakes, and the numbers they produce look like measurements.
export async function evaluate<T>(tasks: Task<T>[], k: number, options: EvalOptions = {}): Promise<EvalResult> {
	if (!Number.isInteger(k) || k < 1) throw new Error(`k must be a positive integer, got ${k}`);
	if (!tasks.length) throw new Error("evaluate needs at least one task; an empty list has no rate to report");
	const guard = options.timeout ?? defaultTimeout;
	const budget = options.timeoutMs;
	// Spread the budget over the runs, with a floor, so one run cannot consume the
	// whole evaluation's allowance.
	const perRun = budget ? Math.max(1, Math.floor(budget / (tasks.length * k))) : undefined;

	let single = 0;
	let allK = 0;
	for (const task of tasks) {
		let wins = 0;
		for (let i = 0; i < k; i++) {
			try {
				const result = perRun ? await guard(() => task.run(), perRun) : await task.run();
				if (task.passes(result as T)) wins++;
			} catch {
				// A step that throws, or times out, is a failed run. Not a crashed
				// evaluation: the point of pass^k is that a run which did not work
				// counts against the task, and a timeout is exactly that.
			}
		}
		single += wins / k;
		if (wins === k) allK++;
	}
	return { tasks: tasks.length, k, passAt1: single / tasks.length, passPowK: allK / tasks.length };
}

// Deterministic pseudo-randomness, so an evaluation of a *simulated* model is repeatable.
export function seeded(seed: number): () => number {
	let a = seed >>> 0;
	return () => {
		a = (a + 0x6d2b79f5) >>> 0;
		let t = a;
		t = Math.imul(t ^ (t >>> 15), t | 1);
		t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
		return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
	};
}
