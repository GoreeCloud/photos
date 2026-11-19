"""Restoring a verified archive must never revive still-valid bearer tokens."""
import sqlite3

from fastapi.testclient import TestClient
from test_backup import seed_library

from app.backup import backup, restore, verify, verify_library
from app.main import Settings, create_app

PASSWORD = "a-long-private-test-password"


def test_restoring_backup_revokes_all_previous_sessions_and_failures(tmp_path):
    root = tmp_path / "active-library"
    asset_id, original = seed_library(root)
    with TestClient(create_app(Settings(root, None))) as client:
        old = client.post("/v1/session", json={"password": PASSWORD}).json()["access_token"]
        other = client.post("/v1/session", json={"password": PASSWORD}).json()["access_token"]
        assert client.post("/v1/session", json={"password": "incorrect"}).status_code == 401

    with sqlite3.connect(root / "photos.sqlite3") as db:
        assert db.execute("SELECT count(*) FROM sessions").fetchone()[0] >= 2
        assert db.execute("SELECT count(*) FROM auth_failures").fetchone()[0] == 1

    archive = tmp_path / "snapshot.tar"
    backup(root, archive)
    assert verify(archive)["verified"] is True
    recovered = tmp_path / "recovered"
    restore(archive, recovered)
    assert verify_library(recovered)["verified"] is True

    with sqlite3.connect(recovered / "photos.sqlite3") as db:
        assert db.execute("SELECT count(*) FROM sessions").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM auth_failures").fetchone()[0] == 0
    with TestClient(create_app(Settings(recovered, None))) as client:
        for token in (old, other):
            unauthorized = client.get(
                "/v1/assets", headers={"Authorization": "Bearer " + token}
            )
            assert unauthorized.status_code == 401
        fresh = client.post("/v1/session", json={"password": PASSWORD})
        assert fresh.status_code == 200
        auth = {"Authorization": "Bearer " + fresh.json()["access_token"]}
        assert client.get(f"/v1/assets/{asset_id}/original", headers=auth).content == original
        assert client.get("/v1/albums", headers=auth).json()["items"][0]["name"] == "Vacation"
