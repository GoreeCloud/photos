"""GoreeCloud Photos Linux client: native Qt Quick 6.12, private in-memory sessions."""
import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkAccessManager, QNetworkRequest
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtCore import QFile, QIODevice

ALLOWED_HTTP = {"localhost", "127.0.0.1", "::1"}


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

    @Property(bool, notify=loggedInChanged)
    def loggedIn(self):
        return bool(self._token)

    @Property("QVariantList", notify=libraryChanged)
    def items(self):
        return self._items

    def send(self, method, path, payload=None, callback=None, content_type="application/json"):
        request = QNetworkRequest(QUrl(self.server + path))
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
        self._items = []
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
            self._items = data.get("items", [])
            self.provider.images.clear()
            self.libraryChanged.emit()
            for item in self._items:
                if item.get("media_type", "").startswith("image/"):
                    self.fetch_thumb(item["id"], generation)
        self.send("GET", "/v1/assets?limit=100", callback=done)

    def fetch_thumb(self, asset_id, generation):
        request = QNetworkRequest(QUrl(self.server + "/v1/assets/" + asset_id + "/thumbnail"))
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
