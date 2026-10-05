"""Endpoint de tracking (M4) : réutilise la vidéo (M2) et le détecteur (M3).

Le registre en mémoire (`_tracks_registry`) suit le même principe temporaire
que celui de `app/api/videos.py` : remplacé par la vraie persistance en
M12. Le résultat d'un premier calcul est mis en cache par vidéo, car le
pipeline (détection sur de nombreuses frames) est coûteux en CPU.
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.detection import get_detector
from app.api.videos import get_video_entry
from app.tracking.pipeline import run_tracking
from app.tracking.tracker import IoUTracker, TrackPoint
from app.video.engine import FileVideoSource

router = APIRouter(prefix="/videos", tags=["tracking"])

_tracks_registry: dict[str, list[TrackPoint]] = {}


class BoundingBoxResponse(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class TrackPointResponse(BaseModel):
    track_id: int
    timestamp: float
    bbox: BoundingBoxResponse
    confidence: float
    x_pixel: float
    y_pixel: float


def _to_response(track_point: TrackPoint) -> TrackPointResponse:
    return TrackPointResponse(
        track_id=track_point.track_id,
        timestamp=track_point.timestamp,
        bbox=BoundingBoxResponse(**asdict(track_point.bbox)),
        confidence=track_point.confidence,
        x_pixel=track_point.x_pixel,
        y_pixel=track_point.y_pixel,
    )


@router.get("/{video_id}/tracks", response_model=list[TrackPointResponse])
def get_tracks(
    video_id: str,
    confidence: float = 0.5,
    sample_every_n_frames: int = 2,
    force: bool = False,
) -> list[TrackPointResponse]:
    entry = get_video_entry(video_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Vidéo introuvable")

    if not 0.0 <= confidence <= 1.0:
        raise HTTPException(status_code=400, detail="confidence doit être entre 0 et 1")
    if sample_every_n_frames < 1:
        raise HTTPException(status_code=400, detail="sample_every_n_frames doit être >= 1")

    if not force and video_id in _tracks_registry:
        return [_to_response(tp) for tp in _tracks_registry[video_id]]

    source = FileVideoSource(entry.path)
    try:
        track_points = run_tracking(
            source,
            get_detector(),
            IoUTracker(),
            confidence_threshold=confidence,
            sample_every_n_frames=sample_every_n_frames,
        )
    finally:
        source.close()

    _tracks_registry[video_id] = track_points

    return [_to_response(tp) for tp in track_points]
