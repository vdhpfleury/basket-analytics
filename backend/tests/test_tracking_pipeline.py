"""Test d'intégration du pipeline détection->tracking (M4.3/M4.5), avec un
détecteur factice (le contenu réel des frames n'importe pas ici : on teste
l'assemblage VideoEngine -> Detector -> Tracker, pas la détection elle-même,
déjà testée en M3).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from app.detection.detector import BoundingBox, Detection, Detector
from app.tracking.pipeline import run_tracking
from app.tracking.tracker import IoUTracker
from app.video.engine import FileVideoSource


class _ScriptedDetector(Detector):
    """Retourne une détection par frame, bbox en mouvement constant."""

    def __init__(self, step_px: float = 2.0) -> None:
        self._step_px = step_px
        self._call_count = 0

    def detect(self, frame: np.ndarray, confidence_threshold: float = 0.5) -> list[Detection]:
        x = self._call_count * self._step_px
        self._call_count += 1
        box = BoundingBox(x1=x, y1=0, x2=x + 20, y2=40)
        return [Detection(bbox=box, confidence=0.9, label="person")]


def test_run_tracking_on_full_video_keeps_single_stable_id(
    synthetic_video_path: Path,
) -> None:
    source = FileVideoSource(synthetic_video_path)
    try:
        track_points = run_tracking(
            source, _ScriptedDetector(), IoUTracker(), sample_every_n_frames=1
        )
    finally:
        source.close()

    assert len(track_points) == 30  # FIXTURE_FRAME_COUNT (conftest.py)
    assert len({tp.track_id for tp in track_points}) == 1

    timestamps = [tp.timestamp for tp in track_points]
    assert timestamps == sorted(timestamps)


def test_run_tracking_respects_sample_every_n_frames(synthetic_video_path: Path) -> None:
    source = FileVideoSource(synthetic_video_path)
    try:
        track_points = run_tracking(
            source, _ScriptedDetector(), IoUTracker(), sample_every_n_frames=2
        )
    finally:
        source.close()

    assert len(track_points) == 15  # une frame sur deux, sur 30 frames


def test_track_point_x_y_pixel_is_bbox_bottom_center() -> None:
    source_detector = _ScriptedDetector(step_px=0.0)
    detections = source_detector.detect(np.zeros((1, 1, 3), dtype=np.uint8))
    from app.tracking.tracker import TrackedDetection, TrackPoint

    tracked = TrackedDetection(track_id=1, detection=detections[0])
    point = TrackPoint.from_tracked_detection(timestamp=1.5, tracked=tracked)

    assert point.x_pixel == (detections[0].bbox.x1 + detections[0].bbox.x2) / 2
    assert point.y_pixel == detections[0].bbox.y2
