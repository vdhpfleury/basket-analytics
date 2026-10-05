"""Heuristique couleur de maillot (M5.3) : aide visuelle au regroupement des
tracks par équipe pendant la correction manuelle — PAS une identification
automatique fiable. L'identification réelle (track -> joueur nommé) reste
toujours une action humaine (voir `app/identification/store.py`).
"""

from __future__ import annotations

import numpy as np
from scipy.cluster.vq import kmeans2

from app.detection.detector import BoundingBox


def _torso_region(frame: np.ndarray, bbox: BoundingBox) -> np.ndarray:
    """Région centrale du buste : évite la tête, les jambes et le fond."""
    height, width = frame.shape[:2]
    x1, y1, x2, y2 = bbox.x1, bbox.y1, bbox.x2, bbox.y2
    box_height = y2 - y1
    box_width = x2 - x1

    top = y1 + box_height * 0.2
    bottom = y1 + box_height * 0.5
    left = x1 + box_width * 0.2
    right = x1 + box_width * 0.8

    top_i = max(0, int(top))
    bottom_i = min(height, max(top_i + 1, int(bottom)))
    left_i = max(0, int(left))
    right_i = min(width, max(left_i + 1, int(right)))

    return frame[top_i:bottom_i, left_i:right_i]


def dominant_color_bgr(frame: np.ndarray, bbox: BoundingBox) -> tuple[int, int, int]:
    region = _torso_region(frame, bbox)
    if region.size == 0:
        return (0, 0, 0)
    mean = region.reshape(-1, 3).mean(axis=0)
    return (int(mean[0]), int(mean[1]), int(mean[2]))


def bgr_to_hex(bgr: tuple[int, int, int]) -> str:
    b, g, r = bgr
    return f"#{r:02x}{g:02x}{b:02x}"


def suggest_groups(colors: list[tuple[int, int, int]], n_groups: int = 2) -> list[int]:
    """Regroupe les couleurs en `n_groups` clusters (k-means).

    Retourne un groupe (0..n_groups-1) par couleur, dans le même ordre.
    Si trop peu de couleurs distinctes pour former `n_groups` clusters,
    tout le monde est placé dans le groupe 0 plutôt que de lever une erreur.
    """
    if len(colors) < 2:
        return [0] * len(colors)

    data = np.array(colors, dtype=float)
    distinct = len({tuple(c) for c in colors})
    k = min(n_groups, distinct)
    if k < 2:
        return [0] * len(colors)

    try:
        _, labels = kmeans2(data, k, seed=0, minit="++")
    except Exception:
        return [0] * len(colors)

    return [int(label) for label in labels]
