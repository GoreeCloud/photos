import { test } from "node:test";
import assert from "node:assert/strict";
import { boundedBlob, boundedJson, JSON_LIMIT, THUMB_LIMIT, PREVIEW_LIMIT } from "../src/network.ts";

test("small authenticated thumbnail passes with exact content length", async () => {
  const body = new Uint8Array([1, 2, 3, 4]);
  const blob = await boundedBlob(new Response(body, {
    headers: { "content-length": "4", "content-type": "image/jpeg" }
  }), THUMB_LIMIT);
  assert.deepEqual([...new Uint8Array(await blob.arrayBuffer())], [1, 2, 3, 4]);
  assert.equal(blob.type, "image/jpeg");
});

test("declared oversized body is rejected", async () => {
  await assert.rejects(
    boundedBlob(new Response("small", {
      headers: { "content-length": String(THUMB_LIMIT + 1) }
    }), THUMB_LIMIT),
    /safe browser preview limit/
  );
});

test("chunked oversize body is rejected early", async () => {
  let reads = 0;
  const stream = new ReadableStream({
    pull(controller) {
      reads += 1;
      controller.enqueue(new Uint8Array(8));
      if (reads === 100) controller.close();
    },
  });
  await assert.rejects(boundedBlob(new Response(stream), 16), /safe browser preview limit/);
  assert.ok(reads < 100);
});

test("truncated or invalid content length is rejected", async () => {
  await assert.rejects(
    boundedBlob(new Response("short", { headers: { "content-length": "20" } }), THUMB_LIMIT),
    /Incomplete server response/
  );
  for (const value of ["-1", "nonsense", "3.3", "999999999999999999999"]) {
    await assert.rejects(
      boundedBlob(new Response("text", { headers: { "content-length": value } }), JSON_LIMIT),
      /Invalid server response length/
    );
  }
});

test("bounded JSON accepts objects and rejects arrays and oversized payloads", async () => {
  const sample = { total: 4, items: [] };
  assert.deepEqual(await boundedJson(new Response(JSON.stringify(sample))), sample);
  await assert.rejects(boundedJson(new Response("[]")), /Invalid JSON object/);
  await assert.rejects(
    boundedJson(new Response("X".repeat(JSON_LIMIT + 2))), /safe browser preview limit/
  );
});

test("large originals are not silently allocated for browser preview", () => {
  assert.equal(PREVIEW_LIMIT, 64 * 1024 * 1024);
  assert.ok(PREVIEW_LIMIT < 512 * 1024 * 1024);
});
