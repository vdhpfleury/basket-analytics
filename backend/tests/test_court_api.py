from pathlib import Path

from fastapi.testclient import TestClient

from app.api import tracking as tracking_module
from app.detection.detector import BoundingBox
from app.main import app
from app.tracking.tracker import TrackPoint

client = TestClient(app)

_FOUR_CORNERS_PAYLOAD = {
    "points": [
        {"pixel_x": 40, "pixel_y": 340, "landmark_id": "corner_bl"},
        {"pixel_x": 600, "pixel_y": 340, "landmark_id": "corner_br"},
        {"pixel_x": 600, "pixel_y": 40, "landmark_id": "corner_tr"},
        {"pixel_x": 40, "pixel_y": 40, "landmark_id": "corner_tl"},
    ]
}


def _upload(synthetic_video_path: Path) -> str:
    with synthetic_video_path.open("rb") as f:
        response = client.post("/videos", files={"file": ("match.mp4", f, "video/mp4")})
    return response.json()["id"]


def test_get_landmarks_returns_known_catalog() -> None:
    response = client.get("/court/landmarks")

    assert response.status_code == 200
    ids = [landmark["id"] for landmark in response.json()]
    assert "corner_bl" in ids
    assert "center" in ids


def test_set_calibration_success(synthetic_video_path: Path) -> None:
    video_id = _upload(synthetic_video_path)

    response = client.post(f"/videos/{video_id}/court/calibration", json=_FOUR_CORNERS_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["point_count"] == 4
    assert body["mean_reprojection_error_m"] < 1e-6


def test_set_calibration_unknown_video_returns_404() -> None:
    response = client.post("/videos/does-not-exist/court/calibration", json=_FOUR_CORNERS_PAYLOAD)

    assert response.status_code == 404


def test_set_calibration_insufficient_points_returns_400(synthetic_video_path: Path) -> None:
    video_id = _upload(synthetic_video_path)
    payload = {"points": _FOUR_CORNERS_PAYLOAD["points"][:3]}

    response = client.post(f"/videos/{video_id}/court/calibration", json=payload)

    assert response.status_code == 400


def test_set_calibration_unknown_landmark_returns_400(synthetic_video_path: Path) -> None:
    video_id = _upload(synthetic_video_path)
    payload = {
        "points": [
            {"pixel_x": 1, "pixel_y": 1, "landmark_id": "does-not-exist"},
            {"pixel_x": 2, "pixel_y": 2, "landmark_id": "corner_br"},
            {"pixel_x": 3, "pixel_y": 3, "landmark_id": "corner_tr"},
            {"pixel_x": 4, "pixel_y": 4, "landmark_id": "corner_tl"},
        ]
    }

    response = client.post(f"/videos/{video_id}/court/calibration", json=payload)

    assert response.status_code == 400


def test_set_calibration_with_explicit_court_coordinates(synthetic_video_path: Path) -> None:
    video_id = _upload(synthetic_video_path)
    payload = {
        "points": [
            {"pixel_x": 40, "pixel_y": 340, "court_x": 0.0, "court_y": 0.0},
            {"pixel_x": 600, "pixel_y": 340, "court_x": 28.0, "court_y": 0.0},
            {"pixel_x": 600, "pixel_y": 40, "court_x": 28.0, "court_y": 15.0},
            {"pixel_x": 40, "pixel_y": 40, "court_x": 0.0, "court_y": 15.0},
        ]
    }

    response = client.post(f"/videos/{video_id}/court/calibration", json=payload)

    assert response.status_code == 200


def test_get_calibration_before_set_returns_404(synthetic_video_path: Path) -> None:
    video_id = _upload(synthetic_video_path)

    response = client.get(f"/videos/{video_id}/court/calibration")

    assert response.status_code == 404


def test_get_calibration_after_set(synthetic_video_path: Path) -> None:
    video_id = _upload(synthetic_video_path)
    client.post(f"/videos/{video_id}/court/calibration", json=_FOUR_CORNERS_PAYLOAD)

    response = client.get(f"/videos/{video_id}/court/calibration")

    assert response.status_code == 200
    assert response.json()["point_count"] == 4


def test_projected_tracks_without_calibration_returns_404(synthetic_video_path: Path) -> None:
    video_id = _upload(synthetic_video_path)

    response = client.get(f"/videos/{video_id}/court/tracks")

    assert response.status_code == 404


def test_projected_tracks_without_tracking_returns_409(synthetic_video_path: Path) -> None:
    video_id = _upload(synthetic_video_path)
    client.post(f"/videos/{video_id}/court/calibration", json=_FOUR_CORNERS_PAYLOAD)

    response = client.get(f"/videos/{video_id}/court/tracks")

    assert response.status_code == 409


def test_projected_tracks_success(synthetic_video_path: Path) -> None:
    video_id = _upload(synthetic_video_path)
    client.post(f"/videos/{video_id}/court/calibration", json=_FOUR_CORNERS_PAYLOAD)
    tracking_module._tracks_registry[video_id] = [
        TrackPoint(1, 0.0, BoundingBox(300, 300, 340, 380), 0.9, 320, 380),
    ]

    response = client.get(f"/videos/{video_id}/court/tracks")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["track_id"] == 1
    # Le point projeté doit rester dans (ou proche de) les limites du terrain (28x15m).
    assert -2.0 <= body[0]["court_x"] <= 30.0
    assert -2.0 <= body[0]["court_y"] <= 17.0
