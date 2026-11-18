"""播放清單狀態管理模組（與 UI 元件解耦）。"""

import logging
import os
import random
from typing import Iterable, List, Optional

from player.config import RepeatMode, is_supported_video, normalize_path

logger = logging.getLogger(__name__)


class PlaylistManager:
    """管理播放清單的檔案列表、當前索引、循環與隨機播放狀態。"""

    def __init__(self) -> None:
        self._files: List[str] = []
        self._original_files: List[str] = []
        self.current_index: int = -1
        self.repeat_mode: RepeatMode = RepeatMode.NONE
        self.shuffle_enabled: bool = False

    @property
    def files(self) -> List[str]:
        """回傳目前清單的唯讀複本。"""
        return list(self._files)

    @property
    def current_path(self) -> Optional[str]:
        """回傳目前選中項目的路徑，若無效則回傳 None。"""
        if 0 <= self.current_index < len(self._files):
            return self._files[self.current_index]
        return None

    def scan_folder(self, dir_path: str) -> List[str]:
        """掃描資料夾內支援的影片檔案並取代目前清單。"""
        if not dir_path or not os.path.isdir(dir_path):
            return []

        scanned: List[str] = []
        try:
            for filename in sorted(os.listdir(dir_path)):
                if is_supported_video(filename):
                    scanned.append(normalize_path(os.path.join(dir_path, filename)))
        except OSError as exc:
            logger.error("掃描資料夾時發生錯誤 (%s): %s", dir_path, exc)
            return []

        self._original_files = list(scanned)
        self._files = list(scanned)
        self.current_index = -1

        if self.shuffle_enabled and len(self._files) > 1:
            random.shuffle(self._files)

        return list(self._files)

    def add_files(self, paths: Iterable[str]) -> List[str]:
        """將多個影片路徑加入清單（自動正規化與去重），回傳實際新增的路徑。"""
        added: List[str] = []
        for raw_path in paths:
            norm = normalize_path(raw_path)
            if not norm or not is_supported_video(norm):
                continue
            if norm not in self._files:
                self._files.append(norm)
                self._original_files.append(norm)
                added.append(norm)
        return added

    def remove_indices(self, indices: Iterable[int]) -> bool:
        """依據索引集合移除清單項目，回傳目前正在播放的項目是否被移除。"""
        sorted_rows = sorted(
            {idx for idx in indices if 0 <= idx < len(self._files)},
            reverse=True,
        )
        current_removed = False

        for row in sorted_rows:
            removed_path = self._files.pop(row)
            if removed_path in self._original_files:
                self._original_files.remove(removed_path)

            if row == self.current_index:
                self.current_index = -1
                current_removed = True
            elif row < self.current_index:
                self.current_index -= 1

        return current_removed

    def clear(self) -> None:
        """清空播放清單並重設索引。"""
        self._files.clear()
        self._original_files.clear()
        self.current_index = -1

    def set_current_path(self, path: str) -> int:
        """依據路徑設定目前索引；若不在清單中則設為 -1。"""
        norm = normalize_path(path)
        if norm in self._files:
            self.current_index = self._files.index(norm)
        else:
            self.current_index = -1
        return self.current_index

    def cycle_repeat_mode(self) -> RepeatMode:
        """依序切換循環模式：NONE -> ONE -> ALL -> NONE。"""
        self.repeat_mode = RepeatMode((self.repeat_mode + 1) % 3)
        return self.repeat_mode

    def set_shuffle(self, enabled: bool) -> None:
        """開啟或關閉隨機播放；開啟時洗牌並置頂目前項目，關閉時還原原始順序。"""
        self.shuffle_enabled = enabled
        if not self._files:
            return

        active_path = self.current_path

        if enabled:
            remaining = [p for p in self._files if p != active_path]
            random.shuffle(remaining)
            if active_path is not None:
                self._files = [active_path] + remaining
                self.current_index = 0
            else:
                self._files = remaining
                self.current_index = -1
        else:
            self._files = list(self._original_files)
            if active_path is not None and active_path in self._files:
                self.current_index = self._files.index(active_path)
            else:
                self.current_index = -1

    def get_next_path(self) -> Optional[str]:
        """根據目前索引與循環模式計算下一首影片路徑。"""
        if not self._files:
            return None

        if self.repeat_mode == RepeatMode.ONE:
            if self.current_path is not None:
                return self.current_path
            self.current_index = 0
            return self._files[0]

        next_index = -1
        if self.current_index < len(self._files) - 1:
            next_index = self.current_index + 1
        elif self.repeat_mode == RepeatMode.ALL:
            next_index = 0

        if next_index != -1:
            self.current_index = next_index
            return self._files[next_index]

        return None

    def get_previous_path(self) -> Optional[str]:
        """根據目前索引與循環模式計算上一首影片路徑。"""
        if not self._files:
            return None

        if self.repeat_mode == RepeatMode.ONE:
            if self.current_path is not None:
                return self.current_path
            self.current_index = 0
            return self._files[0]

        prev_index = -1
        if self.current_index > 0:
            prev_index = self.current_index - 1
        elif self.repeat_mode == RepeatMode.ALL:
            prev_index = len(self._files) - 1

        if prev_index != -1:
            self.current_index = prev_index
            return self._files[prev_index]

        return None
