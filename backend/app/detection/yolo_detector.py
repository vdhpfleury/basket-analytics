"""Détecteur par défaut du MVP : YOLO (Ultralytics), classe "person" (COCO).

Modèle "nano" choisi pour le compromis vitesse/précision sur CPU (benchmark
dans docs/benchmarks.md). Le chemin du modèle est configurable pour pouvoir
changer de variante (small, medium...) sans toucher au code.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from ultralytics import YOLO

from app.detection.detector import BoundingBox, Detection, Detector

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "yolov8n.pt"
PERSON_CLASS_ID = 0  # index COCO de la classe "person"


class YOLOPersonDetector(Detector):
    def __init__(self, model_path: Path | str = DEFAULT_MODEL_PATH) -> None:
        self._model = YOLO(str(model_path))

    def detect(self, frame: np.ndarray, confidence_threshold: float = 0.5) -> list[Detection]:
        results = self._model.predict(
            frame,
            conf=confidence_threshold,
            classes=[PERSON_CLASS_ID],
            verbose=False,
        )

        detections: list[Detection] = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = (float(v) for v in box.xyxy[0].tolist())
            confidence = float(box.conf[0])
            detections.append(
                Detection(
                    bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
                    confidence=confidence,
                    label="person",
                )
            )
        return detections
