"""Endpoint de détection (M3) : réutilise une vidéo déjà uploadée (M2)."""

from __future__ import annotations

from dataclasses import asdict
from functools import lru_cache

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.videos import get_video_entry
from app.detection.yolo_detector import YOLOPersonDetector
from app.video.engine import FileVideoSource

router = APIRouter(prefix="/videos", tags=["detection"])


@lru_cache(maxsize=1)
def get_detector() -> YOLOPersonDetector:
    # Chargé une seule fois : l'instanciation du modèle a un coût (~1s) qu'on
    # ne veut pas payer à chaque requête.
    return YOLOPersonDetector()


class BoundingBoxResponse(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class DetectionResponse(BaseModel):
    bbox: BoundingBoxResponse
    confidence: float
    label: str


@router.get("/{video_id}/detections", response_model=list[DetectionResponse])
def detect_frame(video_id: str, t: float = 0.0, confidence: float = 0.5) -> list[DetectionResponse]:
    entry = get_video_entry(video_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Vidéo introuvable")

    if not 0.0 <= confidence <= 1.0:
        raise HTTPException(status_code=400, detail="confidence doit être entre 0 et 1")

    source = FileVideoSource(entry.path)
    try:
        frame = source.read_frame_at(t)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        source.close()

    detections = get_detector().detect(frame, confidence_threshold=confidence)

    return [
        DetectionResponse(bbox=BoundingBoxResponse(**asdict(d.bbox)), confidence=d.confidence, label=d.label)
        for d in detections
    ]
