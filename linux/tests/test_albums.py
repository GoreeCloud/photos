"""Native Qt album workflow routing with synthetic API responses and no personal media."""
import unittest

from PySide6.QtGui import QGuiApplication

from linux.main import Bridge, ThumbnailProvider

ALBUM = "00000000-0000-4000-8000-000000000001"
MEDIA = "00000000-0000-4000-8000-000000000002"


class AlbumsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication(["photos-album-tests"])

    def setUp(self):
        self.bridge = Bridge("http://127.0.0.1:8787", ThumbnailProvider())
        self.bridge._token = "fake-memory-only"
        self.bridge._albums = [{"id": ALBUM, "name": "Journeys", "count": 1}]
        self.bridge._items = [{"id": MEDIA, "filename": "synthetic.png"}]
        self.calls = []
        self.errors = []
        self.messages = []
        self.bridge.error.connect(self.errors.append)
        self.bridge.message.connect(self.messages.append)

        def fake_send(method, path, payload=None, callback=None, content_type="application/json"):
            self.calls.append((method, path, payload))
            if callback:
                if path.startswith("/v1/albums") and method == "GET" and path == "/v1/albums":
                    callback({"items": [{"id": ALBUM, "name": "Journeys", "count": 1}]})
                elif method == "GET":
                    callback({"items": [{"id": MEDIA, "filename": "synthetic.png"}], "total": 1})
                elif method == "POST" and path == "/v1/albums":
                    callback({"id": ALBUM, "name": payload["name"]})
                else:
                    callback({})
        self.bridge.send = fake_send

    def test_album_navigation_and_search_are_server_paged(self):
        self.bridge.viewAlbum(ALBUM)
        self.assertEqual(self.bridge.view, "album")
        self.assertTrue(self.calls[-1][1].startswith(f"/v1/albums/{ALBUM}/assets?"))
        self.assertIn("limit=60", self.calls[-1][1])
        self.bridge.setSearch("trip photo")
        self.assertIn("search=trip+photo", self.calls[-1][1])
        self.bridge.setView("library")
        self.assertEqual(self.bridge.view, "library")
        self.assertTrue(self.calls[-1][1].startswith("/v1/assets?"))

    def test_album_creation_membership_and_original_preservation(self):
        self.bridge.createAlbum("  Holidays  ")
        self.assertEqual(self.calls[0], ("POST", "/v1/albums", {"name": "Holidays"}))
        self.assertEqual(self.bridge.albums[0]["id"], ALBUM)
        self.bridge.addToAlbum(ALBUM, MEDIA)
        self.assertIn(("POST", f"/v1/albums/{ALBUM}/assets/{MEDIA}", None), self.calls)
        self.bridge.viewAlbum(ALBUM)
        self.bridge.removeFromAlbum(MEDIA)
        self.assertIn(("DELETE", f"/v1/albums/{ALBUM}/assets/{MEDIA}", None), self.calls)
        self.assertTrue(any("original preserved" in msg for msg in self.messages))

    def test_locked_trash_or_unknown_album_cannot_change_membership(self):
        self.bridge._view = "trash"
        self.bridge.addToAlbum(ALBUM, MEDIA)
        self.assertFalse(self.calls)
        self.bridge._view = "library"
        self.bridge.addToAlbum("wrong", MEDIA)
        self.bridge.removeFromAlbum(MEDIA)
        self.assertFalse(self.calls)
        self.assertEqual(len(self.errors), 3)
        self.bridge.logout()
        self.assertEqual(self.bridge.albums, [])
        self.assertEqual(self.bridge.view, "library")
        self.assertFalse(self.bridge.loggedIn)
        self.assertEqual(self.calls[-1][0:2], ("DELETE", "/v1/session"))

    def test_album_name_validation(self):
        self.bridge.createAlbum(" ")
        self.bridge.createAlbum("a" * 101)
        self.assertEqual(len(self.errors), 2)
        self.assertFalse(self.calls)


if __name__ == "__main__":
    unittest.main()
