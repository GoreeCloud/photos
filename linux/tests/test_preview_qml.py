"""Offscreen Qt Quick dialog acceptance with only synthetic state."""
import unittest
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QObject, QMetaObject, Qt
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest

from linux.main import Bridge, ThumbnailProvider


class NativePreviewDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication(
            ["goreecloud-photos-preview-acceptance"]
        )

    def setUp(self):
        self.engine = QQmlApplicationEngine()
        self.provider = ThumbnailProvider()
        sample = QImage(24, 12, QImage.Format.Format_RGB32)
        sample.fill(Qt.GlobalColor.green)
        payload = QByteArray()
        buffer = QBuffer(payload)
        self.assertTrue(buffer.open(QIODevice.OpenModeFlag.WriteOnly))
        self.assertTrue(sample.save(buffer, "JPEG"))
        buffer.close()
        self.provider.images["synthetic-test-photo"] = bytes(payload)
        self.engine.addImageProvider("preview", self.provider)
        self.bridge = Bridge("http://127.0.0.1:8787", self.provider)
        self.bridge._token = "synthetic-in-memory-session"
        self.bridge._items = [{
            "id": "synthetic-test-photo", "filename": "synthetic.png",
            "media_type": "image/png", "thumbVersion": "0",
        }]
        self.engine.rootContext().setContextProperty("photosBridge", self.bridge)
        self.engine.load(str(Path(__file__).resolve().parents[1] / "Main.qml"))
        self.assertTrue(self.engine.rootObjects(), "Native QML failed to load")
        self.window = self.engine.rootObjects()[0]
        self.dialog = self.window.findChild(QObject, "privatePhotoPreview")
        self.assertIsNotNone(self.dialog, "Missing native photo preview dialog")

    def tearDown(self):
        self.dialog = None
        self.window = None
        self.engine.clearComponentCache()
        self.engine = None
        self.app.processEvents()

    def test_preview_closes_and_forgets_selected_media_on_lock(self):
        self.window.setProperty("previewId", "synthetic-test-photo")
        self.window.setProperty("previewName", "synthetic.png")
        self.window.setProperty("previewMediaType", "image/png")
        opened = QMetaObject.invokeMethod(self.dialog, "open", Qt.ConnectionType.DirectConnection)
        self.assertTrue(opened)
        QTest.qWait(90)
        self.assertTrue(self.dialog.property("opened"))
        self.assertEqual(self.window.property("previewId"), "synthetic-test-photo")

        self.bridge._clear_session()
        QTest.qWait(150)
        self.assertFalse(self.dialog.property("opened"))
        self.assertEqual(self.window.property("previewId"), "")
        self.assertEqual(self.window.property("previewName"), "")

    def test_selection_is_dismissed_on_library_navigation(self):
        self.window.setProperty("previewId", "synthetic-test-photo")
        self.window.setProperty("previewName", "synthetic.png")
        self.window.setProperty("previewMediaType", "image/png")
        self.assertTrue(QMetaObject.invokeMethod(
            self.dialog, "open", Qt.ConnectionType.DirectConnection
        ))
        QTest.qWait(90)
        self.bridge._items = []
        self.bridge.libraryChanged.emit()
        QTest.qWait(150)
        self.assertFalse(self.dialog.property("opened"))
        self.assertEqual(self.window.property("previewId"), "")


if __name__ == "__main__":
    unittest.main()
