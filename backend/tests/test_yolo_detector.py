"""Tests du détecteur YOLO.

Deux niveaux : des tests rapides sur la logique de parsing (modèle factice,
aucun chargement réel), et un test d'intégration qui charge le vrai modèle
pour vérifier l'absence de crash sur CPU. La validation qu'une vraie
personne est détectée avec une confiance correcte a été faite manuellement
(voir docs/benchmarks.md) plutôt que dans la suite automatisée, pour éviter
de committer une photo tierce ou de dépendre du réseau pendant les tests.
"""

from __future__ import annotations

import numpy as np
import pytest

from app.detection.detector import BoundingBox, Detection
from app.detection.yolo_detector import YOLOPersonDetector


class _FakeBox:
    def __init__(self, xyxy: list[float], conf: float) -> None:
        self.xyxy = [np.array(xyxy)]
        self.conf = [conf]


class _FakeResult:
    def __init__(self, boxes: list[_FakeBox]) -> None:
        self.boxes = boxes


class _FakeModel:
    def __init__(self, boxes: list[_FakeBox]) -> None:
        self._boxes = boxes

    def predict(self, *args: object, **kwargs: object) -> list[_FakeResult]:
        return [_FakeResult(self._boxes)]


def _detector_with_fake_model(boxes: list[_FakeBox]) -> YOLOPersonDetector:
    detector = YOLOPersonDetector.__new__(YOLOPersonDetector)
    detector._model = _FakeModel(boxes)  # noqa: SLF001 — test double, contournement volontaire
    return detector


def test_detect_parses_model_output_into_detections() -> None:
    detector = _detector_with_fake_model([_FakeBox([10.0, 20.0, 110.0, 220.0], 0.73)])

    detections = detector.detect(np.zeros((240, 160, 3), dtype=np.uint8), confidence_threshold=0.5)

    assert detections == [
        Detection(
            bbox=BoundingBox(x1=10.0, y1=20.0, x2=110.0, y2=220.0),
            confidence=pytest.approx(0.73),
            label="person",
        )
    ]


def test_detect_returns_empty_list_when_no_boxes() -> None:
    detector = _detector_with_fake_model([])

    assert detector.detect(np.zeros((10, 10, 3), dtype=np.uint8)) == []


@pytest.fixture(scope="module")
def real_detector() -> YOLOPersonDetector:
    return YOLOPersonDetector()


def test_real_model_runs_without_crash_on_blank_frame(real_detector: YOLOPersonDetector) -> None:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    detections = real_detector.detect(frame, confidence_threshold=0.5)

    assert detections == []
