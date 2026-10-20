import pytest
from core.database import StudioDatabase


def test_import_does_not_create_database(tmp_path):
    path = tmp_path / "nested" / "test.db"
    StudioDatabase(path)
    assert not path.exists()


def test_download_path_is_persisted(tmp_path):
    db = StudioDatabase(tmp_path / "test.db")
    db.log_generation("a", "title", "p", "t", "model")
    db.update_track_status("a", "complete", audio_url="url")
    db.update_track_status("a", "downloaded", local_path="local.mp3")
    assert db.get_track("a")["local_path"] == "local.mp3"
    assert db.get_track("a")["audio_url"] == "url"


def test_repeated_record_preserves_result_fields(tmp_path):
    db = StudioDatabase(tmp_path / "test.db")
    db.log_generation("a", "title", "p", "t", "model")
    db.update_track_status("a", "downloaded", audio_url="url", local_path="local.mp3")
    db.log_generation("a", "title", "p", "t", "model")
    assert db.get_track("a")["local_path"] == "local.mp3"


@pytest.mark.parametrize("limit", [0, -1, 501, True, "50"])
def test_library_limit_is_bounded(limit):
    with pytest.raises(ValueError):
        StudioDatabase().list_tracks(limit)
