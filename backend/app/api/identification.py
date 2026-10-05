"""Endpoints d'identification des joueurs (M5).

Résumé des tracks significatifs (vignette, couleur dominante suggérée) et
association manuelle track -> joueur. Réutilise le tracking déjà calculé
pour la vidéo (M4) — ne relance jamais le pipeline vision lui-même.
"""

from __future__ import annotations

from collections import defaultdict

import cv2
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.api.tracking import get_cached_tracks
from app.api.videos import get_video_entry
from app.identification import store
from app.identification.color import bgr_to_hex, dominant_color_bgr, suggest_groups
from app.storage import roster
from app.tracking.tracker import TrackPoint
from app.video.engine import FileVideoSource

router = APIRouter(prefix="/videos", tags=["identification"])


def _representative_point(points: list[TrackPoint]) -> TrackPoint:
    return max(points, key=lambda p: p.confidence)


class TrackSummaryResponse(BaseModel):
    track_id: int
    point_count: int
    first_timestamp: float
    last_timestamp: float
    dominant_color: str
    suggested_group: int
    player_id: str | None
    player_name: str | None
    manually_verified: bool


@router.get("/{video_id}/tracks/summary", response_model=list[TrackSummaryResponse])
def get_tracks_summary(video_id: str, min_points: int = 3) -> list[TrackSummaryResponse]:
    entry = get_video_entry(video_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Vidéo introuvable")

    track_points = get_cached_tracks(video_id)
    if track_points is None:
        raise HTTPException(
            status_code=409,
            detail="Le tracking n'a pas encore été calculé (GET /videos/{id}/tracks d'abord)",
        )

    by_track: dict[int, list[TrackPoint]] = defaultdict(list)
    for point in track_points:
        by_track[point.track_id].append(point)

    significant = {tid: pts for tid, pts in by_track.items() if len(pts) >= min_points}
    representatives = {tid: _representative_point(pts) for tid, pts in significant.items()}

    source = FileVideoSource(entry.path)
    try:
        colors: dict[int, tuple[int, int, int]] = {
            tid: dominant_color_bgr(source.read_frame_at(point.timestamp), point.bbox)
            for tid, point in representatives.items()
        }
    finally:
        source.close()

    track_ids = sorted(significant.keys())
    groups = dict(zip(track_ids, suggest_groups([colors[tid] for tid in track_ids]), strict=True))

    results = []
    for tid in track_ids:
        pts = significant[tid]
        identification = store.get_identification(video_id, tid)
        player = roster.get_player(identification.player_id) if identification else None
        results.append(
            TrackSummaryResponse(
                track_id=tid,
                point_count=len(pts),
                first_timestamp=min(p.timestamp for p in pts),
                last_timestamp=max(p.timestamp for p in pts),
                dominant_color=bgr_to_hex(colors[tid]),
                suggested_group=groups[tid],
                player_id=identification.player_id if identification else None,
                player_name=player.full_name if player else None,
                manually_verified=identification.manually_verified if identification else False,
            )
        )
    return results


@router.get("/{video_id}/tracks/{track_id}/thumbnail")
def get_track_thumbnail(video_id: str, track_id: int) -> Response:
    entry = get_video_entry(video_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Vidéo introuvable")

    track_points = get_cached_tracks(video_id)
    if track_points is None:
        raise HTTPException(status_code=409, detail="Tracking non calculé")

    points = [p for p in track_points if p.track_id == track_id]
    if not points:
        raise HTTPException(status_code=404, detail="Track introuvable")

    point = _representative_point(points)

    source = FileVideoSource(entry.path)
    try:
        frame = source.read_frame_at(point.timestamp)
    finally:
        source.close()

    bbox = point.bbox
    crop = frame[max(0, int(bbox.y1)) : int(bbox.y2), max(0, int(bbox.x1)) : int(bbox.x2)]
    if crop.size == 0:
        raise HTTPException(status_code=500, detail="Échec de génération de la vignette")

    success, buffer = cv2.imencode(".jpg", crop)
    if not success:
        raise HTTPException(status_code=500, detail="Échec d'encodage de la vignette")

    return Response(content=buffer.tobytes(), media_type="image/jpeg")


class IdentifyRequest(BaseModel):
    player_id: str


class IdentificationResponse(BaseModel):
    video_id: str
    track_id: int
    player_id: str
    method: str
    manually_verified: bool


@router.put("/{video_id}/tracks/{track_id}/identification", response_model=IdentificationResponse)
def identify_track(video_id: str, track_id: int, body: IdentifyRequest) -> IdentificationResponse:
    if get_video_entry(video_id) is None:
        raise HTTPException(status_code=404, detail="Vidéo introuvable")
    if roster.get_player(body.player_id) is None:
        raise HTTPException(status_code=404, detail="Joueur introuvable")

    record = store.set_identification(video_id, track_id, body.player_id)
    return IdentificationResponse(
        video_id=record.video_id,
        track_id=record.track_id,
        player_id=record.player_id,
        method=record.method,
        manually_verified=record.manually_verified,
    )


@router.delete("/{video_id}/tracks/{track_id}/identification", status_code=204)
def remove_track_identification(video_id: str, track_id: int) -> None:
    store.remove_identification(video_id, track_id)
