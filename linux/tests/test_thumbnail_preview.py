"""Native image-provider privacy and aspect-ratio regression tests."""
import unittest

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QSize
from PySide6.QtGui import QColor, QGuiApplication, QImage

from linux.main import ThumbnailProvider


class ThumbnailPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication(
            ["goreecloud-photos-thumbnail-tests"]
        )

    def test_private_jpeg_preview_retains_aspect_ratio(self):
        provider = ThumbnailProvider()
        original = QImage(96, 48, QImage.Format.Format_RGB32)
        original.fill(QColor("red"))
        payload = QByteArray()
        buffer = QBuffer(payload)
        self.assertTrue(buffer.open(QIODevice.OpenModeFlag.WriteOnly))
        self.assertTrue(original.save(buffer, "JPEG"))
        buffer.close()

        provider.images["synthetic-image"] = bytes(payload)
        preview = provider.requestImage("synthetic-image?v=1", QSize(), QSize(320, 320))
        self.assertFalse(preview.isNull())
        self.assertEqual((preview.width(), preview.height()), (320, 160))

        # The provider has no external thumbnail cache and never reads disk.
        provider.images.clear()
        missing = provider.requestImage("synthetic-image?v=1", QSize(), QSize(320, 320))
        self.assertTrue(missing.isNull())

    def test_private_thumbnail_missing_is_empty(self):
        provider = ThumbnailProvider()
        missing = provider.requestImage("absent", QSize(), QSize(512, 512))
        self.assertTrue(missing.isNull())


if __name__ == "__main__":
    unittest.main()
