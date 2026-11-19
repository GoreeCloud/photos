/** Chronological import-day sections, based on the API's UTC import timestamp.
 * This is not the EXIF capture date; invalid timestamps are never guessed.
 */
export type ImportedAsset = { created_at: string };
export type ImportDay<T> = { key: string; label: string; items: T[] };

function importDay(value: string): string | null {
  const match = /^(\d{4}-\d{2}-\d{2})(?:[T ]|$)/.exec(value);
  if (!match) return null;
  const parsed = new Date(match[1] + "T12:00:00Z");
  return Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== match[1]
    ? null : match[1];
}

/** Preserve API ordering and paging; group only contiguous adjacent uploads. */
export function groupImportsByUtcDay<T extends ImportedAsset>(items: readonly T[]): ImportDay<T>[] {
  const groups: ImportDay<T>[] = [];
  let lastDay: string | null | undefined;
  for (const item of items) {
    const day = importDay(item.created_at);
    if (lastDay !== day || !groups.length) {
      groups.push({
        key: (day ?? "undated") + "-" + groups.length,
        label: day
          ? new Intl.DateTimeFormat("en-US", { dateStyle: "long", timeZone: "UTC" })
            .format(new Date(day + "T12:00:00Z"))
          : "Undated imports",
        items: [],
      });
      lastDay = day;
    }
    groups[groups.length - 1].items.push(item);
  }
  return groups;
}
