from app.court.landmarks import LANDMARKS, get_landmark


def test_get_known_landmark() -> None:
    landmark = get_landmark("center")

    assert landmark is not None
    assert landmark.x_meters == 14.0
    assert landmark.y_meters == 7.5


def test_get_unknown_landmark_returns_none() -> None:
    assert get_landmark("does-not-exist") is None


def test_all_landmarks_within_court_bounds() -> None:
    for landmark in LANDMARKS:
        assert 0.0 <= landmark.x_meters <= 28.0
        assert 0.0 <= landmark.y_meters <= 15.0


def test_landmark_ids_are_unique() -> None:
    ids = [landmark.id for landmark in LANDMARKS]
    assert len(ids) == len(set(ids))
