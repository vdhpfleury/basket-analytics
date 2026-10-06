"""Catalogue de repères terrain identifiables à l'œil (M6.1).

Dimensions FIBA standard (terrain de 28 x 15 m). Repère : origine (0, 0) au
coin du terrain côté ligne de fond gauche / ligne de touche basse ; `x` le
long de la grande dimension (28 m, lignes de touche), `y` le long de la
petite dimension (15 m, lignes de fond).

Seuls des points clairement identifiables comme intersections de lignes
droites sont proposés (pas l'arc à 3 points, dont le tracé courbe rend le
clic bien moins précis).
"""

from __future__ import annotations

from dataclasses import dataclass

COURT_LENGTH_M = 28.0
COURT_WIDTH_M = 15.0
LANE_WIDTH_M = 4.9  # largeur de la raquette
FREE_THROW_LINE_DISTANCE_M = 5.8  # distance ligne de fond -> ligne de lancers francs
CENTER_CIRCLE_RADIUS_M = 1.8


@dataclass(frozen=True)
class CourtLandmark:
    id: str
    label: str
    x_meters: float
    y_meters: float


_half_width = COURT_WIDTH_M / 2
_half_lane = LANE_WIDTH_M / 2

LANDMARKS: list[CourtLandmark] = [
    CourtLandmark("corner_bl", "Coin bas-gauche", 0.0, 0.0),
    CourtLandmark("corner_br", "Coin bas-droit", COURT_LENGTH_M, 0.0),
    CourtLandmark("corner_tr", "Coin haut-droit", COURT_LENGTH_M, COURT_WIDTH_M),
    CourtLandmark("corner_tl", "Coin haut-gauche", 0.0, COURT_WIDTH_M),
    CourtLandmark("halfcourt_bottom", "Ligne médiane – touche basse", COURT_LENGTH_M / 2, 0.0),
    CourtLandmark("halfcourt_top", "Ligne médiane – touche haute", COURT_LENGTH_M / 2, COURT_WIDTH_M),
    CourtLandmark("center", "Centre du terrain", COURT_LENGTH_M / 2, _half_width),
    CourtLandmark(
        "ft_left_bottom",
        "Raquette gauche – coin bas (ligne de lancers francs)",
        FREE_THROW_LINE_DISTANCE_M,
        _half_width - _half_lane,
    ),
    CourtLandmark(
        "ft_left_top",
        "Raquette gauche – coin haut (ligne de lancers francs)",
        FREE_THROW_LINE_DISTANCE_M,
        _half_width + _half_lane,
    ),
    CourtLandmark(
        "ft_right_bottom",
        "Raquette droite – coin bas (ligne de lancers francs)",
        COURT_LENGTH_M - FREE_THROW_LINE_DISTANCE_M,
        _half_width - _half_lane,
    ),
    CourtLandmark(
        "ft_right_top",
        "Raquette droite – coin haut (ligne de lancers francs)",
        COURT_LENGTH_M - FREE_THROW_LINE_DISTANCE_M,
        _half_width + _half_lane,
    ),
]

_by_id = {landmark.id: landmark for landmark in LANDMARKS}


def get_landmark(landmark_id: str) -> CourtLandmark | None:
    return _by_id.get(landmark_id)
