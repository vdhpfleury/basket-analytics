"""Video Engine : lecture de vidéo et extraction de métadonnées/frames.

`VideoSource` est l'interface commune. Pour le MVP, seule `FileVideoSource`
(lecture d'un fichier) est implémentée — un flux live (webcam/RTSP)
implémenterait la même interface plus tard (M16), sans changer le code en
aval (détection, tracking, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True)
class VideoMetadata:
    duration_seconds: float
    fps: float
    width: int
    height: int
    frame_count: int


class VideoSource(ABC):
    @abstractmethod
    def get_metadata(self) -> VideoMetadata: ...

    @abstractmethod
    def read_frame_at(self, timestamp_seconds: float) -> np.ndarray:
        """Retourne la frame la plus proche de `timestamp_seconds`.

        Lève `ValueError` si aucune frame ne peut être lue à cette position
        (timestamp hors de la vidéo, flux corrompu...).
        """

    @abstractmethod
    def close(self) -> None: ...


class FileVideoSource(VideoSource):
    def __init__(self, path: Path) -> None:
        self._path = path
        self._capture = cv2.VideoCapture(str(path))
        if not self._capture.isOpened():
            raise ValueError(f"Impossible d'ouvrir la vidéo : {path}")

    def get_metadata(self) -> VideoMetadata:
        fps = self._capture.get(cv2.CAP_PROP_FPS)
        frame_count = int(self._capture.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0.0
        return VideoMetadata(
            duration_seconds=duration,
            fps=fps,
            width=width,
            height=height,
            frame_count=frame_count,
        )

    def read_frame_at(self, timestamp_seconds: float) -> np.ndarray:
        self._capture.set(cv2.CAP_PROP_POS_MSEC, max(timestamp_seconds, 0.0) * 1000)
        success, frame = self._capture.read()
        if not success:
            raise ValueError(f"Impossible de lire une frame à t={timestamp_seconds}s")
        return frame

    def close(self) -> None:
        self._capture.release()
