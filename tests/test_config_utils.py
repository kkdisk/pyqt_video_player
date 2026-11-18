"""測試 player.config 模組的設定與純邏輯工具函式。"""

import os
from player.config import RepeatMode, format_time, is_supported_video, normalize_path


def test_format_time_zero_and_negative() -> None:
    assert format_time(-500) == "00:00"
    assert format_time(0) == "00:00"


def test_format_time_minutes_and_seconds() -> None:
    assert format_time(5_000) == "00:05"
    assert format_time(65_000) == "01:05"
    assert format_time(3_599_000) == "59:59"


def test_format_time_hours() -> None:
    assert format_time(3_600_000) == "01:00:00"
    assert format_time(3_661_000) == "01:01:01"
    assert format_time(36_000_000) == "10:00:00"


def test_normalize_path() -> None:
    assert normalize_path("") == ""
    expected = os.path.normpath("C:/Videos/test.mp4")
    assert normalize_path("C:/Videos/test.mp4") == expected
    assert normalize_path("C:\\Videos\\test.mp4") == expected


def test_is_supported_video() -> None:
    assert is_supported_video("movie.mp4") is True
    assert is_supported_video("MOVIE.MKV") is True
    assert is_supported_video("clip.webm") is True
    assert is_supported_video("image.png") is False
    assert is_supported_video("") is False


def test_repeat_mode_enum_values() -> None:
    assert RepeatMode.NONE == 0
    assert RepeatMode.ONE == 1
    assert RepeatMode.ALL == 2
