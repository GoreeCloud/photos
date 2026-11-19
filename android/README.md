# Android Photos — explicit folder import

Native Kotlin/Jetpack Compose provides individual file selection and an optional **Import folder** action. The latter uses Android's system document-tree picker, reads only directly contained JPEG, PNG, GIF, WebP and MP4 files, computes each file's SHA-256 locally, queries the authenticated `POST /v1/assets/lookup` endpoint in bounded batches, and uploads only missing files. Existing files are skipped, including matches in the trash (reported separately; **never automatically restored**). Imports scan at most 500 supported files per action and reject files beyond the server's 512 MiB maximum.

**Privacy model:** no blanket storage permissions, no background media scanning, no stored folder grants, no saved passwords or bearer tokens, no tracking. Import operates in the foreground under the current authenticated session; users explicitly choose a folder on each import, and can repeat the action later. Permissions granted by the system picker are not persisted. Authentication is in memory. Remote endpoints require HTTPS and automatic redirects are disabled. Do not describe this as unattended or scheduled Android camera backup.

## Development checks

Build with `cd android && ./gradlew :app:assembleDebug`. Test on a real Android device with a trusted HTTPS server: unlock the library, choose a folder with a mixture of new and previously imported photos, import it twice, then trash one asset and import again. Verify the second import skips existing hashes and that trashed content is not silently restored. Denied picker access, expired sessions, oversized photos, and inaccessible documents should be treated as errors or counted failures. Device/emulator acceptance is not established by a debug build alone.
