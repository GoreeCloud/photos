# Android Photos — foreground folder import and library browser

The native Jetpack Compose library now pages media from the server 40 at a time, supports all/favorites/trash views, filtered filename search, manual refresh, and restoration of trashed items. It uses request-generation checks so results from older navigation actions cannot replace the current view. Original media is not deleted by hiding it in trash. Gallery thumbnails are authenticated and decoded in the app; signed production distribution and real device acceptance remain unverified.

Native Kotlin/Jetpack Compose provides individual file selection and an optional **Import folder** action. The latter uses Android's system document-tree picker, reads only directly contained JPEG, PNG, GIF, WebP and MP4 files, computes each file's SHA-256 locally, queries the authenticated `POST /v1/assets/lookup` endpoint in bounded batches, and uploads only missing files. Existing files are skipped, including matches in the trash (reported separately; **never automatically restored**). Imports scan at most 500 supported files per action and reject files beyond the server's 512 MiB maximum.

**Privacy model:** no blanket storage permissions, no background media scanning, no stored folder grants, no saved passwords or bearer tokens, no tracking. Import operates in the foreground under the current authenticated session; users explicitly choose a folder on each import, and can repeat the action later. Permissions granted by the system picker are not persisted. Authentication is in memory. Remote endpoints require HTTPS and automatic redirects are disabled. Do not describe this as unattended or scheduled Android camera backup.

## Development checks

Build with `cd android && ./gradlew :app:assembleDebug`. Test on a real Android device with a trusted HTTPS server: unlock the library, choose a folder with a mixture of new and previously imported photos, import it twice, then trash one asset and import again. Verify the second import skips existing hashes and that trashed content is not silently restored. Denied picker access, expired sessions, oversized photos, and inaccessible documents should be treated as errors or counted failures. Device/emulator acceptance is not established by a debug build alone.


## Save original (explicit user control)

In All or Favorites, select **Save original** beneath the photo/video. Android's `ACTION_CREATE_DOCUMENT` system picker creates a user-chosen destination, and the app streams the authenticated original directly to its document URI with a 512 MiB cap and checks the complete Content-Length when provided. Individual document uploads also stop locally at 512 MiB. Automatic HTTP redirects are disabled; a failed transfer makes a best-effort attempt to delete the newly created partial document. No blanket storage permissions, automatic camera-roll exports, or background photo downloads are enabled. Originals in Trash cannot be saved until restored.
