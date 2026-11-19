"""Private aggregate library stats and byte-range behavior for original files."""
import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import Settings, create_app


def image_bytes():
    stream = io.BytesIO()
    Image.new("RGB", (11, 9), (10, 20, 30)).save(stream, format="PNG")
    return stream.getvalue()


def test_private_stats_and_ranges(tmp_path):
    with TestClient(create_app(Settings(tmp_path / "photos", "very-long-test-password"))) as client:
        path = "/v1/library/stats"
        assert client.get(path).status_code == 401
        token = client.post("/v1/session", json={"password": "very-long-test-password"}).json()[
            "access_token"
        ]
        headers = {"Authorization": "Bearer " + token}
        empty = client.get(path, headers=headers)
        assert empty.status_code == 200
        assert empty.json() == {
            "total": 0, "active": 0, "trashed": 0, "favorites": 0,
            "images": 0, "videos": 0, "original_bytes": 0, "albums": 0,
            "quota_bytes": None, "remaining_bytes": None,
        }
        assert client.post("/v1/albums", json={"name": "Demo"}, headers=headers).status_code == 201
        png = image_bytes()
        original = client.post(
            "/v1/assets", headers=headers, files={"file": ("family.png", png, "image/png")}
        )
        assert original.status_code == 201
        image_id = original.json()["id"]
        mp4 = b"\0\0\0\x18ftypisom" + b"\0" * 32
        video = client.post(
            "/v1/assets", headers=headers, files={"file": ("clip.mp4", mp4, "video/mp4")}
        )
        assert video.status_code == 201
        video_id = video.json()["id"]
        assert client.patch(
            f"/v1/assets/{image_id}/favorite", headers=headers, json={"favorite": True}
        ).status_code == 200
        assert client.delete(f"/v1/assets/{video_id}", headers=headers).status_code == 204
        stat = client.get(path, headers=headers).json()
        assert stat == {
            "total": 2, "active": 1, "trashed": 1, "favorites": 1,
            "images": 1, "videos": 1, "original_bytes": len(png) + len(mp4), "albums": 1,
            "quota_bytes": None, "remaining_bytes": None,
        }
        assert "filename" not in stat and "sha256" not in stat
        url = f"/v1/assets/{image_id}/original"
        full = client.get(url, headers=headers)
        assert full.content == png
        assert full.headers["accept-ranges"] == "bytes"
        assert full.headers["cache-control"] == "private, no-store"
        partial = client.get(url, headers={**headers, "Range": "bytes=0-9"})
        assert partial.status_code == 206 and partial.content == png[:10]
        assert partial.headers["content-range"] == f"bytes 0-9/{len(png)}"
        suffix = client.get(url, headers={**headers, "Range": "bytes=-5"})
        assert suffix.status_code == 206 and suffix.content == png[-5:]
        invalid = client.get(url, headers={**headers, "Range": "bytes=999999-"})
        assert invalid.status_code == 416
        assert invalid.headers["content-range"] == f"bytes */{len(png)}"
        assert client.get(url, headers={**headers, "Range": "bytes=0-2,4-8"}).status_code == 416
        assert client.get(f"/v1/assets/{video_id}/original", headers=headers).status_code == 404
