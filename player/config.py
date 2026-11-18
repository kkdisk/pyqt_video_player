"""應用程式設定常數、列舉與純邏輯工具函式。"""

import os
from enum import IntEnum
from typing import List
from PyQt6.QtCore import QSize


class RepeatMode(IntEnum):
    """播放清單循環模式。"""

    NONE = 0
    ONE = 1
    ALL = 2


class Config:
    """集中管理應用程式的所有設定。"""

    APP_TITLE: str = "PyQt6 影片播放器 v1.3.0"
    ORGANIZATION_NAME: str = "MyVideoPlayer"  # 用於 QSettings
    APP_NAME: str = "PyQt6VideoPlayer"        # 用於 QSettings
    DEFAULT_WINDOW_SIZE: QSize = QSize(1000, 700)
    DEFAULT_VOLUME: float = 0.7               # 0.0 到 1.0
    SUPPORTED_VIDEO_FORMATS: tuple[str, ...] = (
        ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"
    )
    SEEK_SLIDER_PRECISION: int = 1000         # 進度條的預設精度
    PLAYBACK_RATES: List[float] = [0.5, 0.75, 1.0, 1.5, 2.0]
    SEEK_STEP_MS: int = 5000                  # 快轉/倒退步長 (5 秒)
    VOLUME_STEP: int = 5                      # 音量調整步長 (5%)


def format_time(ms: int) -> str:
    """將毫秒轉換為 MM:SS 或 HH:MM:SS 格式字串。"""
    if ms <= 0:
        return "00:00"
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def normalize_path(path: str) -> str:
    """正規化本地檔案路徑（解決 Windows 正反斜線不一致問題）。"""
    if not path:
        return ""
    return os.path.normpath(path)


def is_supported_video(path: str) -> bool:
    """檢查檔案路徑的副檔名是否為支援的影片格式。"""
    if not path:
        return False
    return path.lower().endswith(Config.SUPPORTED_VIDEO_FORMATS)
