"""GoreeCloud Photos Linux client: native Qt Quick 6.12, private in-memory sessions."""
import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from PySide6.QtCore import Qt, QBuffer, QByteArray, QFile, QIODevice, QObject, Property, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication, QImage, QImageReader
from PySide6.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider

ALLOWED_HTTP = {"localhost", "127.0.0.1", "::1"}
MAX_DOWNLOAD_BYTES = 512 * 1024 * 1024
MAX_JSON_BYTES = 4 * 1024 * 1024
MAX_THUMB_BYTES = 6 * 1024 * 1024
MAX_THUMB_DIMENSION = 2048


def safe_thumbnail(payload: bytes) -> bool:
    """Read JPEG dimensions without allocating image pixels for a suspicious reply."""
    if not payload or len(payload) > MAX_THUMB_BYTES:
        return False
    source = QBuffer()
    source.setData(QByteArray(payload))
    if not source.open(QIODevice.OpenModeFlag.ReadOnly):
        return False
    reader = QImageReader(source)
    reader.setDecideFormatFromContent(True)
    dimensions = reader.size()
    return (
        bytes(reader.format()).lower() in (b"jpeg", b"jpg")
        and dimensions.isValid()
        and 1 <= dimensions.width() <= MAX_THUMB_DIMENSION
        and 1 <= dimensions.height() <= MAX_THUMB_DIMENSION
    )


def read_bounded(reply, collector: bytearray, limit: int) -> bool:
    """Consume Qt chunks without letting untrusted network data grow without bound."""
    while reply.bytesAvailable():
        chunk = bytes(reply.read(min(65536, reply.bytesAvailable())))
        if len(collector) + len(chunk) > limit:
            # Caller sets its failure state before aborting, because Qt may
            # emit finished synchronously from abort().
            return False
        collector.extend(chunk)
    return True



class ThumbnailProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self.images = {}

    def requestImage(self, image_id, size, requested_size):
        image = QImage.fromData(self.images.get(image_id.split("?")[0], b""))
        if not image.isNull() and requested_size.isValid():
            image = image.scaled(
                requested_size, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        return image


class Bridge(QObject):
    error = Signal(str)
    message = Signal(str)
    libraryChanged = Signal()
    loggedInChanged = Signal()
    securityCompleted = Signal()

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
        self._albums = []
        self._album_id = ""
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

    @Property("QVariantList", notify=libraryChanged)
    def albums(self):
        return self._albums

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
        self._album_id = ""
        self._page = 0
        self.refresh()

    @Slot()
    def refreshAlbums(self):
        if not self._token:
            return
        generation = self._generation
        def done(data):
            if not self._token or generation != self._generation:
                return
            self._albums = data.get("items", [])
            self.libraryChanged.emit()
        self.send("GET", "/v1/albums", callback=done)

    @Slot(str)
    def viewAlbum(self, album_id):
        if not any(album.get("id") == album_id for album in self._albums):
            self.error.emit("Select an available album")
            return
        self._view = "album"
        self._album_id = album_id
        self._page = 0
        self.refresh()

    @Slot(str)
    def createAlbum(self, name):
        name = name.strip()
        if not self._token or not 1 <= len(name) <= 100:
            self.error.emit("Album name must contain 1-100 characters")
            return
        def done(data):
            self.message.emit("Album created")
            self.refreshAlbums()
            # Backend is the authority. Refresh albums so the new ID becomes selectable.
        self.send("POST", "/v1/albums", {"name": name}, done)

    @Slot(str, str)
    def addToAlbum(self, album_id, asset_id):
        if not self._token or self._view == "trash":
            self.error.emit("Unlock an active library view")
            return
        if not any(album.get("id") == album_id for album in self._albums):
            self.error.emit("Select an available album")
            return
        if not any(asset.get("id") == asset_id for asset in self._items):
            self.error.emit("Choose an available photo")
            return
        self.send(
            "POST", f"/v1/albums/{album_id}/assets/{asset_id}",
            callback=lambda _: (self.message.emit("Added to album"), self.refreshAlbums())
        )

    @Slot(str)
    def removeFromAlbum(self, asset_id):
        if not self._token or self._view != "album" or not self._album_id:
            self.error.emit("Select an album first")
            return
        if not any(asset.get("id") == asset_id for asset in self._items):
            self.error.emit("Choose a member of this album")
            return
        self.send(
            "DELETE", f"/v1/albums/{self._album_id}/assets/{asset_id}",
            callback=lambda _: (self.message.emit("Removed from album; original preserved"),
                                self.refresh(), self.refreshAlbums())
        )

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
        request.setTransferTimeout(30_000)
        request.setRawHeader(b"Accept", b"application/json")
        if self._token:
            request.setRawHeader(b"Authorization", ("Bearer " + self._token).encode())
        if payload is not None:
            request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, content_type)
        data = json.dumps(payload).encode() if payload is not None else b""
        reply = self.manager.sendCustomRequest(request, method.encode(), data)
        reply.setReadBufferSize(1024 * 1024)
        body = bytearray()
        too_large = False

        def receive():
            nonlocal too_large
            if not too_large and not read_bounded(reply, body, MAX_JSON_BYTES):
                too_large = True
                reply.abort()

        def done():
            receive()
            status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute) or 0
            error = reply.error()
            reply.deleteLater()
            if too_large:
                self.error.emit("API response exceeded 4 MiB safety limit")
                return
            if status < 200 or status >= 300:
                try:
                    detail = json.loads(body).get("detail", f"HTTP {status}")
                except (ValueError, TypeError, AttributeError):
                    detail = f"HTTP {status}"
                self.error.emit(str(detail)[:180])
                return
            if error != QNetworkReply.NetworkError.NoError:
                self.error.emit("Authenticated API request failed")
                return
            try:
                result = json.loads(body) if body else {}
                if not isinstance(result, dict):
                    raise ValueError("Response must be a JSON object")
            except ValueError:
                self.error.emit("Invalid server response")
                return
            if callback:
                callback(result)

        reply.readyRead.connect(receive)
        reply.finished.connect(done)

    @Slot(str)
    def login(self, password):
        if not password:
            return
        def done(data):
            self._token = data["access_token"]
            self.loggedInChanged.emit()
            self.refresh()
            self.refreshAlbums()
        self.send("POST", "/v1/session", {"password": password}, done)

    def _clear_session(self):
        """Immediately discard session credentials and private in-memory library data."""
        self._token = ""
        self._generation += 1
        self._items = []
        self._albums = []
        self._album_id = ""
        self._view = "library"
        self._search = ""
        self._total = 0
        self._page = 0
        self.provider.images.clear()
        self.loggedInChanged.emit()
        self.libraryChanged.emit()

    @Slot()
    def logout(self):
        if self._token:
            self.send("DELETE", "/v1/session")
        self._clear_session()

    @Slot(str, str, str)
    def changePassword(self, current, replacement, confirmation):
        if not self._token:
            self.error.emit("Unlock your library first")
            return
        if not 1 <= len(current) <= 1024:
            self.error.emit("Enter the current library password")
            return
        if not 12 <= len(replacement) <= 1024:
            self.error.emit("New password must contain 12–1024 characters")
            return
        if replacement == current:
            self.error.emit("Choose a new password different from the current one")
            return
        if replacement != confirmation:
            self.error.emit("New password and confirmation do not match")
            return
        generation = self._generation

        def done(response):
            if generation != self._generation or not self._token:
                return
            if response.get("changed") is not True or response.get("sessions_revoked") is not True:
                self.error.emit("Password rotation was not confirmed")
                return
            self._clear_session()
            self.securityCompleted.emit()
            self.message.emit("Password changed; all devices signed out. Unlock again.")

        self.send(
            "POST", "/v1/settings/password",
            {"current_password": current, "new_password": replacement}, done
        )

    @Slot(str)
    def revokeAllSessions(self, current):
        if not self._token or not 1 <= len(current) <= 1024:
            self.error.emit("Unlock and enter your current library password")
            return
        generation = self._generation

        def done(response):
            if generation != self._generation or not self._token:
                return
            if response.get("sessions_revoked") is not True:
                self.error.emit("Global sign-out was not confirmed")
                return
            self._clear_session()
            self.securityCompleted.emit()
            self.message.emit("Every device signed out; password unchanged.")

        self.send("POST", "/v1/settings/revoke-sessions", {"password": current}, done)

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
        if self._view == "album" and self._album_id:
            query = urlencode({
                "limit": 60, "offset": self._page * 60, "search": self._search,
            })
            path = f"/v1/albums/{self._album_id}/assets?" + query
        else:
            path = "/v1/assets?" + query
        self.send("GET", path, callback=done)

    def fetch_thumb(self, asset_id, generation):
        request = QNetworkRequest(QUrl(self.server + "/v1/assets/" + asset_id + "/thumbnail"))
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.ManualRedirectPolicy,
        )
        request.setRawHeader(b"Authorization", ("Bearer " + self._token).encode())
        request.setTransferTimeout(30_000)
        reply = self.manager.get(request)
        reply.setReadBufferSize(1024 * 1024)
        image_bytes = bytearray()
        too_large = False

        def receive():
            nonlocal too_large
            if not too_large and not read_bounded(reply, image_bytes, MAX_THUMB_BYTES):
                too_large = True
                reply.abort()

        def done():
            receive()
            status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute) or 0
            error = reply.error()
            reply.deleteLater()
            if (not too_large and status == 200
                    and error == QNetworkReply.NetworkError.NoError
                    and self._token and generation == self._generation
                    and safe_thumbnail(bytes(image_bytes))):
                self.provider.images[asset_id] = bytes(image_bytes)
                # Drop QML's cache by refreshing model sources with generation suffix.
                self._items = [{**x, "thumbVersion": str(len(self.provider.images))}
                               for x in self._items]
                self.libraryChanged.emit()

        reply.readyRead.connect(receive)
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
