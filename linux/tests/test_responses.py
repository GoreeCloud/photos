"""Native Qt private response limits against a synthetic loopback HTTP server."""
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QTimer
from PySide6.QtGui import QGuiApplication, QImage

from linux.main import Bridge, ThumbnailProvider, safe_thumbnail

GOOD_ID = "00000000-0000-4000-8000-000000000071"
BAD_ID = "00000000-0000-4000-8000-000000000072"
LARGE = b"x" * (6 * 1024 * 1024 + 100)


def sample_image(format_name="JPEG", width=20, height=25):
    image = QImage(width, height, QImage.Format.Format_RGB32)
    image.fill(0xFF3388CC)
    payload = QByteArray()
    buffer = QBuffer(payload)
    assert buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer, format_name)
    buffer.close()
    return bytes(payload)


SAMPLE_JPEG = None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def respond(self, data, status=200, media="application/json"):
        try:
            self.send_response(status)
            self.send_header("Content-Type", media)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            for index in range(0, len(data), 65536):
                self.wfile.write(data[index:index + 65536])
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        if self.path == "/huge-json":
            self.respond(LARGE, media="application/json")
        elif self.path == "/valid-json":
            self.respond(json.dumps({"items": [], "total": 0}).encode())
        elif self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "https://example.invalid/never")
            self.end_headers()
        elif GOOD_ID in self.path:
            self.respond(SAMPLE_JPEG, media="image/jpeg")
        elif BAD_ID in self.path:
            self.respond(LARGE, media="image/jpeg")
        else:
            self.respond(b"{}", status=404)


class ResponseLimitsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global SAMPLE_JPEG
        cls.app = QGuiApplication.instance() or QGuiApplication(["qt-bounded-responses"])
        SAMPLE_JPEG = sample_image()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.worker.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.worker.join(timeout=5)

    def setUp(self):
        self.provider = ThumbnailProvider()
        self.bridge = Bridge(
            f"http://127.0.0.1:{self.server.server_port}", self.provider
        )
        self.bridge._token = "only-synthetic-memory-token"
        self.errors = []
        self.bridge.error.connect(self.errors.append)

    def wait_for_network(self, milliseconds=4000):
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(self.app.quit)
        self.bridge.manager.finished.connect(self.app.quit)
        timer.start(milliseconds)
        self.app.exec()
        timer.stop()

    def test_valid_and_rejected_json_responses(self):
        data = []
        self.bridge.send("GET", "/valid-json", callback=data.append)
        self.wait_for_network()
        self.assertEqual(data, [{"items": [], "total": 0}])
        self.assertEqual(self.errors, [])
        self.bridge.send("GET", "/huge-json", callback=data.append)
        self.wait_for_network()
        self.assertEqual(len(data), 1)
        self.assertIn("exceeded 4 MiB", self.errors[-1])

    def test_redirect_is_not_followed(self):
        self.bridge.send("GET", "/redirect")
        self.wait_for_network()
        self.assertTrue(self.errors)

    def test_thumbnail_header_validation(self):
        self.assertTrue(safe_thumbnail(SAMPLE_JPEG))
        self.assertFalse(safe_thumbnail(b"not an image"))
        self.assertFalse(safe_thumbnail(sample_image("PNG")))
        self.assertFalse(safe_thumbnail(sample_image(width=2050, height=10)))
        self.assertFalse(safe_thumbnail(LARGE))

    def test_private_thumbnail_limited_before_storage(self):
        self.bridge.fetch_thumb(GOOD_ID, self.bridge._generation)
        self.wait_for_network()
        self.assertIn(GOOD_ID, self.provider.images)
        self.bridge.fetch_thumb(BAD_ID, self.bridge._generation)
        self.wait_for_network()
        self.assertNotIn(BAD_ID, self.provider.images)
        self.assertLess(len(self.provider.images[GOOD_ID]), 6 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
