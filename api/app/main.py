"""GoreeCloud Photos single-library API. No telemetry, public files, or implicit signup."""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import tempfile
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from urllib.parse import quote
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel, Field

Image.MAX_IMAGE_PIXELS = 50_000_000
CHUNK = 1024 * 1024
MAX_BYTES = 512 * 1024 * 1024
TOKEN_SECONDS = 24 * 3600


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    admin_password: str | None
    cors_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")


def from_env() -> Settings:
    return Settings(
        Path(os.environ.get("PHOTOS_DATA_DIR", "./data")).resolve(),
        os.environ.get("PHOTOS_ADMIN_PASSWORD"),
        tuple(s.strip() for s in os.environ.get(
            "PHOTOS_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",") if s.strip()),
    )


@contextmanager
def database(settings: Settings):
    conn = sqlite3.connect(settings.data_dir / "photos.sqlite3", timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def make_password_hash(password: str) -> str:
    salt = os.urandom(16)
    derived = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return salt.hex() + ":" + derived.hex()


def check_password(password: str, stored: str) -> bool:
    salt, expected = stored.split(":")
    actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1)
    return hmac.compare_digest(actual, bytes.fromhex(expected))


def init_storage(settings: Settings) -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    settings.data_dir.chmod(0o700)
    for folder in ("objects", "previews", "tmp"):
        (settings.data_dir / folder).mkdir(parents=True, exist_ok=True, mode=0o700)
    with database(settings) as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS configuration (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS sessions (digest TEXT PRIMARY KEY, expires INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY, sha256 TEXT NOT NULL UNIQUE, filename TEXT NOT NULL,
                media_type TEXT NOT NULL, bytes INTEGER NOT NULL, created_at TEXT NOT NULL,
                favorite INTEGER NOT NULL DEFAULT 0, deleted_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_assets_created ON assets(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_assets_deleted ON assets(deleted_at);
            CREATE TABLE IF NOT EXISTS albums (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS album_assets (
                album_id TEXT NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
                asset_id TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
                PRIMARY KEY (album_id, asset_id)
            );
        """)
        row = db.execute("SELECT value FROM configuration WHERE key='password'").fetchone()
        if row is None:
            if not settings.admin_password or len(settings.admin_password) < 12:
                raise RuntimeError("First startup requires PHOTOS_ADMIN_PASSWORD (at least 12 characters).")
            db.execute("INSERT INTO configuration VALUES('password', ?)",
                       (make_password_hash(settings.admin_password),))


def sniff_media(header: bytes) -> tuple[str, str] | None:
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", ".jpg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", ".png"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif", ".gif"
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "image/webp", ".webp"
    if header[4:8] == b"ftyp" and header[8:12] in (b"isom", b"iso2", b"mp41", b"mp42", b"avc1"):
        return "video/mp4", ".mp4"
    return None


def safe_name(name: str | None) -> str:
    cleaned = (name or "untitled").replace("\\", "/").split("/")[-1]
    cleaned = "".join(ch for ch in cleaned if 31 < ord(ch) < 127 and ch not in "\"<>")
    return cleaned[:180] or "untitled"


def asset_dict(row: sqlite3.Row) -> dict:
    return {key: (bool(value) if key == "favorite" else value) for key, value in dict(row).items()}


class PasswordIn(BaseModel):
    password: str = Field(min_length=1, max_length=1024)


class FavoriteIn(BaseModel):
    favorite: bool


class AlbumIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or from_env()
    init_storage(settings)
    app = FastAPI(title="GoreeCloud Photos", version="0.1.0", docs_url=None, redoc_url=None)
    app.add_middleware(
        CORSMiddleware, allow_origins=list(settings.cors_origins), allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type"]
    )
    failed: dict[str, list[float]] = {}
    failed_lock = threading.Lock()

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "private, no-store"
        return response

    def authorized(authorization: Annotated[str | None, Header()] = None) -> None:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})
        token = authorization[7:]
        if len(token) != 43 or not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
            raise HTTPException(401, "Invalid session")
        digest = hashlib.sha256(token.encode()).hexdigest()
        with database(settings) as db:
            row = db.execute("SELECT expires FROM sessions WHERE digest=?", (digest,)).fetchone()
        if row is None or row["expires"] <= int(time.time()):
            raise HTTPException(401, "Session expired or invalid")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/v1/session")
    def login(body: PasswordIn, request: Request):
        # Per-process backstop; enforce edge rate limits for multi-worker or Internet exposure.
        peer = request.client.host if request.client else "unknown"
        now = time.monotonic()
        with failed_lock:
            attempts = [t for t in failed.get(peer, []) if now - t < 900]
            failed[peer] = attempts
            if len(attempts) >= 5:
                raise HTTPException(429, "Too many login attempts; try later")
        with database(settings) as db:
            row = db.execute("SELECT value FROM configuration WHERE key='password'").fetchone()
            valid = check_password(body.password, row["value"])
            if not valid:
                with failed_lock:
                    failed[peer].append(now)
                raise HTTPException(401, "Invalid password")
            token = secrets.token_urlsafe(32)
            expiry = int(time.time()) + TOKEN_SECONDS
            db.execute("DELETE FROM sessions WHERE expires <= ?", (int(time.time()),))
            db.execute("INSERT INTO sessions VALUES (?,?)",
                       (hashlib.sha256(token.encode()).hexdigest(), expiry))
        with failed_lock:
            failed.pop(peer, None)
        return {"access_token": token, "expires_at": expiry}

    @app.delete("/v1/session", status_code=204, dependencies=[Depends(authorized)])
    def logout(authorization: Annotated[str, Header()]):
        with database(settings) as db:
            db.execute("DELETE FROM sessions WHERE digest=?",
                       (hashlib.sha256(authorization[7:].encode()).hexdigest(),))
        return Response(status_code=204)

    @app.get("/v1/assets", dependencies=[Depends(authorized)])
    def list_assets(
        search: str = Query("", max_length=128), favorite: bool = False, trashed: bool = False,
        limit: int = Query(60, ge=1, le=100), offset: int = Query(0, ge=0, le=1_000_000)
    ):
        where = ["deleted_at IS NOT NULL" if trashed else "deleted_at IS NULL"]
        args: list[object] = []
        if favorite:
            where.append("favorite=1")
        if search:
            where.append("filename LIKE ? ESCAPE '\\'")
            args.append("%" + search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%")
        clause = " AND ".join(where)
        with database(settings) as db:
            count = db.execute(f"SELECT count(*) AS c FROM assets WHERE {clause}", args).fetchone()["c"]
            rows = db.execute(
                f"SELECT * FROM assets WHERE {clause} ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
                [*args, limit, offset],
            ).fetchall()
        return {"items": [asset_dict(row) for row in rows], "total": count}

    @app.post("/v1/assets", status_code=201, dependencies=[Depends(authorized)])
    async def upload(file: Annotated[UploadFile, File()]):
        temp_path: Path | None = None
        h = hashlib.sha256()
        size = 0
        header = b""
        try:
            with tempfile.NamedTemporaryFile(dir=settings.data_dir / "tmp", delete=False) as out:
                temp_path = Path(out.name)
                os.chmod(temp_path, 0o600)
                while chunk := await file.read(CHUNK):
                    size += len(chunk)
                    if size > MAX_BYTES:
                        raise HTTPException(413, "File exceeds 512 MiB limit")
                    if not header:
                        header = chunk[:32]
                    h.update(chunk)
                    out.write(chunk)
                out.flush()
                os.fsync(out.fileno())
            media = sniff_media(header)
            if not media or not size:
                raise HTTPException(415, "Unsupported media format")
            media_type, ext = media
            if media_type.startswith("image/"):
                try:
                    with Image.open(temp_path) as img:
                        img.verify()
                except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
                    raise HTTPException(415, "Invalid image") from None
            digest = h.hexdigest()
            asset_id = str(uuid4())
            target = settings.data_dir / "objects" / digest[:2] / (digest + ext)
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with database(settings) as db:
                existing = db.execute("SELECT id FROM assets WHERE sha256=?", (digest,)).fetchone()
                if existing:
                    raise HTTPException(409, f"Duplicate file (asset {existing['id']})")
                if not target.exists():
                    os.replace(temp_path, target)
                    temp_path = None
                db.execute(
                    "INSERT INTO assets(id,sha256,filename,media_type,bytes,created_at) VALUES(?,?,?,?,?,?)",
                    (asset_id, digest, safe_name(file.filename), media_type, size,
                     datetime.now(UTC).isoformat()),
                )
            if media_type.startswith("image/"):
                try:
                    with Image.open(target) as img:
                        img = ImageOps.exif_transpose(img)
                        img.thumbnail((512, 512))
                        preview = settings.data_dir / "previews" / (asset_id + ".jpg")
                        img.convert("RGB").save(preview, "JPEG", quality=82, optimize=True)
                        preview.chmod(0o600)
                except (OSError, ValueError, Image.DecompressionBombError):
                    pass  # Original remains available; no misleading preview is emitted.
            return {"id": asset_id, "sha256": digest, "media_type": media_type, "bytes": size}
        finally:
            await file.close()
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    def find_asset(asset_id: str, include_deleted: bool = False):
        with database(settings) as db:
            row = db.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()
        if not row or (row["deleted_at"] and not include_deleted):
            raise HTTPException(404, "Asset not found")
        return row

    def stream_path(path: Path, media_type: str, request: Request, filename: str | None = None):
        if not path.is_file():
            raise HTTPException(404, "Content unavailable")
        length = path.stat().st_size
        start, end = 0, max(0, length - 1)
        headers = {"Accept-Ranges": "bytes"}
        if filename:
            headers["Content-Disposition"] = "attachment; filename*=UTF-8''" + quote(filename)
        code = 200
        range_value = request.headers.get("range")
        if range_value:
            matched = re.fullmatch(r"bytes=(\d*)-(\d*)", range_value)
            if not matched or not length or (not matched[1] and not matched[2]):
                raise HTTPException(416, "Invalid byte range", headers={"Content-Range": f"bytes */{length}"})
            if matched[1]:
                start = int(matched[1])
                end = min(int(matched[2]), length - 1) if matched[2] else length - 1
            else:
                start = max(0, length - int(matched[2]))
            if start > end or start >= length:
                raise HTTPException(416, "Invalid byte range", headers={"Content-Range": f"bytes */{length}"})
            headers["Content-Range"] = f"bytes {start}-{end}/{length}"
            code = 206
        headers["Content-Length"] = str(end - start + 1)
        def chunks():
            with path.open("rb") as source:
                source.seek(start)
                remaining = end - start + 1
                while remaining:
                    block = source.read(min(CHUNK, remaining))
                    if not block:
                        break
                    remaining -= len(block)
                    yield block
        return StreamingResponse(chunks(), status_code=code, media_type=media_type, headers=headers)

    @app.get("/v1/assets/{asset_id}/original", dependencies=[Depends(authorized)])
    def original(asset_id: str, request: Request):
        row = find_asset(asset_id)
        ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
               "image/gif": ".gif", "video/mp4": ".mp4"}[row["media_type"]]
        path = settings.data_dir / "objects" / row["sha256"][:2] / (row["sha256"] + ext)
        return stream_path(path, row["media_type"], request, row["filename"])

    @app.get("/v1/assets/{asset_id}/thumbnail", dependencies=[Depends(authorized)])
    def thumbnail(asset_id: str, request: Request):
        row = find_asset(asset_id)
        if not row["media_type"].startswith("image/"):
            raise HTTPException(404, "Thumbnail unavailable")
        return stream_path(settings.data_dir / "previews" / (asset_id + ".jpg"), "image/jpeg", request)

    @app.post("/v1/assets/{asset_id}/favorite", dependencies=[Depends(authorized)])
    @app.patch("/v1/assets/{asset_id}/favorite", dependencies=[Depends(authorized)])
    def favorite(asset_id: str, body: FavoriteIn):
        find_asset(asset_id)
        with database(settings) as db:
            db.execute("UPDATE assets SET favorite=? WHERE id=?", (int(body.favorite), asset_id))
        return {"id": asset_id, "favorite": body.favorite}

    @app.delete("/v1/assets/{asset_id}", status_code=204, dependencies=[Depends(authorized)])
    def trash(asset_id: str):
        find_asset(asset_id)
        with database(settings) as db:
            db.execute("UPDATE assets SET deleted_at=? WHERE id=?",
                       (datetime.now(UTC).isoformat(), asset_id))
        return Response(status_code=204)

    @app.post("/v1/assets/{asset_id}/restore", dependencies=[Depends(authorized)])
    def restore(asset_id: str):
        find_asset(asset_id, include_deleted=True)
        with database(settings) as db:
            db.execute("UPDATE assets SET deleted_at=NULL WHERE id=?", (asset_id,))
        return {"id": asset_id, "restored": True}

    @app.get("/v1/albums", dependencies=[Depends(authorized)])
    def albums():
        with database(settings) as db:
            rows = db.execute("""SELECT albums.id, albums.name, albums.created_at,
                 COUNT(CASE WHEN assets.deleted_at IS NULL THEN album_assets.asset_id END) AS count
                 FROM albums LEFT JOIN album_assets ON albums.id=album_assets.album_id
                 LEFT JOIN assets ON assets.id=album_assets.asset_id
                 GROUP BY albums.id ORDER BY albums.created_at DESC""").fetchall()
        return {"items": [dict(r) for r in rows]}

    @app.post("/v1/albums", status_code=201, dependencies=[Depends(authorized)])
    def create_album(body: AlbumIn):
        name = body.name.strip()
        if not name:
            raise HTTPException(422, "Album name cannot be blank")
        album_id = str(uuid4())
        with database(settings) as db:
            db.execute("INSERT INTO albums VALUES(?,?,?)",
                       (album_id, name, datetime.now(UTC).isoformat()))
        return {"id": album_id, "name": name}

    @app.post("/v1/albums/{album_id}/assets/{asset_id}", dependencies=[Depends(authorized)])
    def add_album_asset(album_id: str, asset_id: str):
        find_asset(asset_id)
        with database(settings) as db:
            if not db.execute("SELECT 1 FROM albums WHERE id=?", (album_id,)).fetchone():
                raise HTTPException(404, "Album not found")
            db.execute("INSERT OR IGNORE INTO album_assets VALUES(?,?)", (album_id, asset_id))
        return {"album_id": album_id, "asset_id": asset_id}

    @app.get("/v1/albums/{album_id}/assets", dependencies=[Depends(authorized)])
    def album_assets(album_id: str):
        with database(settings) as db:
            if not db.execute("SELECT 1 FROM albums WHERE id=?", (album_id,)).fetchone():
                raise HTTPException(404, "Album not found")
            rows = db.execute("""SELECT assets.* FROM assets JOIN album_assets ON assets.id=album_assets.asset_id
                WHERE album_assets.album_id=? AND assets.deleted_at IS NULL
                ORDER BY assets.created_at DESC""", (album_id,)).fetchall()
        return {"items": [asset_dict(r) for r in rows], "total": len(rows)}

    return app


# Launch with: uvicorn app.main:app --factory --host 127.0.0.1 --port 8787
def app() -> FastAPI:
    return create_app()
