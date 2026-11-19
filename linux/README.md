# Native Linux Photo Library

This Qt Quick 6.12 application uses the authenticated GoreeCloud Photos API without a browser wrapper. It supports file-picker uploads, private streamed original downloads with an explicit Save dialog, thumbnails, favorites, soft deletion, restoration from trash, filename search and server-side paging (60 results per page). Select All Photos, Favorites or Trash, then use the page controls.

Search is submitted on Return or by clicking Search; Clear resets the filter. This build is a development preview. Native albums can be browsed, created, and have members added or removed without deleting original media. There is no native album rename/delete dialog, local offline cache, signed package, or background backup.

## Test

Install the pinned, smaller PySide6-Essentials Qt Quick distribution via `uv venv .venv --python 3.12 && uv pip install --python .venv/bin/python -r requirements.txt`, then run `.venv/bin/python main.py --server https://your-private-server.example`. Only loopback HTTP is allowed. For an automated QML startup smoke on Linux, run `QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software timeout 3s .venv/bin/python main.py` and confirm it stays running until timeout without QML parser errors. The required `desktop-static` CI job compiles Python and runs `pyside6-qmllint` with pinned Qt 6.12 wheels. Real offscreen GUI startup is a separate, explicitly triggered `Native Linux Qt runtime acceptance (manual)` workflow because its Ubuntu EGL dependency installation currently depends on intermittently unavailable Ubuntu mirrors. A passing static check must **not** be described as runtime acceptance. A local Qt offscreen startup smoke has been performed; physical desktop interaction and assistive-technology review remain outstanding.

Download security: the Linux native client denies network redirects for authenticated operations and streams selected originals to a 0600 temporary file, checks a 512 MiB limit, then promotes without overwriting any existing destination. In-flight downloads are discarded when the library locks. File save is always an explicit user action; no automatic local photo scanning or backup is performed.


Native album use: choose an existing album with the Qt Quick selector and select **Open album**, or enter a new album name and select **Create**. In All/Favorites, **Add to album** adds an item to the selected album. Inside an album, **Remove from album** only deletes its membership; originals remain available in the main library. Album membership paging and filename search are served by the private API. There is no external sync or sharing.


## Bounded native network responses

Authenticated JSON responses are bounded to 4 MiB and thumbnail responses to 6 MiB, with Qt's network read buffer capped and a 30-second transfer timeout. Thumbnail headers are inspected with Qt 6.12's QImageReader before decoding; only JPEG previews up to 2048 pixels per axis are accepted. HTTPS/loopback-only URLs and manual redirect rejection remain enforced. Oversize or corrupt responses do not enter the image cache. The manual native Linux CI workflow runs the synthetic authenticated network-response unit tests alongside the original-download and album tests; the required cross-platform CI continues to do pinned QML/static checks without relying on unreliable Ubuntu EGL mirrors.

## Native owner security

The unlocked Qt Quick **Security** dialog uses masked current/new/confirmation fields, a dedicated password-rotation button, and a separate **Sign out all devices without changing password** button. Both call the server's bearer-authenticated API and require the current library password. On success the server revokes all sessions and the native client immediately clears its token, media previews, albums, search and selected view before returning to Unlock. Draft secrets are cleared after submission, Cancel or Escape; this app does not save credentials. Server-side persistent throttling protects repeated wrong-password attempts. Signing out without rotation is not adequate if the password itself is compromised. Assistive-technology and distribution acceptance remain outstanding.


## Photo-first native gallery

The Qt Quick library now sizes media tiles to its window width rather than fixing every grid column to 192 pixels. Each card prioritizes a nearly-square cropped private image preview, with clearly identified video placeholders, followed by the original filename and explicit favorite, save, album and trash actions. Images remain fetched from authenticated API responses and held in the existing memory-only thumbnail provider; no filesystem or camera access is added. Resizing, scaling and contrast must still be accepted on representative real Linux desktops.

## Tap-to-open private previews

The native photo tiles are keyboard-focusable Qt Quick buttons. Opening an active tile shows a modal built with Qt Quick Controls and the already authenticated, in-memory EXIF-stripped thumbnail provider. Video entries are explicitly marked as not previewable; both photo and video dialogs can open the user's native Save-original file picker. Trashed items require restoration before preview and a library Lock or global session revocation closes the dialog and clears its selected media reference. No full-resolution original is loaded into the Qt preview, no background media indexing occurs, and no new dependency is introduced. Real desktop pointer, keyboard and screen-reader acceptance remains pending.


Private Qt thumbnails preserve source aspect ratio when scaled, disable image-source caches, and update the modal preview if its in-memory thumbnail arrives after opening. The preview automatically closes if the selected media is no longer part of the visible collection, including after filtering, page changes or trash; the file picker remains backed by the same authenticated original-download validation. The preview is never a full-resolution original viewer.
