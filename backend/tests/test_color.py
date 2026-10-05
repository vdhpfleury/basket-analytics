import numpy as np

from app.detection.detector import BoundingBox
from app.identification.color import bgr_to_hex, dominant_color_bgr, suggest_groups


def test_dominant_color_on_solid_region() -> None:
    frame = np.full((100, 100, 3), (10, 20, 200), dtype=np.uint8)  # BGR

    color = dominant_color_bgr(frame, BoundingBox(0, 0, 100, 100))

    assert color == (10, 20, 200)


def test_bgr_to_hex() -> None:
    assert bgr_to_hex((0, 0, 255)) == "#ff0000"  # rouge
    assert bgr_to_hex((255, 0, 0)) == "#0000ff"  # bleu


def test_suggest_groups_empty() -> None:
    assert suggest_groups([]) == []


def test_suggest_groups_single_color() -> None:
    assert suggest_groups([(10, 10, 10)]) == [0]


def test_suggest_groups_identical_colors_all_same_group() -> None:
    colors = [(10, 10, 10), (10, 10, 10), (10, 10, 10)]

    groups = suggest_groups(colors)

    assert len(set(groups)) == 1


def test_suggest_groups_two_distinct_colors_separated() -> None:
    colors = [(0, 0, 255), (0, 0, 255), (255, 0, 0), (255, 0, 0)]

    groups = suggest_groups(colors)

    assert groups[0] == groups[1]
    assert groups[2] == groups[3]
    assert groups[0] != groups[2]
