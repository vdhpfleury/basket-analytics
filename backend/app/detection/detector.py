"""Interface de détection, indépendante du framework/modèle utilisé.

`Detector` est le seul contrat connu du reste de l'application (API,
tracking futur...). `YOLOPersonDetector` (voir `yolo_detector.py`) en est
l'implémentation par défaut pour le MVP, mais un autre détecteur pourrait
l'implémenter sans changer le code appelant.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(frozen=True)
class Detection:
    bbox: BoundingBox
    confidence: float
    label: str


class Detector(ABC):
    @abstractmethod
    def detect(self, frame: np.ndarray, confidence_threshold: float = 0.5) -> list[Detection]:
        """Retourne les détections de `frame` dont la confiance dépasse le seuil."""
