'use strict';

// Security and basic API regression against installed serializer; no eval, code
// execution, Photos content, external resources, or production web app.
const assert = require('node:assert/strict');
const path = require('node:path');
const serialize = require(path.resolve(__dirname,
  '../../node_modules/.pnpm/serialize-javascript@7.1.3/node_modules/serialize-javascript'
));

const fakeRegex = Object.create(RegExp.prototype);
Object.defineProperty(fakeRegex, 'source', { get: () => 'x' });
Object.defineProperty(fakeRegex, 'flags', {
  get: () => 'g"+synthetic_canary+"'
});
fakeRegex.toJSON = () => '@placeholder';
const output = serialize({ re: fakeRegex });
assert.match(output, /new RegExp/);
assert.doesNotMatch(output, /synthetic_canary/);

const fakeDate = Object.create(Date.prototype);
fakeDate.toISOString = () => '"+synthetic_date_canary+"';
fakeDate.toJSON = () => '2024-01-01';
assert.throws(() => serialize({ d: fakeDate }), TypeError);

const normal = serialize({ re: /ab/gi, number: 4, text: '<test>', arr: [true, null] });
assert.match(normal, /new RegExp/);
assert.match(normal, /\\u003C/);
assert.match(normal, /"number":4/);
const scriptEdge = serialize({ fn: function scriptEnding() { return '</script'; } });
assert.doesNotMatch(scriptEdge, /<\/script/i);
const spoofedFunction = function syntheticOnly() {};
spoofedFunction.toString = () => 'function() {}</script';
assert.doesNotMatch(serialize({ fn: spoofedFunction }), new RegExp('</script', 'i'));
console.log('serialize-javascript synthetic sanitization and object API: PASS');
