import { test } from "node:test";
import assert from "node:assert/strict";
import { groupImportsByUtcDay } from "../src/timeline.ts";

test("groups adjacent photo imports by UTC date without changing API order", () => {
  const items = [
    { id: "a", created_at: "2026-11-19T23:59:50+00:00" },
    { id: "b", created_at: "2026-11-19T13:02:00+00:00" },
    { id: "c", created_at: "2026-11-18T22:15:00+00:00" },
    { id: "d", created_at: "2026-11-19T00:01:00+00:00" },
  ];
  const sections = groupImportsByUtcDay(items);
  assert.deepEqual(sections.map(g => g.items.map(item => item.id)), [
    ["a", "b"], ["c"], ["d"]
  ]);
  assert.equal(sections[0].label, "November 19, 2026");
  assert.notEqual(sections[0].key, sections[2].key);
  assert.deepEqual(items.map(item => item.id), ["a", "b", "c", "d"]);
});

test("handles invalid, malformed, and missing timestamps without guessing capture dates", () => {
  const items = [
    { created_at: "not a date" },
    { created_at: "2026-02-30T00:00:00+00:00" },
    { created_at: "" },
    { created_at: "2026-01-01T15:00:00+00:00" },
  ];
  const result = groupImportsByUtcDay(items);
  assert.deepEqual(result.map(x => x.items.length), [3, 1]);
  assert.equal(result[0].label, "Undated imports");
  assert.equal(result[1].label, "January 1, 2026");
  assert.deepEqual(groupImportsByUtcDay([]), []);
});
