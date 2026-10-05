"""Endpoints de gestion vidéo (M2).

Le registre en mémoire (`_registry`) est une solution temporaire : il sera
remplacé par la persistance réelle en base (M12). Les fichiers restent sur
disque dans `STORAGE_DIR` indépendamment du registre.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import cv2
from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from app.video.engine import FileVideoSource, VideoMetadata

router = APIRouter(prefix="/videos", tags=["videos"])

STORAGE_DIR = Path(__file__).resolve().parents[2] / "data" / "videos"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".mp4"}


class _VideoEntry(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    filename: str
    path: Path
    metadata: VideoMetadata


_registry: dict[str, _VideoEntry] = {}


class VideoMetadataResponse(BaseModel):
    id: str
    filename: str
    duration_seconds: float
    fps: float
    width: int
    height: int
    frame_count: int


def _to_response(video_id: str, entry: _VideoEntry) -> VideoMetadataResponse:
    return VideoMetadataResponse(
        id=video_id,
        filename=entry.filename,
        duration_seconds=entry.metadata.duration_seconds,
        fps=entry.metadata.fps,
        width=entry.metadata.width,
        height=entry.metadata.height,
        frame_count=entry.metadata.frame_count,
    )


@router.post("", response_model=VideoMetadataResponse, status_code=201)
async def upload_video(file: UploadFile) -> VideoMetadataResponse:
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté : {extension or 'inconnu'} (attendu : .mp4)",
        )

    video_id = uuid.uuid4().hex
    destination = STORAGE_DIR / f"{video_id}{extension}"
    destination.write_bytes(await file.read())

    try:
        source = FileVideoSource(destination)
        try:
            metadata = source.get_metadata()
        finally:
            source.close()
    except ValueError as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if metadata.frame_count <= 0 or metadata.fps <= 0:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Vidéo invalide ou illisible")

    entry = _VideoEntry(filename=destination.name, path=destination, metadata=metadata)
    _registry[video_id] = entry

    return _to_response(video_id, entry)


@router.get("/{video_id}", response_model=VideoMetadataResponse)
def get_video(video_id: str) -> VideoMetadataResponse:
    entry = _registry.get(video_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Vidéo introuvable")
    return _to_response(video_id, entry)


@router.get("/{video_id}/frame")
def get_frame(video_id: str, t: float = 0.0) -> Response:
    entry = _registry.get(video_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Vidéo introuvable")

    source = FileVideoSource(entry.path)
    try:
        frame = source.read_frame_at(t)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        source.close()

    success, buffer = cv2.imencode(".jpg", frame)
    if not success:
        raise HTTPException(status_code=500, detail="Échec d'encodage de la frame")

    return Response(content=buffer.tobytes(), media_type="image/jpeg")
