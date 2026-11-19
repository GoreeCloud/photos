"""Album pagination and lifecycle must never delete photo originals."""
import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import Settings, create_app


def payload(color):
    stream = io.BytesIO()
    Image.new("RGB", (8, 8), color).save(stream, "PNG")
    return stream.getvalue()


def test_album_lifecycle_and_paging(tmp_path):
    with TestClient(create_app(Settings(tmp_path / "photos", "long-private-album-test-password"))) as client:
        auth = client.post(
            "/v1/session", json={"password": "long-private-album-test-password"}
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {auth}"}
        assert client.get("/v1/albums").status_code == 401

        album = client.post("/v1/albums", headers=headers, json={"name": "Travel"}).json()["id"]
        ids = []
        for name, color in [
            ("family%trip.png", (10, 20, 30)),
            ("nature.png", (50, 60, 70)),
            ("family_trip.png", (90, 100, 110)),
        ]:
            response = client.post(
                "/v1/assets", headers=headers,
                files={"file": (name, payload(color), "image/png")}
            )
            assert response.status_code == 201, response.text
            ids.append(response.json()["id"])
            assert client.post(f"/v1/albums/{album}/assets/{ids[-1]}", headers=headers).status_code == 200

        address = f"/v1/albums/{album}/assets"
        unpaged = client.get(address, headers=headers).json()
        assert unpaged["total"] == 3
        assert len(unpaged["items"]) == 3
        page1 = client.get(address + "?limit=2&offset=0", headers=headers).json()
        page2 = client.get(address + "?limit=2&offset=2", headers=headers).json()
        assert page1["total"] == page2["total"] == 3
        assert len(page1["items"]) == 2
        assert len(page2["items"]) == 1
        assert {x["id"] for x in page1["items"] + page2["items"]} == set(ids)

        escaped = client.get(address + "?search=%25&limit=10", headers=headers).json()
        assert escaped["total"] == 1
        assert escaped["items"][0]["filename"] == "family%trip.png"
        escaped_underscore = client.get(address + "?search=_", headers=headers).json()
        assert escaped_underscore["total"] == 1
        assert escaped_underscore["items"][0]["filename"] == "family_trip.png"

        assert client.get(address + "?limit=101", headers=headers).status_code == 422
        assert client.get(address + "?offset=1", headers=headers).status_code == 422
        assert client.patch(f"/v1/albums/{album}", headers=headers,
                            json={"name": "  Journeys  "}).json()["name"] == "Journeys"
        assert client.patch(f"/v1/albums/{album}", headers=headers,
                            json={"name": "  "}).status_code == 422
        assert client.delete(f"/v1/albums/{album}/assets/{ids[0]}", headers=headers).status_code == 204
        assert client.get(address, headers=headers).json()["total"] == 2
        assert client.delete(f"/v1/albums/{album}/assets/{ids[0]}", headers=headers).status_code == 404
        assert client.get(f"/v1/assets/{ids[0]}/original", headers=headers).status_code == 200

        assert client.delete(f"/v1/albums/{album}", headers=headers).status_code == 204
        assert client.get(address, headers=headers).status_code == 404
        assert client.delete(f"/v1/albums/{album}", headers=headers).status_code == 404
        for asset_id in ids:
            assert client.get(f"/v1/assets/{asset_id}/original", headers=headers).status_code == 200
        assert client.get("/v1/assets", headers=headers).json()["total"] == 3
