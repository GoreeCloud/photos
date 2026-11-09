'use strict';

// Synthetic, bounded parser regression only; no network, app, user data or eval.
// Hosted checks run under an independent 12-second process timeout.
const assert = require('node:assert/strict');
const path = require('node:path');

function installed(name, version) {
  return require(path.resolve(__dirname, '../../node_modules/.pnpm',
    name + '@' + version + '/node_modules/' + name));
}

const expand = installed('brace-expansion', '1.1.21');
assert.deepEqual(expand('{a},b}'), ['a}', 'b']);
assert.deepEqual(expand('{a},b}', { maxRewrites: 0 }), ['{a},b}']);
const payload = '{a}' + '}'.repeat(12000) + ',z}';
const start = performance.now();
const result = expand(payload);
const elapsedMs = performance.now() - start;
assert.equal(result.length, 2);
assert.ok(elapsedMs < 8000, 'Brace parser exceeded synthetic time budget: ' + elapsedMs);

const qs = installed('qs', '6.16.1');
assert.deepEqual(qs.parse('a=x,y', { comma: true }), { a: ['x', 'y'] });
assert.deepEqual(qs.parse('a[0]=x&a[1]=y', { arrayLimit: 1 }), { a: ['x', 'y'] });
assert.equal(qs.parse('a[__proto__][synthetic_pollution]=yes').a, undefined);
assert.equal({}.synthetic_pollution, undefined);

const { colord } = installed('colord', '2.9.4');
assert.equal(colord('#ffffff').isValid(), true);
assert.equal(colord('#' + 'x'.repeat(30000)).isValid(), false);

const selector6 = installed('postcss-selector-parser', '6.1.5');
const selector7 = installed('postcss-selector-parser', '7.1.6');
for (const parser of [selector6, selector7]) {
  let nodes = 0;
  const text = parser((root) => { root.walkTags(() => { nodes++; }); })
    .processSync('section > a.test, img[alt="synthetic"]');
  assert.equal(nodes, 2);
  assert.match(text, /section > a/);
}
console.log('Synthetic parser bounds and API compatibility: PASS');
