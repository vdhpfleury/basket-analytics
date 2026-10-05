"""Fixtures partagées : génération de vidéos de test synthétiques.

On évite de committer un fichier vidéo binaire : une courte vidéo MP4 est
générée à la volée avec OpenCV (quelques frames de couleur unie), ce qui
suffit à tester l'ouverture, les métadonnées et la lecture de frames sans
dépendre d'un fichier externe.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

FIXTURE_FPS = 10.0
FIXTURE_FRAME_COUNT = 30
FIXTURE_WIDTH = 64
FIXTURE_HEIGHT = 48


def _write_synthetic_video(path: Path) -> None:
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(
        str(path), fourcc, FIXTURE_FPS, (FIXTURE_WIDTH, FIXTURE_HEIGHT)
    )
    try:
        for i in range(FIXTURE_FRAME_COUNT):
            frame = np.full((FIXTURE_HEIGHT, FIXTURE_WIDTH, 3), i % 256, dtype=np.uint8)
            writer.write(frame)
    finally:
        writer.release()


@pytest.fixture
def synthetic_video_path(tmp_path: Path) -> Path:
    path = tmp_path / "synthetic.mp4"
    _write_synthetic_video(path)
    return path
