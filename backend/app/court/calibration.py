"""Calibration terrain (M6) : homographie pixel <-> terrain.

Au moins 4 correspondances (point image, point terrain connu) sont
nécessaires pour calculer une homographie. Au-delà de 4, `cv2.findHomography`
utilise RANSAC pour être robuste à un point mal cliqué.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


class CalibrationError(ValueError):
    pass


@dataclass(frozen=True)
class PointCorrespondence:
    pixel_x: float
    pixel_y: float
    court_x: float
    court_y: float


def compute_homography(correspondences: list[PointCorrespondence]) -> np.ndarray:
    if len(correspondences) < 4:
        raise CalibrationError(
            f"Au moins 4 points de correspondance sont nécessaires (reçu {len(correspondences)})"
        )

    pixel_points = np.array([[c.pixel_x, c.pixel_y] for c in correspondences], dtype=np.float32)
    court_points = np.array([[c.court_x, c.court_y] for c in correspondences], dtype=np.float32)

    method = cv2.RANSAC if len(correspondences) > 4 else 0
    homography, _ = cv2.findHomography(pixel_points, court_points, method=method)
    if homography is None:
        raise CalibrationError(
            "Impossible de calculer l'homographie à partir de ces points "
            "(probablement colinéaires ou dupliqués)"
        )
    return homography


def project_pixel_to_court(homography: np.ndarray, pixel_x: float, pixel_y: float) -> tuple[float, float]:
    point = np.array([[[pixel_x, pixel_y]]], dtype=np.float32)
    projected = cv2.perspectiveTransform(point, homography)
    x, y = projected[0][0]
    return float(x), float(y)


def reprojection_errors(
    homography: np.ndarray, correspondences: list[PointCorrespondence]
) -> list[float]:
    """Distance (en mètres) entre chaque point terrain attendu et celui
    recalculé à partir du pixel via l'homographie — indicateur de qualité
    de la calibration."""
    errors = []
    for c in correspondences:
        x, y = project_pixel_to_court(homography, c.pixel_x, c.pixel_y)
        errors.append(((x - c.court_x) ** 2 + (y - c.court_y) ** 2) ** 0.5)
    return errors
