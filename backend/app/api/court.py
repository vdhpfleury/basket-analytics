"""Endpoints de calibration terrain (M6).

Réutilise la vidéo (M2) et le tracking déjà calculé (M4). La calibration
est stockée en mémoire par vidéo (même principe temporaire que les autres
registres, remplacé par la vraie persistance en M12).
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.tracking import get_cached_tracks
from app.api.videos import get_video_entry
from app.court import landmarks
from app.court.calibration import (
    CalibrationError,
    PointCorrespondence,
    compute_homography,
    project_pixel_to_court,
    reprojection_errors,
)

router = APIRouter(tags=["court"])


@dataclass
class _StoredCalibration:
    homography: object  # np.ndarray — typé `object` pour éviter d'importer numpy ici
    correspondences: list[PointCorrespondence]


_calibrations: dict[str, _StoredCalibration] = {}


def get_calibration(video_id: str) -> _StoredCalibration | None:
    """Accès pour les autres modules (M7/M8) — None si pas encore calibré."""
    return _calibrations.get(video_id)


class LandmarkResponse(BaseModel):
    id: str
    label: str
    x_meters: float
    y_meters: float


@router.get("/court/landmarks", response_model=list[LandmarkResponse])
def get_landmarks() -> list[LandmarkResponse]:
    return [
        LandmarkResponse(id=l.id, label=l.label, x_meters=l.x_meters, y_meters=l.y_meters)
        for l in landmarks.LANDMARKS
    ]


class PointInput(BaseModel):
    pixel_x: float
    pixel_y: float
    landmark_id: str | None = None
    court_x: float | None = None
    court_y: float | None = None


class CalibrationRequest(BaseModel):
    points: list[PointInput]


class CalibrationResponse(BaseModel):
    video_id: str
    point_count: int
    mean_reprojection_error_m: float
    max_reprojection_error_m: float


def _resolve_point(point: PointInput) -> PointCorrespondence:
    if point.landmark_id is not None:
        landmark = landmarks.get_landmark(point.landmark_id)
        if landmark is None:
            raise HTTPException(status_code=400, detail=f"Repère inconnu : {point.landmark_id}")
        return PointCorrespondence(
            pixel_x=point.pixel_x,
            pixel_y=point.pixel_y,
            court_x=landmark.x_meters,
            court_y=landmark.y_meters,
        )
    if point.court_x is not None and point.court_y is not None:
        return PointCorrespondence(
            pixel_x=point.pixel_x,
            pixel_y=point.pixel_y,
            court_x=point.court_x,
            court_y=point.court_y,
        )
    raise HTTPException(
        status_code=400, detail="Chaque point doit avoir soit landmark_id, soit court_x et court_y"
    )


def _to_calibration_response(video_id: str, calibration: _StoredCalibration) -> CalibrationResponse:
    errors = reprojection_errors(calibration.homography, calibration.correspondences)
    return CalibrationResponse(
        video_id=video_id,
        point_count=len(calibration.correspondences),
        mean_reprojection_error_m=sum(errors) / len(errors),
        max_reprojection_error_m=max(errors),
    )


@router.post("/videos/{video_id}/court/calibration", response_model=CalibrationResponse)
def set_calibration(video_id: str, body: CalibrationRequest) -> CalibrationResponse:
    if get_video_entry(video_id) is None:
        raise HTTPException(status_code=404, detail="Vidéo introuvable")

    correspondences = [_resolve_point(p) for p in body.points]

    try:
        homography = compute_homography(correspondences)
    except CalibrationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    calibration = _StoredCalibration(homography=homography, correspondences=correspondences)
    _calibrations[video_id] = calibration

    return _to_calibration_response(video_id, calibration)


@router.get("/videos/{video_id}/court/calibration", response_model=CalibrationResponse)
def get_calibration_summary(video_id: str) -> CalibrationResponse:
    calibration = _calibrations.get(video_id)
    if calibration is None:
        raise HTTPException(status_code=404, detail="Pas de calibration pour cette vidéo")
    return _to_calibration_response(video_id, calibration)


class ProjectedTrackPointResponse(BaseModel):
    track_id: int
    timestamp: float
    court_x: float
    court_y: float


@router.get("/videos/{video_id}/court/tracks", response_model=list[ProjectedTrackPointResponse])
def get_projected_tracks(video_id: str) -> list[ProjectedTrackPointResponse]:
    calibration = _calibrations.get(video_id)
    if calibration is None:
        raise HTTPException(status_code=404, detail="Pas de calibration pour cette vidéo")

    track_points = get_cached_tracks(video_id)
    if track_points is None:
        raise HTTPException(status_code=409, detail="Le tracking n'a pas encore été calculé")

    results = []
    for point in track_points:
        court_x, court_y = project_pixel_to_court(calibration.homography, point.x_pixel, point.y_pixel)
        results.append(
            ProjectedTrackPointResponse(
                track_id=point.track_id, timestamp=point.timestamp, court_x=court_x, court_y=court_y
            )
        )
    return results
