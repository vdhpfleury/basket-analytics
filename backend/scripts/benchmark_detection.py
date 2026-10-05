"""Mesure le FPS de détection sur CPU (M3.6).

Usage :
    python scripts/benchmark_detection.py chemin/vers/video.mp4 [--frames 30] [--confidence 0.5]

Échantillonne des frames réparties sur la vidéo, lance la détection sur
chacune, et rapporte le FPS moyen de traitement (hors chargement du modèle).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.detection.yolo_detector import YOLOPersonDetector  # noqa: E402
from app.video.engine import FileVideoSource  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video_path", type=Path)
    parser.add_argument("--frames", type=int, default=30, help="Nombre de frames échantillonnées")
    parser.add_argument("--confidence", type=float, default=0.5)
    args = parser.parse_args()

    source = FileVideoSource(args.video_path)
    metadata = source.get_metadata()
    print(
        f"Vidéo : {args.video_path.name} — {metadata.width}x{metadata.height}, "
        f"{metadata.fps:.1f} fps source, {metadata.duration_seconds:.1f}s"
    )

    timestamps = [
        metadata.duration_seconds * i / args.frames for i in range(args.frames)
    ]
    frames = [source.read_frame_at(t) for t in timestamps]
    source.close()

    detector = YOLOPersonDetector()

    # Warmup : exclu de la mesure (première inférence plus lente).
    detector.detect(frames[0], confidence_threshold=args.confidence)

    t0 = time.perf_counter()
    total_detections = 0
    for frame in frames:
        detections = detector.detect(frame, confidence_threshold=args.confidence)
        total_detections += len(detections)
    elapsed = time.perf_counter() - t0

    fps = len(frames) / elapsed
    print(f"{len(frames)} frames traitées en {elapsed:.2f}s -> {fps:.2f} FPS (CPU)")
    print(f"Total détections (toutes frames confondues) : {total_detections}")


if __name__ == "__main__":
    main()
