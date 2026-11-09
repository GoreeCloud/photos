'use strict';

// Synthetic, bounded validation regression. No request server or personal data.
// Follows upstream Zod 4.6.6 early-size-gate array/set/map tests.
const assert = require('node:assert/strict');
const path = require('node:path');
const { z } = require(path.resolve(__dirname, '../../node_modules/.pnpm/zod@4.6.6/node_modules/zod'));

let elementChecks = 0;
const array = z.array(z.string().refine(() => { elementChecks++; return true; })).max(2);
const result = array.safeParse(Array(4096).fill('synthetic'));
assert.equal(result.success, false);
assert.equal(result.error.issues.length, 1);
assert.equal(result.error.issues[0].code, 'too_big');
assert.equal(elementChecks, 0, 'oversized array elements must not be parsed');

const set = z.set(z.string()).max(1).safeParse(new Set([1, 2]));
assert.equal(set.success, false);
assert.equal(set.error.issues.length, 1);
assert.equal(set.error.issues[0].code, 'too_big');
const map = z.map(z.string(), z.string()).max(1).safeParse(new Map([[1, 1], [2, 2]]));
assert.equal(map.success, false);
assert.equal(map.error.issues.length, 1);
assert.equal(map.error.issues[0].code, 'too_big');

const nested = z.object({ a: z.array(z.string()).max(1) }).safeParse({ a: ['one', 'two'] });
assert.equal(nested.success, false);
assert.equal(nested.error.issues.length, 1);
assert.deepEqual(nested.error.issues[0].path, ['a']);
console.log('Zod synthetic early array/set/map bounds: PASS');
