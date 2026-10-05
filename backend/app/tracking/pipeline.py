"""Pipeline détection → tracking sur une séquence complète de frames (M4.3)."""

from __future__ import annotations

from app.detection.detector import Detector
from app.tracking.tracker import Tracker, TrackPoint
from app.video.engine import VideoSource


def run_tracking(
    source: VideoSource,
    detector: Detector,
    tracker: Tracker,
    confidence_threshold: float = 0.5,
    sample_every_n_frames: int = 1,
) -> list[TrackPoint]:
    """Parcourt `source` séquentiellement, détecte et piste les joueurs.

    `sample_every_n_frames` permet de ne traiter qu'une frame sur N (ex. 2
    pour diviser le temps de traitement par deux — voir `docs/benchmarks.md`
    sur le coût CPU de la détection). Le tracker reçoit alors des frames non
    strictement consécutives ; `max_age` de `IoUTracker` doit être choisi en
    conséquence pour tolérer ces "trous".
    """
    tracker.reset()
    track_points: list[TrackPoint] = []

    for frame_index, (timestamp, frame) in enumerate(source.iter_frames()):
        if frame_index % sample_every_n_frames != 0:
            continue

        detections = detector.detect(frame, confidence_threshold=confidence_threshold)
        tracked = tracker.update(detections)

        for t in tracked:
            track_points.append(TrackPoint.from_tracked_detection(timestamp, t))

    return track_points
