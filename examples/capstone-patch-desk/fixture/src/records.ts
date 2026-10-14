// Records are key=value pairs. Nonblank malformed records must still fail.
export function parseRecords(input: string): Record<string, string> {
  const records: Record<string, string> = {};
  for (const line of input.split(/\r?\n/)) {
    const match = /^([a-z]+)=([^=]+)$/.exec(line);
    if (!match) throw new Error(`Invalid record: ${line}`);
    records[match[1]] = match[2];
  }
  return records;
}
