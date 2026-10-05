from pathlib import Path

import pytest

from app.video.engine import FileVideoSource
from tests.conftest import FIXTURE_FPS, FIXTURE_FRAME_COUNT, FIXTURE_HEIGHT, FIXTURE_WIDTH


def test_metadata_matches_fixture(synthetic_video_path: Path) -> None:
    source = FileVideoSource(synthetic_video_path)
    try:
        metadata = source.get_metadata()
    finally:
        source.close()

    assert metadata.fps == pytest.approx(FIXTURE_FPS, rel=0.05)
    assert metadata.frame_count == FIXTURE_FRAME_COUNT
    assert metadata.width == FIXTURE_WIDTH
    assert metadata.height == FIXTURE_HEIGHT
    assert metadata.duration_seconds == pytest.approx(
        FIXTURE_FRAME_COUNT / FIXTURE_FPS, rel=0.05
    )


def test_read_frame_at_returns_expected_shape(synthetic_video_path: Path) -> None:
    source = FileVideoSource(synthetic_video_path)
    try:
        frame = source.read_frame_at(0.5)
    finally:
        source.close()

    assert frame.shape == (FIXTURE_HEIGHT, FIXTURE_WIDTH, 3)


def test_read_frame_beyond_duration_raises(synthetic_video_path: Path) -> None:
    source = FileVideoSource(synthetic_video_path)
    try:
        with pytest.raises(ValueError):
            source.read_frame_at(1000.0)
    finally:
        source.close()


def test_open_nonexistent_file_raises(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.mp4"

    with pytest.raises(ValueError):
        FileVideoSource(missing)


def test_open_non_video_file_raises(tmp_path: Path) -> None:
    not_a_video = tmp_path / "not_a_video.mp4"
    not_a_video.write_text("ceci n'est pas une vidéo")

    with pytest.raises(ValueError):
        source = FileVideoSource(not_a_video)
        source.read_frame_at(0.0)
