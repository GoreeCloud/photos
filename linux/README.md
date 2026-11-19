# Native Linux Photo Library

This Qt Quick 6.12 application uses the authenticated GoreeCloud Photos API without a browser wrapper. It supports file-picker uploads, thumbnails, favorites, soft deletion, restoration from trash, filename search and server-side paging (60 results per page). Select All Photos, Favorites or Trash, then use the page controls.

Search is submitted on Return or by clicking Search; Clear resets the filter. This build is a development preview. There is no native album editor, local offline cache, signed package, or background backup.

## Test

Install the pinned, smaller PySide6-Essentials Qt Quick distribution via `uv venv .venv --python 3.12 && uv pip install --python .venv/bin/python -r requirements.txt`, then run `.venv/bin/python main.py --server https://your-private-server.example`. Only loopback HTTP is allowed. For an automated QML startup smoke on Linux, run `QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software timeout 3s .venv/bin/python main.py` and confirm it stays running until timeout without QML parser errors. The required `desktop-static` CI job compiles Python and runs `pyside6-qmllint` with pinned Qt 6.12 wheels. Real offscreen GUI startup is a separate, explicitly triggered `Native Linux Qt runtime acceptance (manual)` workflow because its Ubuntu EGL dependency installation currently depends on intermittently unavailable Ubuntu mirrors. A passing static check must **not** be described as runtime acceptance. A local Qt offscreen startup smoke has been performed; physical desktop interaction and assistive-technology review remain outstanding.
