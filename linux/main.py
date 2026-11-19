"""GoreeCloud Photos Linux client: native Qt Quick 6.12, private in-memory sessions."""
import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtCore import QFile, QIODevice

ALLOWED_HTTP = {"localhost", "127.0.0.1", "::1"}
MAX_DOWNLOAD_BYTES = 512 * 1024 * 1024


class ThumbnailProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self.images = {}

    def requestImage(self, image_id, size, requested_size):
        image = QImage.fromData(self.images.get(image_id.split("?")[0], b""))
        if not image.isNull() and requested_size.isValid():
            image = image.scaled(requested_size)
        return image


class Bridge(QObject):
    error = Signal(str)
    message = Signal(str)
    libraryChanged = Signal()
    loggedInChanged = Signal()

    def __init__(self, server, provider):
        super().__init__()
        parsed = urlsplit(server)
        if parsed.scheme != "https" and not (
            parsed.scheme == "http" and parsed.hostname in ALLOWED_HTTP
        ):
            raise ValueError("Remote servers require HTTPS; HTTP is restricted to loopback.")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Invalid server URL")
        self.server = server.rstrip("/")
        self.provider = provider
        self.manager = QNetworkAccessManager(self)
        self._token = ""
        self._items = []
        self._generation = 0
        self._view = "library"
        self._search = ""
        self._page = 0
        self._total = 0

    @Property(bool, notify=loggedInChanged)
    def loggedIn(self):
        return bool(self._token)

    @Property("QVariantList", notify=libraryChanged)
    def items(self):
        return self._items

    @Property(str, notify=libraryChanged)
    def view(self):
        return self._view

    @Property(int, notify=libraryChanged)
    def currentPage(self):
        return self._page + 1

    @Property(int, notify=libraryChanged)
    def pageCount(self):
        return max(1, (self._total + 59) // 60)

    @Property(int, notify=libraryChanged)
    def total(self):
        return self._total

    @Slot(str)
    def setView(self, view):
        if view not in ("library", "favorites", "trash"):
            return
        self._view = view
        self._page = 0
        self.refresh()

    @Slot(str)
    def setSearch(self, value):
        self._search = value[:128]
        self._page = 0
        self.refresh()

    @Slot(int)
    def changePage(self, change):
        new_page = self._page + change
        if 0 <= new_page and new_page * 60 < self._total:
            self._page = new_page
            self.refresh()

    def send(self, method, path, payload=None, callback=None, content_type="application/json"):
        request = QNetworkRequest(QUrl(self.server + path))
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.ManualRedirectPolicy,
        )
        request.setRawHeader(b"Accept", b"application/json")
        if self._token:
            request.setRawHeader(b"Authorization", ("Bearer " + self._token).encode())
        if payload is not None:
            request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, content_type)
        data = json.dumps(payload).encode() if payload is not None else b""
        reply = self.manager.sendCustomRequest(request, method.encode(), data)
        def done():
            status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute) or 0
            body = bytes(reply.readAll())
            reply.deleteLater()
            if status < 200 or status >= 300:
                try:
                    detail = json.loads(body).get("detail", f"HTTP {status}")
                except (ValueError, TypeError):
                    detail = f"HTTP {status}"
                self.error.emit(str(detail))
                return
            try:
                result = json.loads(body) if body else {}
            except ValueError:
                self.error.emit("Invalid server response")
                return
            if callback:
                callback(result)
        reply.finished.connect(done)

    @Slot(str)
    def login(self, password):
        if not password:
            return
        def done(data):
            self._token = data["access_token"]
            self.loggedInChanged.emit()
            self.refresh()
        self.send("POST", "/v1/session", {"password": password}, done)

    @Slot()
    def logout(self):
        if self._token:
            self.send("DELETE", "/v1/session")
        self._token = ""
        self._generation += 1
        self._items = []
        self._total = 0
        self._page = 0
        self.provider.images.clear()
        self.loggedInChanged.emit()
        self.libraryChanged.emit()

    @Slot()
    def refresh(self):
        if not self._token:
            return
        self._generation += 1
        generation = self._generation
        def done(data):
            if generation != self._generation:
                return
            new_total = data.get("total", 0)
            if self._page and self._page * 60 >= new_total:
                self._page = max(0, (new_total - 1) // 60)
                self.refresh()
                return
            self._total = new_total
            self._items = data.get("items", [])
            self.provider.images.clear()
            self.libraryChanged.emit()
            for item in self._items:
                if item.get("media_type", "").startswith("image/"):
                    self.fetch_thumb(item["id"], generation)
        query = urlencode({
            "limit": 60, "offset": self._page * 60,
            "favorite": str(self._view == "favorites").lower(),
            "trashed": str(self._view == "trash").lower(),
            "search": self._search,
        })
        self.send("GET", "/v1/assets?" + query, callback=done)

    def fetch_thumb(self, asset_id, generation):
        request = QNetworkRequest(QUrl(self.server + "/v1/assets/" + asset_id + "/thumbnail"))
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.ManualRedirectPolicy,
        )
        request.setRawHeader(b"Authorization", ("Bearer " + self._token).encode())
        reply = self.manager.get(request)
        def done():
            status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute) or 0
            payload = bytes(reply.readAll())
            reply.deleteLater()
            if 200 <= status < 300 and self._token and generation == self._generation:
                self.provider.images[asset_id] = payload
                # Drop QML's cache by refreshing model sources with generation suffix.
                self._items = [{**x, "thumbVersion": str(len(self.provider.images))}
                               for x in self._items]
                self.libraryChanged.emit()
        reply.finished.connect(done)

    @Slot(str)
    def restore(self, asset_id):
        self.send("POST", f"/v1/assets/{asset_id}/restore", callback=lambda _: self.refresh())

    @Slot(str, str)
    def download(self, asset_id, file_url):
        """Private, bounded, streamed original; never replace an existing file."""
        if (not self._token or self._view == "trash"
                or not re.fullmatch(r"[0-9a-f-]{36}", asset_id)
                or not any(item.get("id") == asset_id for item in self._items)):
            self.error.emit("Choose an active photo from the unlocked library")
            return
        path = QUrl(file_url).toLocalFile()
        if not path:
            self.error.emit("Choose a local destination file")
            return
        target = Path(path).absolute()
        if target.exists() or target.is_symlink():
            self.error.emit("Destination already exists; choose a different filename")
            return
        if not target.parent.is_dir():
            self.error.emit("Destination folder does not exist")
            return
        try:
            handle = tempfile.NamedTemporaryFile(
                mode="w+b", dir=target.parent, prefix=".photos-download-", delete=False,
            )
            os.fchmod(handle.fileno(), 0o600)
        except OSError:
            self.error.emit("Cannot open the selected destination folder")
            return
        temporary = Path(handle.name)
        request = QNetworkRequest(
            QUrl(self.server + "/v1/assets/" + asset_id + "/original")
        )
        request.setRawHeader(b"Authorization", ("Bearer " + self._token).encode())
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.ManualRedirectPolicy,
        )
        request.setTransferTimeout(90_000)
        generation = self._generation
        reply = self.manager.get(request)
        reply.setReadBufferSize(2 * 1024 * 1024)
        total = 0
        failed = False

        def read_data():
            nonlocal total, failed
            if failed:
                return
            if generation != self._generation or not self._token:
                failed = True
                reply.abort()
                return
            while reply.bytesAvailable() and not failed:
                block = bytes(reply.read(min(1024 * 1024, reply.bytesAvailable())))
                if not block:
                    break
                total += len(block)
                if total > MAX_DOWNLOAD_BYTES:
                    failed = True
                    reply.abort()
                    return
                try:
                    handle.write(block)
                except OSError:
                    failed = True
                    reply.abort()
                    return

        def done():
            read_data()
            status = reply.attribute(
                QNetworkRequest.Attribute.HttpStatusCodeAttribute
            ) or 0
            reply_error = reply.error()
            reply.deleteLater()
            try:
                if (failed or generation != self._generation
                        or status != 200 or reply_error != QNetworkReply.NetworkError.NoError):
                    if generation == self._generation:
                        self.error.emit("Original download was interrupted or rejected")
                    return
                handle.flush()
                os.fsync(handle.fileno())
                handle.close()
                # Exclusive atomic promotion: never replace even if another
                # application created the target while bytes were arriving.
                os.link(temporary, target)
                self.message.emit("Original saved privately to selected folder")
            except FileExistsError:
                self.error.emit("Destination already exists; no file was overwritten")
            except OSError:
                self.error.emit("Could not save the downloaded original")
            finally:
                handle.close()
                temporary.unlink(missing_ok=True)

        reply.readyRead.connect(read_data)
        reply.finished.connect(done)

    @Slot(str)
    def upload(self, file_url):
        path = QUrl(file_url).toLocalFile()
        if not path:
            self.error.emit("Select a local file")
            return
        source = QFile(path)
        if not source.open(QIODevice.OpenModeFlag.ReadOnly):
            self.error.emit("Could not open selected file")
            return
        safe = Path(path).name.replace('"', "").replace("\r", "").replace("\n", "")
        request = QNetworkRequest(QUrl(self.server + "/v1/assets"))
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.ManualRedirectPolicy,
        )
        request.setRawHeader(b"Authorization", ("Bearer " + self._token).encode())
        multipart = QHttpMultiPart(QHttpMultiPart.ContentType.FormDataType)
        part = QHttpPart()
        part.setRawHeader(b"Content-Disposition",
                          ('form-data; name="file"; filename="' + safe + '"').encode("utf-8"))
        part.setBodyDevice(source)
        source.setParent(multipart)
        multipart.append(part)
        reply = self.manager.post(request, multipart)
        multipart.setParent(reply)
        def done():
            status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute) or 0
            reply.deleteLater()
            if status == 201:
                self.message.emit("Photo uploaded")
                self.refresh()
            else:
                self.error.emit(f"Upload failed (HTTP {status})")
        reply.finished.connect(done)

    @Slot(str, bool)
    def favorite(self, asset_id, state):
        self.send("PATCH", f"/v1/assets/{asset_id}/favorite", {"favorite": state},
                  lambda _: self.refresh())

    @Slot(str)
    def trash(self, asset_id):
        self.send("DELETE", f"/v1/assets/{asset_id}", callback=lambda _: self.refresh())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="http://127.0.0.1:8787")
    args = parser.parse_args()
    app = QGuiApplication(sys.argv[:1])
    engine = QQmlApplicationEngine()
    provider = ThumbnailProvider()
    engine.addImageProvider("preview", provider)
    bridge = Bridge(args.server, provider)
    engine.rootContext().setContextProperty("photosBridge", bridge)
    engine.load(str(Path(__file__).with_name("Main.qml")))
    if not engine.rootObjects():
        return 1
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
