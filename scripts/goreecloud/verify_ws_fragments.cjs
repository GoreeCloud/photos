'use strict';

// Disposable CI synthetic receiver smoke; does not create network sockets.
// Based on the relevant ws 8.21.x upstream maxFragments regression scenario.
const assert = require('node:assert/strict');
const path = require('node:path');
const Receiver = require(path.resolve(
  __dirname, '../../node_modules/.pnpm/ws@8.21.3/node_modules/ws/lib/receiver.js'
));

async function main() {
  const receiver = new Receiver({ maxFragments: 2 });
  const error = await new Promise((resolve, reject) => {
    const limit = setTimeout(() => reject(new Error('Fragment bound check never settled')), 1500);
    receiver.once('error', (failure) => {
      clearTimeout(limit);
      resolve(failure);
    });
    receiver.once('finish', () => {
      clearTimeout(limit);
      reject(new Error('Unexpected acceptance of too many empty fragments'));
    });
    // One initial nonfinal frame and two empty continuation frames.
    receiver.write(Buffer.from([0x02, 0x00]));
    receiver.write(Buffer.from([0x00, 0x00]));
    receiver.write(Buffer.from([0x00, 0x00]));
  });
  assert.ok(error instanceof RangeError);
  assert.equal(error.code, 'WS_ERR_TOO_MANY_BUFFERED_PARTS');
  assert.equal(error.message, 'Too many message fragments');
  console.log('Synthetic WebSocket zero-length fragment bound: PASS');
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
