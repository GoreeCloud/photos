import { test } from "node:test";
import assert from "node:assert/strict";
import { hashSmallFile, MAX_PREFLIGHT_BYTES } from "../src/import-preflight.ts";

test("computes SHA-256 for small explicit imports with native WebCrypto", async () => {
  const result = await hashSmallFile(new Blob(["abc"]));
  assert.equal(result, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
});

test("never allocates or reads large or empty originals for preflight", async () => {
  let read = 0;
  const fake = size => ({ size, arrayBuffer() { read++; throw Error("should not read"); } });
  assert.equal(await hashSmallFile(fake(0)), null);
  assert.equal(await hashSmallFile(fake(MAX_PREFLIGHT_BYTES + 1)), null);
  assert.equal(read, 0);
});

test("rejects local file-size changes rather than trusting mismatched hashes", async () => {
  await assert.rejects(() => hashSmallFile({
    size: 5,
    async arrayBuffer() { return new Uint8Array([1, 2]).buffer; }
  }), /changed during duplicate checking/);
});
