"""SQLite-backed login throttling is shared by app instances and avoids raw IP storage."""
import hashlib
import sqlite3
import time

from fastapi.testclient import TestClient

from app.main import Settings, create_app

PASSWORD = "a-test-password-at-least-12"


def login(client, password):
    return client.post("/v1/session", json={"password": password})


def test_limit_persists_across_app_restart_and_expires(tmp_path):
    settings = Settings(tmp_path / "photos", PASSWORD)
    app_a = create_app(settings)
    with TestClient(app_a) as first:
        for _ in range(5):
            assert login(first, "incorrect").status_code == 401
        assert login(first, PASSWORD).status_code == 429
    with sqlite3.connect(settings.data_dir / "photos.sqlite3") as db:
        digest, count, start = db.execute(
            "SELECT peer_digest, failed_count, window_start FROM auth_failures"
        ).fetchone()
        assert count == 5
        assert len(digest) == 64
        assert digest != hashlib.sha256(b"testclient").hexdigest()
        assert start <= int(time.time())
        assert "testclient" not in digest
        db.execute(
            "UPDATE auth_failures SET window_start=?", (int(time.time()) - 901,)
        )

    with TestClient(create_app(Settings(settings.data_dir, None))) as restarted:
        valid = login(restarted, PASSWORD)
        assert valid.status_code == 200, valid.text
        token = valid.json()["access_token"]
        assert restarted.get(
            "/v1/assets", headers={"Authorization": f"Bearer {token}"}
        ).status_code == 200
        assert login(restarted, "incorrect").status_code == 401

    with sqlite3.connect(settings.data_dir / "photos.sqlite3") as db:
        assert db.execute(
            "SELECT COUNT(*) FROM auth_failures WHERE failed_count=1"
        ).fetchone()[0] == 1


def test_success_resets_failure_counter_without_logging_password(tmp_path):
    settings = Settings(tmp_path / "photos", PASSWORD)
    with TestClient(create_app(settings)) as client:
        assert login(client, "incorrect").status_code == 401
        assert login(client, "incorrect").status_code == 401
        assert login(client, PASSWORD).status_code == 200
        with sqlite3.connect(settings.data_dir / "photos.sqlite3") as db:
            assert db.execute("SELECT count(*) FROM auth_failures").fetchone()[0] == 0
        # New window after a correct password.
        for _ in range(5):
            assert login(client, "incorrect").status_code == 401
        assert login(client, PASSWORD).status_code == 429


def test_throttle_is_private_to_each_library(tmp_path):
    alpha = Settings(tmp_path / "alpha", PASSWORD)
    beta = Settings(tmp_path / "beta", PASSWORD)
    with TestClient(create_app(alpha)) as a, TestClient(create_app(beta)) as b:
        for _ in range(5):
            assert login(a, "incorrect").status_code == 401
        assert login(a, PASSWORD).status_code == 429
        assert login(b, PASSWORD).status_code == 200
    with sqlite3.connect(alpha.data_dir / "photos.sqlite3") as db:
        secret_a = db.execute(
            "SELECT value FROM configuration WHERE key='rate_secret'"
        ).fetchone()[0]
    with sqlite3.connect(beta.data_dir / "photos.sqlite3") as db:
        secret_b = db.execute(
            "SELECT value FROM configuration WHERE key='rate_secret'"
        ).fetchone()[0]
    assert secret_a != secret_b
