"""First-party GoreeCloud Photos command line; no plaintext credential arguments."""
from __future__ import annotations

import argparse
import getpass
import http.client
import json
import os
import re
import secrets
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from uuid import UUID

from . import backup as offline

VERSION = "0.1.0"
MAX_UPLOAD = 512 * 1024 * 1024
CHUNK = 1024 * 1024


class PhotosError(Exception):
    """An error safe to display without credentials."""


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def validate_server(value: str) -> str:
    try:
        url = urllib.parse.urlsplit(value)
        port = url.port
    except ValueError as error:
        raise PhotosError("Invalid server URL") from error
    if (url.username or url.password or url.query or url.fragment or url.path not in ("", "/")
            or not url.hostname or port == 0):
        raise PhotosError("Server URL must contain a host and optional port only")
    if url.scheme != "https" and not (
        url.scheme == "http" and url.hostname in {"127.0.0.1", "localhost", "::1"}
    ):
        raise PhotosError("Remote servers require HTTPS")
    if url.scheme not in {"https", "http"}:
        raise PhotosError("Unsupported server scheme")
    return value.rstrip("/")


def valid_id(identifier: str) -> str:
    try:
        parsed = UUID(identifier)
    except ValueError as error:
        raise PhotosError("Invalid photo identifier") from error
    if str(parsed) != identifier:
        raise PhotosError("Use a canonical lowercase photo identifier")
    return identifier


class Api:
    def __init__(self, server: str, token: str = ""):
        self.server = validate_server(server)
        self.token = token
        # Ignore environment HTTP_PROXY: explicit server selection must remain direct.
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirects())

    def request(self, method: str, path: str, payload: dict | None = None):
        if not path.startswith("/") or path.startswith("//"):
            raise PhotosError("Invalid API path")
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(
            self.server + path, data=data, method=method,
            headers={
                "Accept": "application/json",
                **({"Authorization": "Bearer " + self.token} if self.token else {}),
                **({"Content-Type": "application/json"} if data is not None else {}),
            },
        )
        try:
            with self.opener.open(req, timeout=30) as response:
                body = response.read(4 * 1024 * 1024)
                if response.read(1):
                    raise PhotosError("Response exceeds safe size limit")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as error:
            raise PhotosError(f"Server returned HTTP {error.code}") from None
        except urllib.error.URLError:
            raise PhotosError("Cannot reach configured Photos server") from None

    def sign_in(self) -> bool:
        if self.token:
            return False
        password = getpass.getpass("Private library password: ")
        if not password:
            raise PhotosError("A nonempty password is required")
        try:
            response = self.request("POST", "/v1/session", {"password": password})
        finally:
            password = ""  # Do not retain plaintext beyond authentication.
        self.token = response["access_token"]
        return True

    def sign_out(self) -> None:
        try:
            self.request("DELETE", "/v1/session")
        finally:
            self.token = ""

    def download(self, identifier: str, output: Path) -> dict:
        valid_id(identifier)
        target = output.absolute()
        if target.exists():
            raise PhotosError("Download destination exists; refusing to overwrite")
        if not target.parent.is_dir():
            raise PhotosError("Download destination folder does not exist")
        req = urllib.request.Request(
            self.server + f"/v1/assets/{identifier}/original",
            headers={"Authorization": "Bearer " + self.token, "Accept": "application/octet-stream"},
        )
        temporary = None
        try:
            with (
                self.opener.open(req, timeout=120) as response,
                tempfile.NamedTemporaryFile(
                    dir=target.parent, prefix=".photos-download-", delete=False
                ) as handle,
            ):
                temporary = Path(handle.name)
                os.fchmod(handle.fileno(), 0o600)
                bytes_saved = 0
                while block := response.read(CHUNK):
                    bytes_saved += len(block)
                    if bytes_saved > MAX_UPLOAD:
                        raise PhotosError("Downloaded object exceeds 512 MiB limit")
                    handle.write(block)
                handle.flush()
                os.fsync(handle.fileno())
            os.link(temporary, target)  # Exclusive: never replace existing user files.
            return {"saved_to": str(target), "bytes": bytes_saved}
        except urllib.error.HTTPError as error:
            raise PhotosError(f"Server returned HTTP {error.code}") from None
        except urllib.error.URLError:
            raise PhotosError("Cannot reach configured Photos server") from None
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)

    def upload(self, file_path: Path) -> dict:
        if file_path.is_symlink() or not file_path.is_file():
            raise PhotosError("Only regular, non-symlink files may be uploaded")
        size = file_path.stat().st_size
        if not 0 < size <= MAX_UPLOAD:
            raise PhotosError("Upload size must be between 1 byte and 512 MiB")
        parsed = urllib.parse.urlsplit(self.server)
        connection_type = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
        client = connection_type(parsed.hostname, port=parsed.port, timeout=120)
        boundary = "GoreeCloudPhotos" + secrets.token_hex(16)
        safe_name = re.sub(r'[^A-Za-z0-9 ._()-]', "_", file_path.name)[:160] or "untitled"
        before = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{safe_name}\"\r\n"
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode()
        after = f"\r\n--{boundary}--\r\n".encode()
        try:
            client.putrequest("POST", "/v1/assets")
            client.putheader("Content-Type", "multipart/form-data; boundary=" + boundary)
            client.putheader("Content-Length", str(len(before) + size + len(after)))
            client.putheader("Authorization", "Bearer " + self.token)
            client.endheaders()
            client.send(before)
            with file_path.open("rb") as source:
                while chunk := source.read(CHUNK):
                    client.send(chunk)
            client.send(after)
            response = client.getresponse()
            if not 200 <= response.status < 300:
                raise PhotosError(f"Server returned HTTP {response.status}")
            payload = response.read(4096)
            return json.loads(payload)
        except OSError as error:
            raise PhotosError("Upload connection or file read failed") from error
        finally:
            client.close()


def parse_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(prog="photosctl", description="Private GoreeCloud Photos command line")
    parser.add_argument("--version", action="version", version="GoreeCloud Photos " + VERSION)
    parser.add_argument("--server", default="http://127.0.0.1:8787",
                        help="HTTPS Photos API URL, or HTTP on loopback only")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("health", help="Read server health without authentication")
    photos = sub.add_parser("list", help="List private photo assets")
    photos.add_argument("--search", default="")
    photos.add_argument("--favorites", action="store_true")
    photos.add_argument("--trash", action="store_true")
    photos.add_argument("--limit", type=int, default=60)
    photos.add_argument("--page", type=int, default=1)
    sub.add_parser("change-password", help="Rotate library password and revoke all sessions")
    sub.add_parser("albums", help="List private albums")
    sub.add_parser("stats", help="Read private library counts and original storage bytes")
    creation = sub.add_parser("create-album", help="Create a private album")
    creation.add_argument("name")
    up = sub.add_parser("upload", help="Upload one explicit local media file")
    up.add_argument("file", type=Path)
    down = sub.add_parser("download", help="Save an original without overwriting any file")
    down.add_argument("id")
    down.add_argument("--output", required=True, type=Path)
    like = sub.add_parser("favorite", help="Change an asset favorite flag")
    like.add_argument("id")
    like.add_argument("--off", action="store_true")
    trash = sub.add_parser("trash", help="Move an asset to recoverable trash")
    trash.add_argument("id")
    trash.add_argument("--yes", action="store_true", help="Acknowledge the trash action")
    recover = sub.add_parser("restore", help="Restore asset from trash")
    recover.add_argument("id")
    bk = sub.add_parser("backup", help="Create an offline unencrypted backup with API stopped")
    bk.add_argument("--data-dir", required=True, type=Path)
    bk.add_argument("--output", required=True, type=Path)
    live = sub.add_parser("verify-library", help="Read-only offline integrity check of local data")
    live.add_argument("--data-dir", required=True, type=Path)
    verify = sub.add_parser("verify-backup", help="Read-only archive integrity check")
    verify.add_argument("--input", required=True, type=Path)
    restore_bk = sub.add_parser("restore-backup", help="Recover to a new, nonexistent data folder")
    restore_bk.add_argument("--input", required=True, type=Path)
    restore_bk.add_argument("--data-dir", required=True, type=Path)
    return parser.parse_args(argv)


def run(args):
    if args.command == "backup":
        return offline.backup(args.data_dir, args.output)
    if args.command == "verify-library":
        return offline.verify_library(args.data_dir)
    if args.command == "verify-backup":
        return offline.verify(args.input)
    if args.command == "restore-backup":
        return offline.restore(args.input, args.data_dir)
    api = Api(args.server, os.environ.get("PHOTOS_ACCESS_TOKEN", ""))
    if args.command == "health":
        return api.request("GET", "/health")
    if args.command == "change-password":
        current = getpass.getpass("Current private library password: ")
        proposed = getpass.getpass("New private library password: ")
        confirmed = getpass.getpass("Confirm new private library password: ")
        if not current or len(proposed) < 12 or len(proposed) > 1024:
            raise PhotosError("New password must be 12-1024 characters")
        if proposed != confirmed:
            raise PhotosError("New password confirmation does not match")
        if proposed == current:
            raise PhotosError("Choose a new password different from the current one")
        ephemeral = not bool(api.token)
        if ephemeral:
            result = api.request("POST", "/v1/session", {"password": current})
            api.token = result["access_token"]
        try:
            return api.request("POST", "/v1/settings/password", {
                "current_password": current, "new_password": proposed
            })
        finally:
            current = proposed = confirmed = ""
            if ephemeral:
                # Successful rotation invalidates *all* tokens; logout then
                # returns 401. A failed rotation must still revoke our session.
                try:
                    api.sign_out()
                except PhotosError:
                    pass
    ephemeral = api.sign_in()
    try:
        if args.command == "list":
            if not 1 <= args.limit <= 100 or not 1 <= args.page <= 25_000 or len(args.search) > 128:
                raise PhotosError("Limit, page or search length out of bounds")
            query = urllib.parse.urlencode({
                "favorite": str(args.favorites).lower(),
                "trashed": str(args.trash).lower(),
                "limit": args.limit, "offset": (args.page - 1) * args.limit,
                "search": args.search,
            })
            return api.request("GET", "/v1/assets?" + query)
        if args.command == "albums":
            return api.request("GET", "/v1/albums")
        if args.command == "stats":
            return api.request("GET", "/v1/library/stats")
        if args.command == "create-album":
            if not 1 <= len(args.name.strip()) <= 100:
                raise PhotosError("Album name must be 1–100 characters")
            return api.request("POST", "/v1/albums", {"name": args.name.strip()})
        if args.command == "upload":
            return api.upload(args.file)
        if args.command == "download":
            return api.download(args.id, args.output)
        if args.command == "favorite":
            return api.request("PATCH", f"/v1/assets/{valid_id(args.id)}/favorite",
                               {"favorite": not args.off})
        if args.command == "trash":
            valid_id(args.id)
            if not args.yes:
                raise PhotosError("Trash requires --yes (reversible, but affects the library)")
            return api.request("DELETE", f"/v1/assets/{args.id}")
        if args.command == "restore":
            return api.request("POST", f"/v1/assets/{valid_id(args.id)}/restore")
        raise PhotosError("Unknown command")
    finally:
        if ephemeral:
            api.sign_out()


def main(argv: list[str] | None = None) -> int:
    try:
        result = run(parse_args(argv))
        print(json.dumps(result, sort_keys=True))
        return 0
    except (PhotosError, ValueError, OSError) as error:
        print("photosctl: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
