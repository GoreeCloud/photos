/** Bounded streaming of untrusted private HTTP replies; no external dependencies. */
export const JSON_LIMIT = 4 * 1024 * 1024;
export const THUMB_LIMIT = 6 * 1024 * 1024;
export const PREVIEW_LIMIT = 64 * 1024 * 1024;

/** Reject oversized declared or actual bodies before constructing a browser Blob. */
export async function boundedBlob(response: Response, maxBytes: number): Promise<Blob> {
  if (!Number.isSafeInteger(maxBytes) || maxBytes < 1) {
    throw new Error("Invalid response size limit");
  }
  const declared = response.headers.get("content-length");
  if (declared !== null) {
    const parsed = Number(declared);
    if (!Number.isSafeInteger(parsed) || parsed < 0) {
      throw new Error("Invalid server response length");
    }
    if (parsed > maxBytes) {
      throw new Error("Media exceeds the safe browser preview limit");
    }
  }
  const reader = response.body?.getReader();
  if (!reader) {
    // A bodyless Response may be legitimate for JSON 204. Callers skip those.
    return new Blob([], { type: response.headers.get("content-type") || "" });
  }
  const parts: ArrayBuffer[] = [];
  let bytes = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      bytes += value.byteLength;
      if (bytes > maxBytes) {
        await reader.cancel().catch(() => undefined);
        throw new Error("Media exceeds the safe browser preview limit");
      }
      parts.push(value.slice().buffer as ArrayBuffer);
    }
  } finally {
    reader.releaseLock();
  }
  if (declared !== null && bytes !== Number(declared)) {
    throw new Error("Incomplete server response");
  }
  return new Blob(parts, { type: response.headers.get("content-type") || "" });
}

export async function boundedJson<T>(response: Response): Promise<T> {
  const blob = await boundedBlob(response, JSON_LIMIT);
  const parsed: unknown = JSON.parse(await blob.text());
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new Error("Invalid JSON object response");
  }
  return parsed as T;
}
