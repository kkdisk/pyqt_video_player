"""測試 player.config 模組的設定與純邏輯工具函式。"""

import os
from player.config import (
    AspectRatioOption,
    RepeatMode,
    build_snapshot_filename,
    calculate_aspect_rect,
    format_time,
    is_supported_video,
    normalize_path,
)


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


def test_calculate_aspect_rect() -> None:
    # AUTO 與 FILL 應填滿整個容器
    assert calculate_aspect_rect(1000, 800, AspectRatioOption.AUTO) == (0, 0, 1000, 800)
    assert calculate_aspect_rect(1000, 800, AspectRatioOption.FILL) == (0, 0, 1000, 800)

    # 16:9 在 1600x1200 (4:3 容器) 下，寬應為 1600，高應為 900，y 置中為 150
    assert calculate_aspect_rect(1600, 1200, AspectRatioOption.RATIO_16_9) == (
        0,
        150,
        1600,
        900,
    )

    # 4:3 在 1920x1080 (16:9 容器) 下，高應為 1080，寬應為 1440，x 置中為 240
    assert calculate_aspect_rect(1920, 1080, AspectRatioOption.RATIO_4_3) == (
        240,
        0,
        1440,
        1080,
    )


def test_build_snapshot_filename() -> None:
    fname = build_snapshot_filename("C:/Videos/my:movie?.mp4", 65_000, "20261118_183000")
    assert fname == "my_movie__01-05_20261118_183000.png"
