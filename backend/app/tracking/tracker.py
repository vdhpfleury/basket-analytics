"""Tracking multi-objets : associe des détections à des identités persistantes
(`track_id`) d'une frame à l'autre.

`Tracker` est l'interface commune, indépendante de l'algorithme utilisé.
`IoUTracker` est l'implémentation par défaut du MVP : un algorithme "SORT
allégé" (association par recouvrement de boîtes — IoU — via l'algorithme
hongrois, **sans filtre de Kalman**). Choisi pour rester simple, sans
dépendance lourde supplémentaire (juste `scipy`), et entièrement testable
avec des séquences de détections synthétiques.

Limite connue, assumée pour le MVP : sans prédiction de mouvement, un
changement de direction brusque ou une occlusion entre deux joueurs peut
provoquer un changement d'ID. Documenté et mesuré dans
`docs/benchmarks.md`. Un tracker plus robuste (ByteTrack, SORT avec filtre
de Kalman) pourrait remplacer `IoUTracker` sans changer l'interface
`Tracker` ni le code appelant.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import linear_sum_assignment

from app.detection.detector import BoundingBox, Detection


@dataclass(frozen=True)
class TrackedDetection:
    track_id: int
    detection: Detection


@dataclass(frozen=True)
class TrackPoint:
    track_id: int
    timestamp: float
    bbox: BoundingBox
    confidence: float
    x_pixel: float
    y_pixel: float

    @staticmethod
    def from_tracked_detection(timestamp: float, tracked: TrackedDetection) -> "TrackPoint":
        bbox = tracked.detection.bbox
        # Centre bas de la boîte (~position des pieds), plus pertinent que le
        # centre géométrique pour une future projection au sol (M6).
        return TrackPoint(
            track_id=tracked.track_id,
            timestamp=timestamp,
            bbox=bbox,
            confidence=tracked.detection.confidence,
            x_pixel=(bbox.x1 + bbox.x2) / 2,
            y_pixel=bbox.y2,
        )


def iou(a: BoundingBox, b: BoundingBox) -> float:
    x1 = max(a.x1, b.x1)
    y1 = max(a.y1, b.y1)
    x2 = min(a.x2, b.x2)
    y2 = min(a.y2, b.y2)
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)

    area_a = max(0.0, a.x2 - a.x1) * max(0.0, a.y2 - a.y1)
    area_b = max(0.0, b.x2 - b.x1) * max(0.0, b.y2 - b.y1)
    union = area_a + area_b - intersection

    return intersection / union if union > 0 else 0.0


class Tracker(ABC):
    @abstractmethod
    def update(self, detections: list[Detection]) -> list[TrackedDetection]:
        """Met à jour l'état du tracker avec les détections d'UNE frame.

        Les appels successifs doivent correspondre à des frames
        consécutives, dans l'ordre. Retourne les détections avec leur
        `track_id` assigné (nouveau ou existant).
        """

    @abstractmethod
    def reset(self) -> None:
        """Réinitialise l'état (nouvelle vidéo)."""


@dataclass
class _ActiveTrack:
    track_id: int
    bbox: BoundingBox
    frames_since_update: int = 0


@dataclass
class IoUTracker(Tracker):
    iou_threshold: float = 0.3
    max_age: int = 5  # frames sans correspondance avant d'abandonner un track

    _active_tracks: list[_ActiveTrack] = field(default_factory=list, init=False)
    _next_id: int = field(default=1, init=False)

    def reset(self) -> None:
        self._active_tracks = []
        self._next_id = 1

    def update(self, detections: list[Detection]) -> list[TrackedDetection]:
        results: list[TrackedDetection | None] = [None] * len(detections)
        matched_track_indices: set[int] = set()
        matched_detection_indices: set[int] = set()

        if self._active_tracks and detections:
            cost_matrix = np.array(
                [
                    [1.0 - iou(track.bbox, d.bbox) for d in detections]
                    for track in self._active_tracks
                ]
            )
            track_indices, detection_indices = linear_sum_assignment(cost_matrix)
            for ti, di in zip(track_indices, detection_indices, strict=True):
                if cost_matrix[ti, di] <= 1.0 - self.iou_threshold:
                    track = self._active_tracks[ti]
                    track.bbox = detections[di].bbox
                    track.frames_since_update = 0
                    results[di] = TrackedDetection(track_id=track.track_id, detection=detections[di])
                    matched_track_indices.add(ti)
                    matched_detection_indices.add(di)

        still_active = []
        for i, track in enumerate(self._active_tracks):
            if i not in matched_track_indices:
                track.frames_since_update += 1
            if track.frames_since_update <= self.max_age:
                still_active.append(track)
        self._active_tracks = still_active

        for di, detection in enumerate(detections):
            if di not in matched_detection_indices:
                track = _ActiveTrack(track_id=self._next_id, bbox=detection.bbox)
                self._active_tracks.append(track)
                results[di] = TrackedDetection(track_id=track.track_id, detection=detection)
                self._next_id += 1

        return [r for r in results if r is not None]
