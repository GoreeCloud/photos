"""Only synthetic data; localhost browser acceptance fixture, never production."""

import io
import os
import tempfile
from pathlib import Path

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from PIL import Image

from app.main import Settings, create_app

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web" / "dist"
DATA = Path(os.environ["PHOTOS_BROWSER_TEST_DIR"]).resolve(strict=True)
if (
    not DATA.name.startswith("photos-browser-accept-")
    or DATA.parent != Path(tempfile.gettempdir()).resolve()
):
    raise RuntimeError(
        "Refusing to run browser fixture outside an isolated temporary folder"
    )
if not (WEB / "index.html").is_file():
    raise RuntimeError("Run npm --prefix web run build before browser acceptance")

app = create_app(Settings(DATA / "library", "synthetic-browser-initial-2026"))
with TestClient(app) as client:
    response = client.post(
        "/v1/session", json={"password": "synthetic-browser-initial-2026"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    image = io.BytesIO()
    Image.new("RGB", (15, 18), (61, 82, 103)).save(image, format="PNG")
    uploaded = client.post(
        "/v1/assets",
        headers={"Authorization": "Bearer " + token},
        files={"file": ("browser-synthetic-only.png", image.getvalue(), "image/png")},
    )
    assert uploaded.status_code == 201, uploaded.text


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse((WEB / "index.html").read_text())


app.mount("/assets", StaticFiles(directory=WEB / "assets"), name="assets")
