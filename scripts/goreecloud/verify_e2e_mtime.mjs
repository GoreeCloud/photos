// Synthetic timestamp precision/behaviour test; no Photos assets or database.
// E2E library rescans compare stat.mtime in milliseconds for two nearly
// identical timestamps. This uses only Node builtins in a disposable CI runner.
import assert from 'node:assert/strict';
import { mkdtemp, rm, stat, utimes, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const dir = await mkdtemp(join(tmpdir(), 'goreecloud-e2e-mtime-'));
const file = join(dir, 'synthetic-not-a-photo.bin');
try {
  await writeFile(file, 'synthetic non-user fixture');
  const stamps = [447_775_200_000, 447_775_200_001, 447_775_200_001];
  const observed = [];
  for (const stamp of stamps) {
    const time = new Date(stamp);
    await utimes(file, time, time);
    const attrs = await stat(file);
    observed.push(attrs.mtime.valueOf());
  }
  assert.deepEqual(observed, stamps);
  console.log('Synthetic E2E mtime millisecond precision: PASS');
} finally {
  await rm(dir, { recursive: true, force: true });
}
