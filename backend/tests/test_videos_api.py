from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import FIXTURE_FPS, FIXTURE_FRAME_COUNT, FIXTURE_HEIGHT, FIXTURE_WIDTH

client = TestClient(app)


def test_upload_video_returns_metadata(synthetic_video_path: Path) -> None:
    with synthetic_video_path.open("rb") as f:
        response = client.post("/videos", files={"file": ("match.mp4", f, "video/mp4")})

    assert response.status_code == 201
    body = response.json()
    assert body["filename"].endswith(".mp4")
    assert body["fps"] == FIXTURE_FPS
    assert body["frame_count"] == FIXTURE_FRAME_COUNT
    assert body["width"] == FIXTURE_WIDTH
    assert body["height"] == FIXTURE_HEIGHT


def test_upload_rejects_non_mp4(tmp_path: Path) -> None:
    text_file = tmp_path / "notes.txt"
    text_file.write_text("pas une vidéo")

    with text_file.open("rb") as f:
        response = client.post("/videos", files={"file": ("notes.txt", f, "text/plain")})

    assert response.status_code == 400


def test_get_video_metadata_after_upload(synthetic_video_path: Path) -> None:
    with synthetic_video_path.open("rb") as f:
        upload_response = client.post("/videos", files={"file": ("match.mp4", f, "video/mp4")})
    video_id = upload_response.json()["id"]

    response = client.get(f"/videos/{video_id}")

    assert response.status_code == 200
    assert response.json()["id"] == video_id


def test_get_video_metadata_unknown_id_returns_404() -> None:
    response = client.get("/videos/does-not-exist")

    assert response.status_code == 404


def test_get_frame_returns_jpeg(synthetic_video_path: Path) -> None:
    with synthetic_video_path.open("rb") as f:
        upload_response = client.post("/videos", files={"file": ("match.mp4", f, "video/mp4")})
    video_id = upload_response.json()["id"]

    response = client.get(f"/videos/{video_id}/frame", params={"t": 0.5})

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert len(response.content) > 0
