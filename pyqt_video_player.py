"""PyQt6 影片播放器相容啟動入口。"""

from player.config import Config
from player.main_window import VideoPlayerWindow, main
from player.theme import ThemeManager

__all__ = ["Config", "ThemeManager", "VideoPlayerWindow", "main"]

if __name__ == "__main__":
    main()
