from app.identification import store


def test_track_without_identification_is_explicitly_none() -> None:
    assert store.get_identification("video-x", 42) is None


def test_set_and_get_identification() -> None:
    record = store.set_identification("video-1", 1, player_id="player-1")

    assert record.method == "manual"
    assert record.manually_verified is True
    assert store.get_identification("video-1", 1) == record


def test_remove_identification() -> None:
    store.set_identification("video-2", 1, player_id="player-1")

    removed = store.remove_identification("video-2", 1)

    assert removed is True
    assert store.get_identification("video-2", 1) is None


def test_remove_identification_not_set_returns_false() -> None:
    assert store.remove_identification("video-3", 999) is False


def test_list_identifications_scoped_to_video() -> None:
    store.set_identification("video-4", 1, player_id="player-1")
    store.set_identification("video-4", 2, player_id="player-2")
    store.set_identification("video-5", 1, player_id="player-3")

    results = store.list_identifications("video-4")

    assert {r.track_id for r in results} == {1, 2}
    assert all(r.video_id == "video-4" for r in results)
