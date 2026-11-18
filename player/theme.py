"""應用程式現代化深色/淺色設計系統與主題管理模組。"""

from dataclasses import dataclass
from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication


@dataclass(frozen=True)
class ThemeTokens:
    """主題色彩語意 Token。"""

    is_dark: bool
    bg_main: str
    bg_surface: str
    bg_elevated: str
    bg_hover: str
    bg_pressed: str
    bg_canvas: str
    bg_card: str
    border: str
    text_primary: str
    text_secondary: str
    text_muted: str
    icon_normal: str
    icon_disabled: str
    accent: str
    accent_hover: str
    accent_pressed: str
    accent_soft: str
    slider_track: str
    tooltip_bg: str


DARK_TOKENS = ThemeTokens(
    is_dark=True,
    bg_main="#121215",
    bg_surface="#1A1A1F",
    bg_elevated="#24242B",
    bg_hover="#2E2E37",
    bg_pressed="#383842",
    bg_canvas="#0B0B0D",
    bg_card="#18181D",
    border="#2B2B34",
    text_primary="#F4F4F5",
    text_secondary="#A1A1AA",
    text_muted="#71717A",
    icon_normal="#E4E4E7",
    icon_disabled="#6E6E7A",
    accent="#3B82F6",
    accent_hover="#60A5FA",
    accent_pressed="#2563EB",
    accent_soft="rgba(59, 130, 246, 0.18)",
    slider_track="#32323C",
    tooltip_bg="#27272A",
)

LIGHT_TOKENS = ThemeTokens(
    is_dark=False,
    bg_main="#F4F6F9",
    bg_surface="#FFFFFF",
    bg_elevated="#F1F5F9",
    bg_hover="#E2E8F0",
    bg_pressed="#CBD5E1",
    bg_canvas="#0F172A",
    bg_card="#FFFFFF",
    border="#E2E8F0",
    text_primary="#0F172A",
    text_secondary="#475569",
    text_muted="#94A3B8",
    icon_normal="#1E293B",
    icon_disabled="#94A3B8",
    accent="#2563EB",
    accent_hover="#3B82F6",
    accent_pressed="#1D4ED8",
    accent_soft="rgba(37, 99, 235, 0.12)",
    slider_track="#CBD5E1",
    tooltip_bg="#FFFFFF",
)


class ThemeManager:
    """管理應用程式的現代化深色/淺色主題。"""

    def __init__(self, app: Optional[QApplication]) -> None:
        self.app = app
        self.is_dark: bool = True

    @property
    def tokens(self) -> ThemeTokens:
        """取得當前主題的色彩 Token。"""
        return DARK_TOKENS if self.is_dark else LIGHT_TOKENS

    def toggle_theme(self, is_dark: Optional[bool] = None) -> ThemeTokens:
        """切換或設定指定的主題模式，並回傳套用後的 Token。"""
        self.is_dark = not self.is_dark if is_dark is None else is_dark
        t = self.tokens
        if self.app is not None:
            self._apply_palette(t)
            self.app.setStyleSheet(self._build_stylesheet(t))
        return t

    def _apply_palette(self, t: ThemeTokens) -> None:
        """套用對應的系統調色板（確保對話框與原生選單一致）。"""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(t.bg_main))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(t.text_primary))
        palette.setColor(QPalette.ColorRole.Base, QColor(t.bg_surface))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(t.bg_elevated))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(t.tooltip_bg))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(t.text_primary))
        palette.setColor(QPalette.ColorRole.Text, QColor(t.text_primary))
        palette.setColor(QPalette.ColorRole.Button, QColor(t.bg_elevated))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(t.text_primary))
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Highlight, QColor(t.accent))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
        self.app.setPalette(palette)

    @staticmethod
    def _build_stylesheet(t: ThemeTokens) -> str:
        """依據主題 Token 建構統一的現代化 QSS 樣式表。"""
        return f"""
        * {{
            font-family: 'Segoe UI', 'Microsoft JhengHei UI', 'Microsoft JhengHei', sans-serif;
        }}
        QMainWindow, QDialog {{
            background-color: {t.bg_main};
            color: {t.text_primary};
        }}
        QWidget {{
            color: {t.text_primary};
        }}
        QToolTip {{
            background-color: {t.tooltip_bg};
            color: {t.text_primary};
            border: 1px solid {t.border};
            border-radius: 6px;
            padding: 5px 8px;
            font-size: 12px;
        }}

        /* === 頂部工具列 === */
        QToolBar#HeaderToolBar {{
            background-color: {t.bg_surface};
            border: none;
            border-bottom: 1px solid {t.border};
            padding: 6px 10px;
            spacing: 6px;
        }}
        QToolBar#HeaderToolBar QToolButton {{
            background-color: transparent;
            color: {t.text_primary};
            border: 1px solid transparent;
            border-radius: 8px;
            padding: 6px 10px;
            font-size: 13px;
            font-weight: 500;
        }}
        QToolBar#HeaderToolBar QToolButton:hover {{
            background-color: {t.bg_hover};
        }}
        QToolBar#HeaderToolBar QToolButton:pressed {{
            background-color: {t.bg_pressed};
        }}
        QToolBar#HeaderToolBar QToolButton:checked {{
            background-color: {t.accent_soft};
            border-color: {t.accent};
            color: {t.accent};
        }}
        QLabel#HeaderFileLabel {{
            color: {t.text_secondary};
            font-size: 12px;
            padding: 0 8px;
        }}

        /* === 影片畫布與空狀態引導 === */
        QVideoWidget {{
            background-color: #000000;
        }}
        QWidget#EmptyStateContainer {{
            background-color: {t.bg_canvas};
        }}
        QFrame#EmptyStateCard {{
            background-color: {t.bg_card};
            border: 1px dashed {t.border};
            border-radius: 16px;
        }}
        QLabel#EmptyStateTitle {{
            color: {t.text_primary};
            font-size: 18px;
            font-weight: 600;
        }}
        QLabel#EmptyStateSubtitle {{
            color: {t.text_secondary};
            font-size: 13px;
        }}
        QPushButton#PrimaryActionButton {{
            background-color: {t.accent};
            color: #FFFFFF;
            border: none;
            border-radius: 8px;
            padding: 9px 18px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton#PrimaryActionButton:hover {{
            background-color: {t.accent_hover};
        }}
        QPushButton#PrimaryActionButton:pressed {{
            background-color: {t.accent_pressed};
        }}
        QPushButton#SecondaryActionButton {{
            background-color: {t.bg_elevated};
            color: {t.text_primary};
            border: 1px solid {t.border};
            border-radius: 8px;
            padding: 9px 18px;
            font-size: 13px;
            font-weight: 500;
        }}
        QPushButton#SecondaryActionButton:hover {{
            background-color: {t.bg_hover};
        }}

        /* === 播放清單 Dock === */
        QDockWidget {{
            background-color: {t.bg_surface};
            border: none;
        }}
        QWidget#PlaylistHeader {{
            background-color: {t.bg_surface};
            border-bottom: 1px solid {t.border};
        }}
        QLabel#PlaylistTitle {{
            color: {t.text_primary};
            font-size: 13px;
            font-weight: 600;
        }}
        QLabel#PlaylistCountBadge {{
            background-color: {t.bg_elevated};
            color: {t.text_secondary};
            border-radius: 9px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 600;
        }}
        QWidget#PlaylistContainer {{
            background-color: {t.bg_surface};
            border-left: 1px solid {t.border};
        }}
        QToolBar#PlaylistToolBar {{
            background-color: {t.bg_surface};
            border-bottom: 1px solid {t.border};
            padding: 4px 6px;
            spacing: 4px;
        }}
        QToolBar#PlaylistToolBar QToolButton {{
            background-color: transparent;
            border: none;
            border-radius: 6px;
            padding: 5px;
        }}
        QToolBar#PlaylistToolBar QToolButton:hover {{
            background-color: {t.bg_hover};
        }}
        QListWidget {{
            background-color: {t.bg_surface};
            border: none;
            padding: 6px;
            outline: none;
        }}
        QListWidget::item {{
            color: {t.text_primary};
            padding: 8px 10px;
            margin: 2px 0;
            border-radius: 8px;
            font-size: 13px;
        }}
        QListWidget::item:hover {{
            background-color: {t.bg_hover};
        }}
        QListWidget::item:selected {{
            background-color: {t.accent};
            color: #FFFFFF;
            font-weight: 500;
        }}

        /* === 底部控制列 === */
        QWidget#ControlsBar {{
            background-color: {t.bg_surface};
            border-top: 1px solid {t.border};
        }}
        QLabel#TimeLabel {{
            color: {t.text_secondary};
            font-family: 'Cascadia Mono', 'Consolas', 'Segoe UI', monospace;
            font-size: 12px;
            font-weight: 500;
        }}

        /* 主播放圓形按鈕 */
        QPushButton#PlayPauseButton {{
            background-color: {t.accent};
            border: none;
            border-radius: 19px;
        }}
        QPushButton#PlayPauseButton:hover {{
            background-color: {t.accent_hover};
        }}
        QPushButton#PlayPauseButton:pressed {{
            background-color: {t.accent_pressed};
        }}
        QPushButton#PlayPauseButton:disabled {{
            background-color: {t.bg_elevated};
            border: 1px solid {t.border};
        }}

        /* 輔助控制按鈕 (Ghost) */
        QPushButton[class="ghost"],
        QPushButton#StopButton,
        QPushButton#PrevButton,
        QPushButton#NextButton,
        QPushButton#RepeatButton,
        QPushButton#ShuffleButton,
        QPushButton#VolumeButton,
        QPushButton#FullscreenButton,
        QPushButton#DockCloseButton {{
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 8px;
            padding: 4px;
        }}
        QPushButton#StopButton:hover,
        QPushButton#PrevButton:hover,
        QPushButton#NextButton:hover,
        QPushButton#RepeatButton:hover,
        QPushButton#ShuffleButton:hover,
        QPushButton#VolumeButton:hover,
        QPushButton#FullscreenButton:hover,
        QPushButton#DockCloseButton:hover {{
            background-color: {t.bg_hover};
        }}
        QPushButton#StopButton:pressed,
        QPushButton#PrevButton:pressed,
        QPushButton#NextButton:pressed,
        QPushButton#RepeatButton:pressed,
        QPushButton#ShuffleButton:pressed,
        QPushButton#VolumeButton:pressed,
        QPushButton#FullscreenButton:pressed {{
            background-color: {t.bg_pressed};
        }}
        QPushButton#RepeatButton:checked,
        QPushButton#ShuffleButton:checked {{
            background-color: {t.accent_soft};
            border-color: {t.accent};
        }}

        /* === 進度條與音量條 === */
        QSlider#SeekSlider {{
            height: 20px;
        }}
        QSlider#SeekSlider::groove:horizontal {{
            height: 5px;
            background: {t.slider_track};
            border-radius: 2.5px;
        }}
        QSlider#SeekSlider::sub-page:horizontal {{
            background: {t.accent};
            border-radius: 2.5px;
        }}
        QSlider#SeekSlider::add-page:horizontal {{
            background: {t.slider_track};
            border-radius: 2.5px;
        }}
        QSlider#SeekSlider::handle:horizontal {{
            background: #FFFFFF;
            border: 2px solid {t.accent};
            width: 12px;
            height: 12px;
            margin: -5px 0;
            border-radius: 8px;
        }}
        QSlider#SeekSlider::handle:horizontal:disabled {{
            background: {t.bg_elevated};
            border: 2px solid {t.border};
            width: 12px;
            height: 12px;
            margin: -5px 0;
            border-radius: 8px;
        }}

        QSlider#VolumeSlider {{
            height: 18px;
        }}
        QSlider#VolumeSlider::groove:horizontal {{
            height: 4px;
            background: {t.slider_track};
            border-radius: 2px;
        }}
        QSlider#VolumeSlider::sub-page:horizontal {{
            background: {t.accent};
            border-radius: 2px;
        }}
        QSlider#VolumeSlider::handle:horizontal {{
            background: {t.text_primary};
            border: 2px solid {t.accent};
            width: 10px;
            height: 10px;
            margin: -5px 0;
            border-radius: 7px;
        }}

        /* === 播放速度下拉選單 === */
        QComboBox#RateCombo {{
            background-color: {t.bg_elevated};
            color: {t.text_primary};
            border: 1px solid {t.border};
            border-radius: 8px;
            padding: 4px 10px;
            font-size: 12px;
            font-weight: 600;
        }}
        QComboBox#RateCombo:hover {{
            background-color: {t.bg_hover};
        }}
        QComboBox#RateCombo:disabled {{
            color: {t.text_muted};
        }}
        QComboBox#RateCombo::drop-down {{
            border: none;
            width: 18px;
        }}
        QComboBox#RateCombo QAbstractItemView {{
            background-color: {t.bg_surface};
            color: {t.text_primary};
            border: 1px solid {t.border};
            border-radius: 8px;
            padding: 4px;
            selection-background-color: {t.accent};
            selection-color: #FFFFFF;
            outline: none;
        }}

        /* === 狀態列與右鍵選單 === */
        QStatusBar {{
            background-color: {t.bg_surface};
            color: {t.text_secondary};
            border-top: 1px solid {t.border};
            font-size: 12px;
            padding: 2px 10px;
        }}
        QStatusBar::item {{
            border: none;
        }}
        QMenu {{
            background-color: {t.bg_surface};
            color: {t.text_primary};
            border: 1px solid {t.border};
            border-radius: 8px;
            padding: 6px;
        }}
        QMenu::item {{
            padding: 6px 18px;
            border-radius: 6px;
        }}
        QMenu::item:selected {{
            background-color: {t.accent};
            color: #FFFFFF;
        }}
        QMenu::separator {{
            height: 1px;
            background: {t.border};
            margin: 4px 8px;
        }}

        /* === 捲軸美化 === */
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 4px 0;
        }}
        QScrollBar::handle:vertical {{
            background: {t.slider_track};
            border-radius: 4px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {t.text_muted};
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {{
            background: none;
            height: 0px;
        }}
        """
