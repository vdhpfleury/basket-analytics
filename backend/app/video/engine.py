"""Video Engine : lecture de vidéo et extraction de métadonnées/frames.

`VideoSource` est l'interface commune. Pour le MVP, seule `FileVideoSource`
(lecture d'un fichier) est implémentée — un flux live (webcam/RTSP)
implémenterait la même interface plus tard (M16), sans changer le code en
aval (détection, tracking, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
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
    def iter_frames(self) -> Iterator[tuple[float, np.ndarray]]:
        """Itère séquentiellement sur les frames, dans l'ordre, avec leur timestamp.

        Contrairement à `read_frame_at` (accès aléatoire, utilisé pour une
        frame isolée en M2/M3), cette méthode lit les frames une par une
        sans "seek" : c'est la seule façon fiable d'obtenir des frames
        réellement consécutives, nécessaire pour le tracking (M4), un seek
        par timestamp pouvant atterrir sur la keyframe la plus proche plutôt
        que la frame exacte.
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

    def iter_frames(self) -> Iterator[tuple[float, np.ndarray]]:
        fps = self._capture.get(cv2.CAP_PROP_FPS)
        frame_index = 0
        while True:
            success, frame = self._capture.read()
            if not success:
                return
            timestamp = frame_index / fps if fps > 0 else 0.0
            yield timestamp, frame
            frame_index += 1

    def close(self) -> None:
        self._capture.release()
