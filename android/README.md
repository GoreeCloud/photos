# Android Photos — foreground folder import and library browser

The native Jetpack Compose library now pages media from the server 40 at a time, supports all/favorites/trash views, filtered filename search, manual refresh, and restoration of trashed items. It uses request-generation checks so results from older navigation actions cannot replace the current view. Original media is not deleted by hiding it in trash. Gallery thumbnails are authenticated and decoded in the app; signed production distribution and real device acceptance remain unverified.

Native Kotlin/Jetpack Compose provides individual file selection and an optional **Import folder** action. The latter uses Android's system document-tree picker, reads only directly contained JPEG, PNG, GIF, WebP and MP4 files, computes each file's SHA-256 locally, queries the authenticated `POST /v1/assets/lookup` endpoint in bounded batches, and uploads only missing files. Existing files are skipped, including matches in the trash (reported separately; **never automatically restored**). Imports scan at most 500 supported files per action and reject files beyond the server's 512 MiB maximum.

**Privacy model:** no blanket storage permissions, no background media scanning, no stored folder grants, no saved passwords or bearer tokens, no tracking. Import operates in the foreground under the current authenticated session; users explicitly choose a folder on each import, and can repeat the action later. Permissions granted by the system picker are not persisted. Authentication is in memory. Remote endpoints require HTTPS and automatic redirects are disabled. Do not describe this as unattended or scheduled Android camera backup.

## Development checks

Build with `cd android && ./gradlew :app:assembleDebug`. Test on a real Android device with a trusted HTTPS server: unlock the library, choose a folder with a mixture of new and previously imported photos, import it twice, then trash one asset and import again. Verify the second import skips existing hashes and that trashed content is not silently restored. Denied picker access, expired sessions, oversized photos, and inaccessible documents should be treated as errors or counted failures. Device/emulator acceptance is not established by a debug build alone.


## User-directed original exports

Each active photo/video has a **Save original** control that launches the operating system's `ACTION_CREATE_DOCUMENT` file picker. The Android client fetches the original via its authenticated API, bounds the transfer to 512 MiB, verifies byte count and SHA-256 against the library record in app-private temporary storage, and only then writes to the explicitly selected document URI. The private temporary data is deleted in `finally`. No broad storage permission, background scan, persisted URI grant, or automatic cloud sharing is added. An interrupted document-provider write can still leave an incomplete user-selected document; the UI warns the user to review it rather than silently deleting a file. This is export, **not** a verified disaster recovery or backup facility. Validate on a real device before release.
