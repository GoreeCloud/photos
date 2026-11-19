# Android Photos — foreground folder import and library browser

The native Jetpack Compose library now pages media from the server 40 at a time, supports all/favorites/trash views, filtered filename search, manual refresh, and restoration of trashed items. It uses request-generation checks so results from older navigation actions cannot replace the current view. Original media is not deleted by hiding it in trash. Gallery thumbnails are authenticated and decoded in the app; signed production distribution and real device acceptance remain unverified.

Native Kotlin/Jetpack Compose provides individual file selection and an optional **Import folder** action. The latter uses Android's system document-tree picker, reads only directly contained JPEG, PNG, GIF, WebP and MP4 files, computes each file's SHA-256 locally, queries the authenticated `POST /v1/assets/lookup` endpoint in bounded batches, and uploads only missing files. Existing files are skipped, including matches in the trash (reported separately; **never automatically restored**). Imports scan at most 500 supported files per action and reject files beyond the server's 512 MiB maximum.

**Privacy model:** no blanket storage permissions, no background media scanning, no stored folder grants, no saved passwords or bearer tokens, no tracking. Import operates in the foreground under the current authenticated session; users explicitly choose a folder on each import, and can repeat the action later. Permissions granted by the system picker are not persisted. Authentication is in memory. Remote endpoints require HTTPS and automatic redirects are disabled. Do not describe this as unattended or scheduled Android camera backup.

## Development checks

Build with `cd android && ./gradlew :app:assembleDebug`. Test on a real Android device with a trusted HTTPS server: unlock the library, choose a folder with a mixture of new and previously imported photos, import it twice, then trash one asset and import again. Verify the second import skips existing hashes and that trashed content is not silently restored. Denied picker access, expired sessions, oversized photos, and inaccessible documents should be treated as errors or counted failures. Device/emulator acceptance is not established by a debug build alone.


## User-directed original exports

Each active photo/video has a **Save original** control that launches the operating system's `ACTION_CREATE_DOCUMENT` file picker. The Android client fetches the original via its authenticated API, bounds the transfer to 512 MiB, verifies byte count and SHA-256 against the library record in app-private temporary storage, and only then writes to the explicitly selected document URI. The private temporary data is deleted in `finally`. No broad storage permission, background scan, persisted URI grant, or automatic cloud sharing is added. An interrupted document-provider write can still leave an incomplete user-selected document; the UI warns the user to review it rather than silently deleting a file. This is export, **not** a verified disaster recovery or backup facility. Validate on a real device before release.


## Bounded media ingest and previews

Direct selected-file uploads also enforce the 512 MiB media limit while streaming from Android's document provider. Authentication is required; the client never auto-scans the gallery. Image thumbnails are limited to 6 MiB of compressed bytes and 2048 pixels per axis before decoding, reducing the impact of unexpected or malicious responses from a misconfigured server. This is defense in depth, not a substitute for hardened server-side image handling or a decoder sandbox.


## Native albums and membership

The Android library now has a native album selector, **View album**, and user-directed **New album** creation. The selected album is an explicit destination for **Add to album** from the library, and **Remove from album** deletes only membership in the currently viewed album, never original media. The private backend serves album membership with bounded pages and filename filtering. Switching to All/Favorites/Trash leaves album view; the system never auto-shares media. There is no native rename/delete-album control yet. Album usability still requires real-device acceptance.

## Native client network and session safeguards

Authenticated API JSON bodies are capped at 4 MiB before buffering, and thumbnails retain the 6 MiB compressed / 2048-pixel dimension limits. User-initiated Lock invalidates the session synchronously on the UI thread before asynchronous remote revocation. Verified original exports reject a session invalidated during download or the subsequent user-selected document write; interruption may leave a partial provider document and is reported to the user. The required Android CI job runs JVM unit tests for bounded-response behavior in addition to assembling a debug APK.

## Native owner-security controls

In an unlocked library, Android's **Security** dialog offers password rotation (masked current/new/confirm fields) and a separate owner-confirmed **Sign out all devices without changing password** action. Both require the current library credential and use the existing authenticated API; successful confirmation revokes all sessions and removes the Android bearer token and sensitive gallery/album state immediately. An unsuccessful request retains the current session but clears draft secrets. No password is saved to preferences, no new permission is added, and the actions do not enable multi-user accounts or SSO. Revoke-only is insufficient when the password itself may be compromised. Synthetic validation unit tests cover length, mismatch and unchanged-secret rejection; real device and assistive-technology acceptance remain separate release gates.


## Android 15/16 system-bar safety

The Compose top bar applies `Modifier.statusBarsPadding()` so library actions, particularly the Security and Lock controls, remain below the Android system status bar with edge-to-edge rendering enforced on modern Android. This was added after physical Android 16 testing exposed a visually rendered but touch-inaccessible top row. The full native UI must still undergo visual, TalkBack and responsive validation on representative screen sizes.

The Android 16 physical-device Security dialog review also found that separate Material confirmation and dismissal slots caused the revoke/cancel controls to overlap. All three actions are now arranged as non-overlapping, full-width vertical buttons; physical retesting remains a required validation step.


## Purpose-led, private photo preview

The native library now prioritizes nearly square photo tiles. Tapping an active photo or video tile opens a native Compose preview dialog using the **authenticated EXIF-stripped JPEG thumbnail** already supported by the API (up to 512 pixels), with an explicit, user-selected **Save original** action through Android's system document picker. Videos show a labelled placeholder; in-app video playback, pinch-to-zoom and full-resolution original decoding are **not yet implemented**. The preview is held in process memory only, closes when the owner locks or revokes sessions, and never requests blanket media storage permission or scans other device folders. Actual TalkBack, dynamic-font and multi-screen acceptance remain open.
