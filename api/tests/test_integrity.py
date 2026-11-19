"""Upload integrity tests: concurrent identical uploads and decompression-bomb limits."""
import io
import struct
import threading
import warnings
import zlib
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient
from PIL import Image

from app.main import Settings, create_app


def small_png():
    buf = io.BytesIO()
    Image.new("RGB", (16, 16), (20, 30, 40)).save(buf, "PNG")
    return buf.getvalue()


def auth(client):
    result = client.post("/v1/session", json={"password": "a-strong-test-password"})
    assert result.status_code == 200
    return {"Authorization": "Bearer " + result.json()["access_token"]}


def test_concurrent_identical_uploads_are_idempotently_rejected(tmp_path):
    app = create_app(Settings(tmp_path / "lib", "a-strong-test-password"))
    with TestClient(app) as client:
        headers = auth(client)
    barrier = threading.Barrier(4)
    payload = small_png()

    def upload():
        with TestClient(app) as client:
            barrier.wait(timeout=5)
            return client.post(
                "/v1/assets", headers=headers,
                files={"file": ("test.png", payload, "image/png")},
            ).status_code

    with ThreadPoolExecutor(max_workers=4) as pool:
        codes = sorted(pool.map(lambda _: upload(), range(4)))
    assert codes == [201, 409, 409, 409]
    with TestClient(app) as client:
        records = client.get("/v1/assets", headers=headers)
        assert records.status_code == 200
        assert records.json()["total"] == 1


def test_pixel_limit_blocks_large_dimensions_without_decoding(tmp_path):
    payload = bytearray(small_png())
    # Rewrite only the PNG IHDR width/height, maintaining its CRC.
    payload[16:24] = struct.pack(">II", 10_000, 6_000)
    payload[29:33] = struct.pack(">I", zlib.crc32(payload[12:29]) & 0xFFFFFFFF)
    data_dir = tmp_path / "lib"
    with TestClient(create_app(Settings(data_dir, "a-strong-test-password"))) as client:
        headers = auth(client)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", Image.DecompressionBombWarning)
            response = client.post(
                "/v1/assets", headers=headers,
                files={"file": ("oversized.png", bytes(payload), "image/png")},
            )
        assert response.status_code == 413, response.text
        assert client.get("/v1/assets", headers=headers).json()["total"] == 0
    assert not list((data_dir / "objects").rglob("*.png"))
    assert not list((data_dir / "tmp").iterdir())
