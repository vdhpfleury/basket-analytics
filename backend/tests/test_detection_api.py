from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _upload(synthetic_video_path: Path) -> str:
    with synthetic_video_path.open("rb") as f:
        response = client.post("/videos", files={"file": ("match.mp4", f, "video/mp4")})
    return response.json()["id"]


def test_detect_on_blank_video_returns_empty_list(synthetic_video_path: Path) -> None:
    video_id = _upload(synthetic_video_path)

    response = client.get(f"/videos/{video_id}/detections", params={"t": 0.5})

    assert response.status_code == 200
    assert response.json() == []


def test_detect_unknown_video_returns_404() -> None:
    response = client.get("/videos/does-not-exist/detections", params={"t": 0.0})

    assert response.status_code == 404


def test_detect_rejects_invalid_confidence(synthetic_video_path: Path) -> None:
    video_id = _upload(synthetic_video_path)

    response = client.get(
        f"/videos/{video_id}/detections", params={"t": 0.5, "confidence": 2.0}
    )

    assert response.status_code == 400
