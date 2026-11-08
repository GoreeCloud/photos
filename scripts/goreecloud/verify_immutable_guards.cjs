'use strict';

// Synthetic security-regression check; run only in disposable hosted docs CI.
// An old vulnerable List can loop indefinitely, so the workflow imposes an
// external GNU timeout. No network, credentials, photos, or application server.
const assert = require('node:assert/strict');
const path = require('node:path');
const immutable = require(path.resolve(
  __dirname, '../../node_modules/.pnpm/immutable@5.1.8/node_modules/immutable'
));

assert.throws(() => immutable.List().setSize(2 ** 30), RangeError);

// 'Aa' and 'BB' use the same polynomial 32-bit public hash. Assert basic
// correctness with several hundred colliding keys; this is not a benchmark.
let colliders = [''];
for (let n = 0; n < 9; n += 1) {
  colliders = colliders.flatMap((prefix) => [prefix + 'Aa', prefix + 'BB']);
}
const map = immutable.Map(colliders.map((key, index) => [key, index]));
assert.equal(map.size, colliders.length);
for (let i = 0; i < colliders.length; i += 1) {
  assert.equal(map.get(colliders[i]), i);
}
console.log('Immutable.js synthetic bounded List and collision integrity smoke passed');
