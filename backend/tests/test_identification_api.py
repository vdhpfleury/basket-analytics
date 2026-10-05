"""Tests de l'API d'identification (M5). Les tracks sont injectés
directement dans le registre de `app/api/tracking.py` (même principe que
les autres registres temporaires) pour tester cette couche indépendamment
de la détection/du tracking eux-mêmes, déjà testés en M3/M4.
"""

from pathlib import Path

from fastapi.testclient import TestClient

from app.api import tracking as tracking_module
from app.detection.detector import BoundingBox
from app.main import app
from app.tracking.tracker import TrackPoint

client = TestClient(app)


def _upload(synthetic_video_path: Path) -> str:
    with synthetic_video_path.open("rb") as f:
        response = client.post("/videos", files={"file": ("match.mp4", f, "video/mp4")})
    return response.json()["id"]


def _seed_tracks(video_id: str) -> None:
    tracking_module._tracks_registry[video_id] = [
        TrackPoint(1, 0.0, BoundingBox(10, 10, 30, 70), 0.9, 20, 70),
        TrackPoint(1, 0.1, BoundingBox(12, 10, 32, 70), 0.9, 22, 70),
        TrackPoint(1, 0.2, BoundingBox(14, 10, 34, 70), 0.9, 24, 70),
        # Track 2 : un seul point -> pas "significatif" avec min_points=3 (défaut).
        TrackPoint(2, 0.0, BoundingBox(10, 10, 12, 12), 0.9, 11, 12),
    ]


def test_summary_requires_tracking_computed_first(synthetic_video_path: Path) -> None:
    video_id = _upload(synthetic_video_path)

    response = client.get(f"/videos/{video_id}/tracks/summary")

    assert response.status_code == 409


def test_summary_unknown_video_returns_404() -> None:
    response = client.get("/videos/does-not-exist/tracks/summary")

    assert response.status_code == 404


def test_summary_lists_only_significant_tracks_unidentified_by_default(
    synthetic_video_path: Path,
) -> None:
    video_id = _upload(synthetic_video_path)
    _seed_tracks(video_id)

    response = client.get(f"/videos/{video_id}/tracks/summary")

    assert response.status_code == 200
    body = response.json()
    assert [t["track_id"] for t in body] == [1]
    assert body[0]["player_id"] is None
    assert body[0]["player_name"] is None
    assert body[0]["manually_verified"] is False


def test_identify_track_and_see_it_in_summary(synthetic_video_path: Path) -> None:
    video_id = _upload(synthetic_video_path)
    _seed_tracks(video_id)
    team = client.post("/teams", json={"name": "Équipe Identif 1"}).json()
    player = client.post(
        f"/teams/{team['id']}/players", json={"full_name": "Joueur Un", "jersey_number": 9}
    ).json()

    put_response = client.put(
        f"/videos/{video_id}/tracks/1/identification", json={"player_id": player["id"]}
    )
    assert put_response.status_code == 200
    assert put_response.json() == {
        "video_id": video_id,
        "track_id": 1,
        "player_id": player["id"],
        "method": "manual",
        "manually_verified": True,
    }

    summary = client.get(f"/videos/{video_id}/tracks/summary").json()
    assert summary[0]["player_id"] == player["id"]
    assert summary[0]["player_name"] == "Joueur Un"
    assert summary[0]["manually_verified"] is True


def test_identify_with_unknown_player_returns_404(synthetic_video_path: Path) -> None:
    video_id = _upload(synthetic_video_path)
    _seed_tracks(video_id)

    response = client.put(
        f"/videos/{video_id}/tracks/1/identification", json={"player_id": "does-not-exist"}
    )

    assert response.status_code == 404


def test_remove_identification_reverts_to_unidentified(synthetic_video_path: Path) -> None:
    video_id = _upload(synthetic_video_path)
    _seed_tracks(video_id)
    team = client.post("/teams", json={"name": "Équipe Identif 2"}).json()
    player = client.post(f"/teams/{team['id']}/players", json={"full_name": "Joueur Deux"}).json()
    client.put(f"/videos/{video_id}/tracks/1/identification", json={"player_id": player["id"]})

    delete_response = client.delete(f"/videos/{video_id}/tracks/1/identification")
    assert delete_response.status_code == 204

    summary = client.get(f"/videos/{video_id}/tracks/summary").json()
    assert summary[0]["player_id"] is None


def test_thumbnail_success(synthetic_video_path: Path) -> None:
    video_id = _upload(synthetic_video_path)
    _seed_tracks(video_id)

    response = client.get(f"/videos/{video_id}/tracks/1/thumbnail")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert len(response.content) > 0


def test_thumbnail_unknown_track_returns_404(synthetic_video_path: Path) -> None:
    video_id = _upload(synthetic_video_path)
    _seed_tracks(video_id)

    response = client.get(f"/videos/{video_id}/tracks/999/thumbnail")

    assert response.status_code == 404
