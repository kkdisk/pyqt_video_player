"""應用程式設定常數、列舉與純邏輯工具函式。"""

import os
import re
from datetime import datetime
from enum import IntEnum
from typing import Dict, List, Optional, Tuple
from PyQt6.QtCore import QSize


class RepeatMode(IntEnum):
    """播放清單循環模式。"""

    NONE = 0
    ONE = 1
    ALL = 2


class AspectRatioOption(IntEnum):
    """影片畫面比例模式。"""

    AUTO = 0
    RATIO_16_9 = 1
    RATIO_4_3 = 2
    FILL = 3


ASPECT_RATIO_LABELS: Dict[AspectRatioOption, str] = {
    AspectRatioOption.AUTO: "自動",
    AspectRatioOption.RATIO_16_9: "16:9",
    AspectRatioOption.RATIO_4_3: "4:3",
    AspectRatioOption.FILL: "填滿",
}


class Config:
    """集中管理應用程式的所有設定。"""

    APP_TITLE: str = "PyQt6 影片播放器 v1.4.0"
    ORGANIZATION_NAME: str = "MyVideoPlayer"  # 用於 QSettings
    APP_NAME: str = "PyQt6VideoPlayer"        # 用於 QSettings
    DEFAULT_WINDOW_SIZE: QSize = QSize(1040, 720)
    DEFAULT_VOLUME: float = 0.7               # 0.0 到 1.0
    SUPPORTED_VIDEO_FORMATS: tuple[str, ...] = (
        ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"
    )
    SUPPORTED_SUBTITLE_FORMATS: tuple[str, ...] = (".srt", ".vtt")
    SEEK_SLIDER_PRECISION: int = 1000         # 進度條的預設精度
    PLAYBACK_RATES: List[float] = [0.5, 0.75, 1.0, 1.5, 2.0]
    SEEK_STEP_MS: int = 5000                  # 快轉/倒退步長 (5 秒)
    VOLUME_STEP: int = 5                      # 音量調整步長 (5%)
    SNAPSHOT_DIR_NAME: str = "PyQt6VideoPlayer_Snapshots"


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


def calculate_aspect_rect(
    container_w: int, container_h: int, mode: AspectRatioOption
) -> Tuple[int, int, int, int]:
    """計算指定畫面比例模式在容器內的置中矩形 (x, y, width, height)。"""
    w = max(1, container_w)
    h = max(1, container_h)

    if mode in (AspectRatioOption.AUTO, AspectRatioOption.FILL):
        return (0, 0, w, h)

    target_ratio = 16.0 / 9.0 if mode == AspectRatioOption.RATIO_16_9 else 4.0 / 3.0
    current_ratio = w / h

    if current_ratio > target_ratio:
        target_h = h
        target_w = max(1, int(round(h * target_ratio)))
    else:
        target_w = w
        target_h = max(1, int(round(w / target_ratio)))

    x = (w - target_w) // 2
    y = (h - target_h) // 2
    return (x, y, target_w, target_h)


def build_snapshot_filename(
    video_path: Optional[str],
    position_ms: int,
    timestamp_str: Optional[str] = None,
) -> str:
    """依據目前影片檔名與播放時間點產生安全的 PNG 截圖檔名。"""
    if video_path:
        stem = os.path.splitext(os.path.basename(video_path))[0]
        safe_stem = re.sub(r'[<>:"/\\|?*]+', "_", stem).strip() or "video"
    else:
        safe_stem = "video"

    pos_tag = format_time(max(0, position_ms)).replace(":", "-")
    ts = timestamp_str or datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe_stem}_{pos_tag}_{ts}.png"
