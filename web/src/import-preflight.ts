/** Optional SHA-256 preflight for explicitly selected small files only.
 * WebCrypto digest consumes its entire input: never buffer large originals.
 */
export const MAX_PREFLIGHT_BYTES = 16 * 1024 * 1024;

export async function hashSmallFile(
  file: Pick<Blob, "size" | "arrayBuffer">
): Promise<string | null> {
  if (file.size <= 0 || file.size > MAX_PREFLIGHT_BYTES || !globalThis.crypto?.subtle)
    return null;
  const bytes = await file.arrayBuffer();
  if (bytes.byteLength !== file.size || bytes.byteLength > MAX_PREFLIGHT_BYTES)
    throw new Error("The selected file changed during duplicate checking");
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), value => value.toString(16).padStart(2, "0")).join("");
}
