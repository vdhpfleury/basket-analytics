import pytest

from app.detection.detector import BoundingBox, Detection, Detector


def test_bounding_box_is_immutable() -> None:
    box = BoundingBox(x1=1.0, y1=2.0, x2=3.0, y2=4.0)

    with pytest.raises(AttributeError):
        box.x1 = 10.0  # type: ignore[misc]


def test_detector_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        Detector()  # type: ignore[abstract]


def test_detection_equality() -> None:
    box = BoundingBox(x1=0.0, y1=0.0, x2=10.0, y2=10.0)

    assert Detection(bbox=box, confidence=0.9, label="person") == Detection(
        bbox=box, confidence=0.9, label="person"
    )
