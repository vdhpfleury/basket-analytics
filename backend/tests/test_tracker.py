"""Tests du tracker IoU (M4.5) : séquences synthétiques déterministes,
sans dépendance à un modèle de détection réel.
"""

from __future__ import annotations

from app.detection.detector import BoundingBox, Detection
from app.tracking.tracker import IoUTracker, iou


def _box(x1: float, y1: float, x2: float, y2: float) -> BoundingBox:
    return BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2)


def _detection(box: BoundingBox, confidence: float = 0.9) -> Detection:
    return Detection(bbox=box, confidence=confidence, label="person")


def test_iou_identical_boxes_is_one() -> None:
    box = _box(0, 0, 10, 10)
    assert iou(box, box) == 1.0


def test_iou_non_overlapping_boxes_is_zero() -> None:
    assert iou(_box(0, 0, 10, 10), _box(20, 20, 30, 30)) == 0.0


def test_iou_partial_overlap() -> None:
    # Boîte 10x10 chevauchée sur un carré 5x5 (25 px²) par une seconde boîte
    # décalée de 5px : union = 100 + 100 - 25 = 175.
    value = iou(_box(0, 0, 10, 10), _box(5, 5, 15, 15))
    assert value == 25 / 175


def test_stable_id_for_smoothly_moving_object() -> None:
    tracker = IoUTracker()
    track_ids = []

    for step in range(10):
        box = _box(step * 4, 0, step * 4 + 40, 80)
        [tracked] = tracker.update([_detection(box)])
        track_ids.append(tracked.track_id)

    assert len(set(track_ids)) == 1, f"L'ID aurait dû rester stable, obtenu : {track_ids}"


def test_new_object_far_away_gets_new_id_after_disappearance() -> None:
    tracker = IoUTracker(max_age=2)

    [first] = tracker.update([_detection(_box(0, 0, 40, 80))])

    # Le track disparaît plus longtemps que `max_age` -> abandonné.
    tracker.update([])
    tracker.update([])
    tracker.update([])

    [second] = tracker.update([_detection(_box(500, 500, 540, 580))])

    assert second.track_id != first.track_id


def test_two_well_separated_objects_tracked_independently() -> None:
    tracker = IoUTracker()
    ids_a: list[int] = []
    ids_b: list[int] = []

    for step in range(8):
        box_a = _box(step * 3, 0, step * 3 + 30, 60)  # se déplace vers la droite
        box_b = _box(600 - step * 3, 0, 630 - step * 3, 60)  # se déplace vers la gauche
        results = tracker.update([_detection(box_a), _detection(box_b)])
        by_bbox = {r.detection.bbox: r.track_id for r in results}
        ids_a.append(by_bbox[box_a])
        ids_b.append(by_bbox[box_b])

    assert len(set(ids_a)) == 1, f"objet A : ID instable, obtenu {ids_a}"
    assert len(set(ids_b)) == 1, f"objet B : ID instable, obtenu {ids_b}"
    assert ids_a[0] != ids_b[0], "deux objets distincts ne devraient jamais partager un ID"


def test_two_objects_crossing_without_full_occlusion_stay_stable() -> None:
    """Cas limite documenté : deux objets qui se croisent sans se superposer
    totalement restent correctement suivis (l'algorithme hongrois choisit à
    chaque frame la correspondance qui maximise l'IoU global). Une
    occlusion complète (une boîte entièrement masquée par l'autre) n'est en
    revanche PAS garantie de rester stable avec ce tracker "sans mémoire de
    mouvement" — limite assumée, voir docstring de `tracker.py`.
    """
    tracker = IoUTracker()
    ids_a: list[int] = []
    ids_b: list[int] = []

    for step in range(10):
        # A va de gauche à droite, B de droite à gauche ; ils se croisent
        # vers step=5 mais restent décalés verticalement (pas d'occlusion totale).
        box_a = _box(step * 20, 0, step * 20 + 40, 40)
        box_b = _box(200 - step * 20, 20, 240 - step * 20, 60)
        results = tracker.update([_detection(box_a), _detection(box_b)])
        by_bbox = {r.detection.bbox: r.track_id for r in results}
        ids_a.append(by_bbox[box_a])
        ids_b.append(by_bbox[box_b])

    assert len(set(ids_a)) == 1
    assert len(set(ids_b)) == 1


def test_reset_clears_state() -> None:
    tracker = IoUTracker()
    tracker.update([_detection(_box(0, 0, 10, 10))])

    tracker.reset()
    [tracked] = tracker.update([_detection(_box(0, 0, 10, 10))])

    assert tracked.track_id == 1
