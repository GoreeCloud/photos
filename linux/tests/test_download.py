"""Native Qt download integration against a synthetic local HTTP endpoint."""
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QGuiApplication

from linux.main import Bridge, ThumbnailProvider

ID = "00000000-0000-4000-8000-000000000042"
REDIRECT = "00000000-0000-4000-8000-000000000043"
PAYLOAD = b"synthetic media only\n" * 8000


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        if REDIRECT in self.path:
            self.send_response(302)
            self.send_header("Location", "https://example.invalid/no-follow")
            self.end_headers()
        elif ID in self.path and self.headers.get("Authorization") == "Bearer fake-token":
            self.send_response(200)
            self.send_header("Content-Length", str(len(PAYLOAD)))
            self.end_headers()
            self.wfile.write(PAYLOAD)
        else:
            self.send_response(401)
            self.end_headers()


class DownloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication(["photos-download-test"])
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.bridge = Bridge(f"http://127.0.0.1:{self.server.server_port}", ThumbnailProvider())
        self.bridge._token = "fake-token"
        self.bridge._items = [{"id": ID}, {"id": REDIRECT}]
        self.errors, self.messages = [], []
        self.bridge.error.connect(self.errors.append)
        self.bridge.message.connect(self.messages.append)

    def run_event_loop(self):
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(self.app.quit)
        self.bridge.error.connect(self.app.quit)
        self.bridge.message.connect(self.app.quit)
        timer.start(4000)
        self.app.exec()
        timer.stop()
        self.assertTrue(self.messages or self.errors, "Timed out waiting for a download result")

    def test_original_streams_privately_and_never_overwrites(self):
        target = Path(self.temporary.name) / "synthetic.jpg"
        self.bridge.download(ID, QUrl.fromLocalFile(str(target)).toString())
        self.run_event_loop()
        self.assertFalse(self.errors)
        self.assertEqual(target.read_bytes(), PAYLOAD)
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        self.assertEqual(list(target.parent.glob(".photos-download-*")), [])
        self.bridge.download(ID, QUrl.fromLocalFile(str(target)).toString())
        self.assertTrue(self.errors)
        self.assertEqual(target.read_bytes(), PAYLOAD)

    def test_redirect_denied_without_leaving_partial_file(self):
        target = Path(self.temporary.name) / "should-not-exist.mp4"
        self.bridge.download(REDIRECT, QUrl.fromLocalFile(str(target)).toString())
        self.run_event_loop()
        self.assertTrue(self.errors)
        self.assertFalse(target.exists())
        self.assertEqual(list(target.parent.glob(".photos-download-*")), [])

    def test_trash_and_locked_library_rejected(self):
        target = Path(self.temporary.name) / "denied.bin"
        self.bridge._view = "trash"
        self.bridge.download(ID, QUrl.fromLocalFile(str(target)).toString())
        self.assertTrue(self.errors)
        self.errors.clear()
        self.bridge._view = "library"
        self.bridge._token = ""
        self.bridge.download(ID, QUrl.fromLocalFile(str(target)).toString())
        self.assertTrue(self.errors)
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
