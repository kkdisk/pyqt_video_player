"""測試 player.playlist.PlaylistManager 播放清單管理邏輯。"""

from pathlib import Path
from player.config import RepeatMode, normalize_path
from player.playlist import PlaylistManager


def test_add_files_deduplicates_and_filters() -> None:
    pm = PlaylistManager()
    added = pm.add_files([
        "C:/Videos/a.mp4",
        "C:\\Videos\\a.mp4",
        "C:/Videos/b.mkv",
        "C:/Videos/notes.txt",
    ])
    assert len(added) == 2
    assert len(pm.files) == 2
    assert pm.files[0] == normalize_path("C:/Videos/a.mp4")
    assert pm.files[1] == normalize_path("C:/Videos/b.mkv")


def test_scan_folder_sorts_and_filters(tmp_path: Path) -> None:
    (tmp_path / "b.mp4").write_text("")
    (tmp_path / "a.avi").write_text("")
    (tmp_path / "ignore.jpg").write_text("")

    pm = PlaylistManager()
    files = pm.scan_folder(str(tmp_path))
    assert [Path(p).name for p in files] == ["a.avi", "b.mp4"]


def test_remove_indices_updates_current_index() -> None:
    pm = PlaylistManager()
    pm.add_files(["a.mp4", "b.mp4", "c.mp4", "d.mp4"])
    pm.set_current_path("c.mp4")
    assert pm.current_index == 2

    # 移除索引 0 (在目前播放之前)，索引應左移為 1
    current_removed = pm.remove_indices([0])
    assert current_removed is False
    assert pm.current_index == 1
    assert pm.current_path == normalize_path("c.mp4")

    # 移除目前正在播放的項目
    current_removed = pm.remove_indices([1])
    assert current_removed is True
    assert pm.current_index == -1
    assert pm.current_path is None


def test_repeat_modes_and_get_next_path() -> None:
    pm = PlaylistManager()
    pm.add_files(["1.mp4", "2.mp4"])
    pm.set_current_path("1.mp4")

    # RepeatMode.NONE
    assert pm.get_next_path() == normalize_path("2.mp4")
    assert pm.get_next_path() is None

    # RepeatMode.ONE
    pm.set_current_path("1.mp4")
    pm.repeat_mode = RepeatMode.ONE
    assert pm.get_next_path() == normalize_path("1.mp4")
    assert pm.current_index == 0

    # RepeatMode.ALL
    pm.repeat_mode = RepeatMode.ALL
    assert pm.get_next_path() == normalize_path("2.mp4")
    assert pm.get_next_path() == normalize_path("1.mp4")


def test_get_previous_path_and_repeat_modes() -> None:
    pm = PlaylistManager()
    pm.add_files(["1.mp4", "2.mp4"])
    pm.set_current_path("2.mp4")

    # RepeatMode.NONE
    assert pm.get_previous_path() == normalize_path("1.mp4")
    assert pm.get_previous_path() is None

    # RepeatMode.ALL 在第 0 首往回切換應繞回最後一首
    pm.repeat_mode = RepeatMode.ALL
    assert pm.get_previous_path() == normalize_path("2.mp4")


def test_shuffle_preserves_current_and_restores_original_order() -> None:
    pm = PlaylistManager()
    original = [f"{i}.mp4" for i in range(10)]
    pm.add_files(original)
    pm.set_current_path("5.mp4")

    pm.set_shuffle(True)
    assert pm.shuffle_enabled is True
    assert pm.current_index == 0
    assert pm.current_path == normalize_path("5.mp4")
    assert len(pm.files) == 10

    pm.set_shuffle(False)
    assert pm.shuffle_enabled is False
    assert pm.files == [normalize_path(p) for p in original]
    assert pm.current_path == normalize_path("5.mp4")
    assert pm.current_index == 5
