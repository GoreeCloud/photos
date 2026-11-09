'use strict';

// Two synthetic loopback HTTP origins; no external endpoints or private data.
// Based on official undici redirect/cache security regression.
const assert = require('node:assert/strict');
const { createServer } = require('node:http');
const { once } = require('node:events');
const path = require('node:path');
const { Agent, cacheStores, interceptors } = require(path.resolve(
  __dirname, '../../node_modules/.pnpm/undici@8.12.2/node_modules/undici'
));
async function listen(server) {
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
}
async function close(server) {
  server.closeAllConnections();
  server.close();
  await once(server, 'close');
}
async function main() {
  let redirectEnabled = true;
  let trustedHits = 0;
  let attackerHits = 0;
  let attackerUrl;
  const attacker = createServer((_req, res) => {
    attackerHits++;
    res.writeHead(200, { 'cache-control': 'public, max-age=3600' });
    res.end('synthetic-attacker-data');
  });
  const trusted = createServer((req, res) => {
    trustedHits++;
    if (redirectEnabled && req.url === '/asset') {
      res.writeHead(302, { location: attackerUrl });
      res.end();
    } else {
      res.writeHead(200, { 'cache-control': 'no-store' });
      res.end('synthetic-trusted-data');
    }
  });
  let dispatcher;
  try {
    await listen(attacker);
    attackerUrl = 'http://127.0.0.1:' + attacker.address().port + '/payload';
    await listen(trusted);
    const origin = 'http://127.0.0.1:' + trusted.address().port;
    dispatcher = new Agent().compose(
      interceptors.redirect({ maxRedirections: 2 }),
      interceptors.cache({ store: new cacheStores.MemoryCacheStore(), type: 'shared' })
    );
    const first = await dispatcher.request({ origin, path: '/asset', method: 'GET', headers: { cookie: 'session=synthetic-a' } });
    assert.equal(await first.body.text(), 'synthetic-attacker-data');
    redirectEnabled = false;
    const before = [trustedHits, attackerHits];
    const second = await dispatcher.request({ origin, path: '/asset', method: 'GET', headers: { cookie: 'session=synthetic-b' } });
    assert.equal(await second.body.text(), 'synthetic-trusted-data');
    assert.notDeepEqual([trustedHits, attackerHits], before);
    console.log('Undici synthetic loopback redirect/cache isolation: PASS');
  } finally {
    if (dispatcher) await dispatcher.close();
    if (trusted.listening) await close(trusted);
    if (attacker.listening) await close(attacker);
  }
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
