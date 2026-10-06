"""Tests de l'homographie (M6.6).

Le test principal construit une transformation perspective CONNUE
(terrain -> pixel), génère des points pixel à partir de points terrain
connus, calibre avec 4 d'entre eux, puis vérifie que le 5e point — non
utilisé pour calibrer — est correctement retrouvé. Ça prouve que la
fonction généralise, pas seulement qu'elle recopie ses entrées.
"""

from __future__ import annotations

import numpy as np
import pytest

from app.court.calibration import (
    CalibrationError,
    PointCorrespondence,
    compute_homography,
    project_pixel_to_court,
    reprojection_errors,
)

# Homographie terrain -> pixel connue (simule une caméra en perspective).
_H_TRUE = np.array(
    [
        [8.0, 2.0, 100.0],
        [1.0, 6.0, 50.0],
        [0.01, 0.005, 1.0],
    ]
)


def _court_to_pixel(x: float, y: float) -> tuple[float, float]:
    vector = _H_TRUE @ np.array([x, y, 1.0])
    return float(vector[0] / vector[2]), float(vector[1] / vector[2])


def test_homography_recovers_held_out_point() -> None:
    calibration_court_points = [(0.0, 0.0), (28.0, 0.0), (28.0, 15.0), (0.0, 15.0)]
    held_out_court_point = (14.0, 7.5)

    correspondences = [
        PointCorrespondence(pixel_x=px, pixel_y=py, court_x=cx, court_y=cy)
        for (cx, cy), (px, py) in (
            (p, _court_to_pixel(*p)) for p in calibration_court_points
        )
    ]

    homography = compute_homography(correspondences)

    held_out_pixel = _court_to_pixel(*held_out_court_point)
    recovered = project_pixel_to_court(homography, *held_out_pixel)

    assert recovered[0] == pytest.approx(held_out_court_point[0], abs=1e-3)
    assert recovered[1] == pytest.approx(held_out_court_point[1], abs=1e-3)


def test_reprojection_errors_near_zero_for_exact_points() -> None:
    court_points = [(0.0, 0.0), (28.0, 0.0), (28.0, 15.0), (0.0, 15.0)]
    correspondences = [
        PointCorrespondence(pixel_x=px, pixel_y=py, court_x=cx, court_y=cy)
        for (cx, cy), (px, py) in ((p, _court_to_pixel(*p)) for p in court_points)
    ]

    homography = compute_homography(correspondences)
    errors = reprojection_errors(homography, correspondences)

    assert all(error < 1e-6 for error in errors)


def test_compute_homography_requires_at_least_four_points() -> None:
    correspondences = [
        PointCorrespondence(pixel_x=0, pixel_y=0, court_x=0, court_y=0),
        PointCorrespondence(pixel_x=1, pixel_y=0, court_x=1, court_y=0),
        PointCorrespondence(pixel_x=1, pixel_y=1, court_x=1, court_y=1),
    ]

    with pytest.raises(CalibrationError):
        compute_homography(correspondences)


def test_compute_homography_rejects_collinear_points() -> None:
    correspondences = [
        PointCorrespondence(pixel_x=0, pixel_y=0, court_x=0, court_y=0),
        PointCorrespondence(pixel_x=10, pixel_y=0, court_x=10, court_y=0),
        PointCorrespondence(pixel_x=20, pixel_y=0, court_x=20, court_y=0),
        PointCorrespondence(pixel_x=30, pixel_y=0, court_x=30, court_y=0),
    ]

    with pytest.raises(CalibrationError):
        compute_homography(correspondences)
