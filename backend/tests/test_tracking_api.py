from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _upload(synthetic_video_path: Path) -> str:
    with synthetic_video_path.open("rb") as f:
        response = client.post("/videos", files={"file": ("match.mp4", f, "video/mp4")})
    return response.json()["id"]


def test_get_tracks_on_blank_video_returns_empty_list(synthetic_video_path: Path) -> None:
    video_id = _upload(synthetic_video_path)

    response = client.get(f"/videos/{video_id}/tracks")

    assert response.status_code == 200
    assert response.json() == []


def test_get_tracks_unknown_video_returns_404() -> None:
    response = client.get("/videos/does-not-exist/tracks")

    assert response.status_code == 404


def test_get_tracks_rejects_invalid_sample_rate(synthetic_video_path: Path) -> None:
    video_id = _upload(synthetic_video_path)

    response = client.get(f"/videos/{video_id}/tracks", params={"sample_every_n_frames": 0})

    assert response.status_code == 400


def test_get_tracks_is_cached_between_calls(synthetic_video_path: Path) -> None:
    video_id = _upload(synthetic_video_path)

    first = client.get(f"/videos/{video_id}/tracks")
    second = client.get(f"/videos/{video_id}/tracks")

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
