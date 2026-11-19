"""Native Qt owner password and global-session controls with synthetic replies."""
import unittest

from PySide6.QtGui import QGuiApplication

from linux.main import Bridge, ThumbnailProvider


PASSWORD = "current-private-test-password"
NEW_PASSWORD = "replacement-private-test-password"


class OwnerSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication(["photos-owner-security"])

    def setUp(self):
        self.provider = ThumbnailProvider()
        self.bridge = Bridge("http://127.0.0.1:8787", self.provider)
        self.bridge._token = "synthetic-in-memory-bearer"
        self.bridge._items = [{"id": "synthetic-media"}]
        self.bridge._albums = [{"id": "synthetic-album"}]
        self.bridge._album_id = "synthetic-album"
        self.bridge._view = "album"
        self.bridge._search = "private search"
        self.provider.images["synthetic-media"] = b"synthetic-thumbnail"
        self.calls = []
        self.callbacks = []
        self.errors = []
        self.messages = []
        self.success = []
        self.bridge.error.connect(self.errors.append)
        self.bridge.message.connect(self.messages.append)
        self.bridge.securityCompleted.connect(lambda: self.success.append(True))

        def send(method, path, payload=None, callback=None, content_type="application/json"):
            self.calls.append((method, path, payload))
            if callback:
                self.callbacks.append(callback)

        self.bridge.send = send

    def assert_private_state_cleared(self):
        self.assertFalse(self.bridge.loggedIn)
        self.assertEqual(self.bridge.items, [])
        self.assertEqual(self.bridge.albums, [])
        self.assertEqual(self.bridge.view, "library")
        self.assertEqual(self.bridge._search, "")
        self.assertEqual(self.bridge._album_id, "")
        self.assertEqual(self.provider.images, {})

    def test_password_rotation_requires_confirmation_and_disposes_state(self):
        self.bridge.changePassword(PASSWORD, NEW_PASSWORD, NEW_PASSWORD)
        self.assertEqual(self.calls, [
            ("POST", "/v1/settings/password",
             {"current_password": PASSWORD, "new_password": NEW_PASSWORD})
        ])
        self.callbacks.pop()({"changed": True, "sessions_revoked": True})
        self.assert_private_state_cleared()
        self.assertEqual(self.success, [True])
        self.assertTrue(any("Password changed" in x for x in self.messages))

    def test_global_revoke_preserves_password_but_discards_session(self):
        self.bridge.revokeAllSessions(PASSWORD)
        self.assertEqual(self.calls[0], (
            "POST", "/v1/settings/revoke-sessions", {"password": PASSWORD}
        ))
        self.callbacks.pop()({"sessions_revoked": True})
        self.assert_private_state_cleared()
        self.assertEqual(self.success, [True])
        self.assertTrue(any("password unchanged" in x for x in self.messages))

    def test_invalid_credentials_and_unconfirmed_server_response(self):
        self.bridge.changePassword("", NEW_PASSWORD, NEW_PASSWORD)
        self.bridge.changePassword(PASSWORD, "too-short", "too-short")
        self.bridge.changePassword(PASSWORD, PASSWORD, PASSWORD)
        self.bridge.changePassword(PASSWORD, NEW_PASSWORD, "mismatch")
        self.bridge.revokeAllSessions("")
        self.assertEqual(len(self.errors), 5)
        self.assertFalse(self.calls)
        self.bridge.changePassword(PASSWORD, NEW_PASSWORD, NEW_PASSWORD)
        self.callbacks.pop()({"changed": True, "sessions_revoked": False})
        self.assertTrue(self.bridge.loggedIn)
        self.assertFalse(self.success)

    def test_stale_reply_after_lock_is_ignored(self):
        self.bridge.revokeAllSessions(PASSWORD)
        callback = self.callbacks.pop()
        self.bridge.logout()
        callback({"sessions_revoked": True})
        self.assert_private_state_cleared()
        self.assertFalse(self.success)
        self.assertEqual(self.calls[-1][:2], ("DELETE", "/v1/session"))


if __name__ == "__main__":
    unittest.main()
