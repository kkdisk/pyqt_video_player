"""影片播放器主視窗與應用程式入口模組。"""

import logging
import os
import sys
from typing import Callable, Optional, Union

from PyQt6.QtCore import (
    QPoint,
    QSettings,
    QSize,
    QStandardPaths,
    Qt,
    QTimer,
    QUrl,
    pyqtSlot,
)
from PyQt6.QtGui import (
    QAction,
    QCloseEvent,
    QDragEnterEvent,
    QDropEvent,
    QIcon,
    QKeyEvent,
    QKeySequence,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from player.config import (
    Config,
    RepeatMode,
    format_time,
    is_supported_video,
    normalize_path,
)
from player.icons import create_icon
from player.playlist import PlaylistManager
from player.theme import ThemeManager

logger = logging.getLogger(__name__)

try:
    from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
    from player.widgets import ClickableSlider, EmptyStateWidget, PlayerVideoWidget

    QT_MULTIMEDIA_AVAILABLE = True
except ImportError as exc:
    logger.error("找不到 PyQt6.QtMultimedia 或 QtMultimediaWidgets 模組: %s", exc)
    QT_MULTIMEDIA_AVAILABLE = False


class VideoPlayerWindow(QMainWindow):
    """影片播放器的主視窗協調器。"""

    def __init__(self) -> None:
        super().__init__()

        if not QT_MULTIMEDIA_AVAILABLE:
            QMessageBox.critical(
                self,
                "缺少模組",
                "找不到 PyQt6.QtMultimedia 或 QtMultimediaWidgets 模組。\n"
                "請確保已安裝 `PyQt6`。\n"
                "應用程式即將退出。",
            )
            QTimer.singleShot(100, self.close)
            return

        self.settings = QSettings(Config.ORGANIZATION_NAME, Config.APP_NAME)
        self.setWindowTitle(Config.APP_TITLE)
        self.resize(Config.DEFAULT_WINDOW_SIZE)
        self.setAcceptDrops(True)

        self.theme_manager = ThemeManager(QApplication.instance())
        self.playlist = PlaylistManager()

        self.current_path: Optional[str] = None
        self._is_slider_pressed: bool = False
        self.is_muted: bool = False
        self._dock_was_visible_before_fullscreen: bool = True

        # 圖示快取（隨主題切換更新）
        self._icon_play = QIcon()
        self._icon_pause = QIcon()
        self._icon_vol = QIcon()
        self._icon_muted = QIcon()
        self._icon_repeat = QIcon()
        self._icon_repeat_one = QIcon()
        self._icon_fs = QIcon()
        self._icon_exit_fs = QIcon()

        # 1. 建立核心媒體與畫布元件
        self.video_widget = PlayerVideoWidget()
        self.video_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.empty_state_widget = EmptyStateWidget()

        self.canvas_stack = QStackedWidget()
        self.canvas_stack.addWidget(self.empty_state_widget)  # index 0: 空狀態引導
        self.canvas_stack.addWidget(self.video_widget)        # index 1: 影片畫布
        self.canvas_stack.setCurrentIndex(0)

        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setAudioOutput(self.audio_output)

        # 2. 建立 UI 元件
        self._create_docks()
        self._create_actions()
        self._create_toolbars()
        self._create_controls_bar()

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("準備就緒 — 拖放影片或點擊「開啟影片」開始播放")

        # 3. 連接訊號與套用設定/主題圖示
        self._connect_signals()
        self.load_settings()
        self._apply_theme_icons()
        self._update_ui_state(QMediaPlayer.PlaybackState.StoppedState)

    # --------------------------------------------------------------------------
    # UI 建構
    # --------------------------------------------------------------------------

    def _create_actions(self) -> None:
        """建立工具列與選單動作。"""
        self.open_action = self._create_action(
            "開啟影片",
            QKeySequence.StandardKey.Open,
            self.open_file_dialog,
            tooltip="開啟影片檔案 (Ctrl+O)",
        )
        self.open_folder_action = self._create_action(
            "開啟資料夾",
            "Ctrl+Shift+O",
            self.open_folder_dialog,
            tooltip="開啟資料夾並載入所有影片 (Ctrl+Shift+O)",
        )
        self.exit_action = self._create_action(
            "離開",
            QKeySequence.StandardKey.Quit,
            self.close,
        )

        self.toggle_playlist_action = self.playlist_dock.toggleViewAction()
        self.toggle_playlist_action.setText("播放清單")
        self.toggle_playlist_action.setToolTip("顯示或隱藏播放清單面板")

        self.toggle_theme_action = self._create_action(
            "切換主題",
            "Ctrl+T",
            self._on_toggle_theme,
            tooltip="切換深色 / 淺色主題 (Ctrl+T)",
        )

        self.add_files_action = self._create_action(
            "新增檔案",
            None,
            self._on_add_files,
            tooltip="新增影片到播放清單",
        )
        self.remove_item_action = self._create_action(
            "移除選中",
            QKeySequence.StandardKey.Delete,
            self._on_remove_items,
            tooltip="從清單移除選中項目 (Delete)",
        )
        self.clear_list_action = self._create_action(
            "清空清單",
            None,
            self._on_clear_list,
            tooltip="清空整個播放清單",
        )

        self.mute_action = QAction("靜音", self)
        self.mute_action.triggered.connect(self._toggle_mute)

        step_sec = Config.SEEK_STEP_MS // 1000
        self.seek_forward_action = QAction(f"快轉 {step_sec} 秒 (→)", self)
        self.seek_forward_action.triggered.connect(self._seek_forward)

        self.seek_backward_action = QAction(f"倒退 {step_sec} 秒 (←)", self)
        self.seek_backward_action.triggered.connect(self._seek_backward)

    def _create_toolbars(self) -> None:
        """建立統合的頂部現代化工具列與播放清單工具列。"""
        self.header_toolbar = self.addToolBar("主工具列")
        self.header_toolbar.setObjectName("HeaderToolBar")
        self.header_toolbar.setMovable(False)
        self.header_toolbar.setFloatable(False)
        self.header_toolbar.setIconSize(QSize(18, 18))
        self.header_toolbar.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )

        self.header_toolbar.addAction(self.open_action)
        self.header_toolbar.addAction(self.open_folder_action)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.header_toolbar.addWidget(spacer)

        self.header_file_label = QLabel("")
        self.header_file_label.setObjectName("HeaderFileLabel")
        self.header_toolbar.addWidget(self.header_file_label)

        spacer_right = QWidget()
        spacer_right.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.header_toolbar.addWidget(spacer_right)

        self.header_toolbar.addAction(self.toggle_playlist_action)
        self.header_toolbar.addAction(self.toggle_theme_action)

        self.playlist_toolbar.addActions(
            [self.add_files_action, self.remove_item_action, self.clear_list_action]
        )
        self.playlist_widget.addAction(self.remove_item_action)

    def _create_docks(self) -> None:
        """建立可停靠的現代化播放清單面板。"""
        self.playlist_dock = QDockWidget("播放清單", self)
        self.playlist_dock.setObjectName("PlaylistDock")
        self.playlist_dock.setMinimumWidth(260)

        # 自訂標題列（解決系統預設深色標題列按鈕模糊不清的問題）
        header_widget = QWidget()
        header_widget.setObjectName("PlaylistHeader")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 10, 8, 10)
        header_layout.setSpacing(8)

        title_label = QLabel("播放清單")
        title_label.setObjectName("PlaylistTitle")
        header_layout.addWidget(title_label)

        self.playlist_count_badge = QLabel("0")
        self.playlist_count_badge.setObjectName("PlaylistCountBadge")
        header_layout.addWidget(self.playlist_count_badge)

        header_layout.addStretch(1)

        self.dock_close_button = QPushButton()
        self.dock_close_button.setObjectName("DockCloseButton")
        self.dock_close_button.setFixedSize(26, 26)
        self.dock_close_button.setIconSize(QSize(14, 14))
        self.dock_close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dock_close_button.setToolTip("隱藏播放清單")
        self.dock_close_button.clicked.connect(self.playlist_dock.hide)
        header_layout.addWidget(self.dock_close_button)

        self.playlist_dock.setTitleBarWidget(header_widget)

        playlist_container = QWidget()
        playlist_container.setObjectName("PlaylistContainer")
        layout = QVBoxLayout(playlist_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.playlist_toolbar = QToolBar("播放清單工具列")
        self.playlist_toolbar.setObjectName("PlaylistToolBar")
        self.playlist_toolbar.setMovable(False)
        self.playlist_toolbar.setIconSize(QSize(16, 16))
        layout.addWidget(self.playlist_toolbar)

        self.playlist_widget = QListWidget()
        self.playlist_widget.itemDoubleClicked.connect(
            self._on_playlist_item_double_clicked
        )
        self.playlist_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        layout.addWidget(self.playlist_widget, 1)

        self.playlist_dock.setWidget(playlist_container)
        self.playlist_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.playlist_dock)
        self.playlist_dock.setVisible(True)

    def _create_ghost_button(self, object_name: str, tooltip: str, checkable: bool = False) -> QPushButton:
        """建立統一規格的現代化 Ghost 控制按鈕。"""
        btn = QPushButton()
        btn.setObjectName(object_name)
        btn.setFixedSize(34, 34)
        btn.setIconSize(QSize(18, 18))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tooltip)
        btn.setCheckable(checkable)
        return btn

    def _create_controls_bar(self) -> None:
        """建立底部現代化播放控制列。"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.canvas_stack, 1)

        self.controls_widget = QWidget()
        self.controls_widget.setObjectName("ControlsBar")
        controls_layout = QVBoxLayout(self.controls_widget)
        controls_layout.setContentsMargins(14, 6, 14, 10)
        controls_layout.setSpacing(6)

        self.seek_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setObjectName("SeekSlider")
        self.seek_slider.setRange(0, Config.SEEK_SLIDER_PRECISION)
        controls_layout.addWidget(self.seek_slider)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(6)

        self.prev_button = self._create_ghost_button("PrevButton", "上一部影片")
        self.prev_button.clicked.connect(self._play_previous)
        buttons_layout.addWidget(self.prev_button)

        self.play_pause_button = QPushButton()
        self.play_pause_button.setObjectName("PlayPauseButton")
        self.play_pause_button.setFixedSize(38, 38)
        self.play_pause_button.setIconSize(QSize(20, 20))
        self.play_pause_button.setCursor(Qt.CursorShape.PointingHandCursor)
        buttons_layout.addWidget(self.play_pause_button)

        self.next_button = self._create_ghost_button("NextButton", "下一部影片")
        self.next_button.clicked.connect(self._play_next)
        buttons_layout.addWidget(self.next_button)

        self.stop_button = self._create_ghost_button("StopButton", "停止播放")
        self.stop_button.clicked.connect(self._on_stop_clicked)
        buttons_layout.addWidget(self.stop_button)

        buttons_layout.addSpacing(8)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setObjectName("TimeLabel")
        self.time_label.setMinimumWidth(105)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        buttons_layout.addWidget(self.time_label)

        buttons_layout.addSpacing(8)

        self.repeat_button = self._create_ghost_button(
            "RepeatButton", "循環: 關", checkable=True
        )
        self.repeat_button.clicked.connect(self._on_repeat_toggled)
        buttons_layout.addWidget(self.repeat_button)

        self.shuffle_button = self._create_ghost_button(
            "ShuffleButton", "隨機播放: 關", checkable=True
        )
        self.shuffle_button.clicked.connect(self._on_shuffle_toggled)
        buttons_layout.addWidget(self.shuffle_button)

        buttons_layout.addStretch(1)

        self.rate_combo = QComboBox()
        self.rate_combo.setObjectName("RateCombo")
        self.rate_combo.addItems([f"{rate}x" for rate in Config.PLAYBACK_RATES])
        self.rate_combo.setCurrentText("1.0x")
        self.rate_combo.setFixedWidth(72)
        self.rate_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rate_combo.setToolTip("播放速度")
        self.rate_combo.currentTextChanged.connect(self._on_rate_changed)
        buttons_layout.addWidget(self.rate_combo)

        buttons_layout.addSpacing(6)

        self.volume_button = self._create_ghost_button("VolumeButton", "靜音 (M)")
        self.volume_button.clicked.connect(self._toggle_mute)
        buttons_layout.addWidget(self.volume_button)

        self.volume_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setObjectName("VolumeSlider")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setFixedWidth(108)
        buttons_layout.addWidget(self.volume_slider)

        buttons_layout.addSpacing(4)

        self.fullscreen_button = self._create_ghost_button(
            "FullscreenButton", "切換全螢幕 (F11)"
        )
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        buttons_layout.addWidget(self.fullscreen_button)

        controls_layout.addLayout(buttons_layout)
        main_layout.addWidget(self.controls_widget, 0)

        wrapper = QWidget()
        wrapper.setLayout(main_layout)
        self.setCentralWidget(wrapper)

    def _connect_signals(self) -> None:
        """連接 QMediaPlayer 與 UI 訊號。"""
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.media_player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.media_player.errorOccurred.connect(self._on_media_error)

        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)

        self.seek_slider.sliderPressed.connect(self._on_slider_pressed)
        self.seek_slider.sliderMoved.connect(self._on_slider_moved)
        self.seek_slider.sliderReleased.connect(self._on_slider_released)
        self.seek_slider.clickedValue.connect(self._on_seek_clicked)

        self.video_widget.customContextMenuRequested.connect(
            self._show_video_context_menu
        )
        self.video_widget.doubleClicked.connect(self.toggle_fullscreen)

        self.empty_state_widget.openFileRequested.connect(self.open_file_dialog)
        self.empty_state_widget.openFolderRequested.connect(self.open_folder_dialog)

    # --------------------------------------------------------------------------
    # 主題與向量圖示同步
    # --------------------------------------------------------------------------

    @pyqtSlot()
    def _on_toggle_theme(self) -> None:
        """切換深/淺色主題並更新所有向量圖示。"""
        self.theme_manager.toggle_theme()
        self._apply_theme_icons()

    def _apply_theme_icons(self) -> None:
        """依據目前主題 Token 重新渲染並套用所有高對比 SVG 向量圖示。"""
        t = self.theme_manager.tokens

        # 1. 快取狀態圖示（主播放鍵即使在 Disabled 狀態也能清晰辨識）
        self._icon_play = create_icon(
            "play", "#FFFFFF", disabled_color=t.text_secondary, size=22
        )
        self._icon_pause = create_icon(
            "pause", "#FFFFFF", disabled_color=t.text_secondary, size=22
        )
        self._icon_vol = create_icon(
            "volume", t.icon_normal, disabled_color=t.icon_disabled, size=20
        )
        self._icon_muted = create_icon(
            "volume_muted", t.accent, disabled_color=t.icon_disabled, size=20
        )
        self._icon_repeat = create_icon(
            "repeat",
            t.icon_normal,
            disabled_color=t.icon_disabled,
            active_color=t.accent,
            size=18,
        )
        self._icon_repeat_one = create_icon(
            "repeat_one",
            t.icon_normal,
            disabled_color=t.icon_disabled,
            active_color=t.accent,
            size=18,
        )
        self._icon_fs = create_icon(
            "fullscreen", t.icon_normal, disabled_color=t.icon_disabled, size=18
        )
        self._icon_exit_fs = create_icon(
            "exit_fullscreen", t.icon_normal, disabled_color=t.icon_disabled, size=18
        )

        # 2. 工具列與清單動作圖示
        self.open_action.setIcon(
            create_icon("open_file", t.icon_normal, disabled_color=t.icon_disabled, size=18)
        )
        self.open_folder_action.setIcon(
            create_icon("open_folder", t.icon_normal, disabled_color=t.icon_disabled, size=18)
        )
        self.toggle_playlist_action.setIcon(
            create_icon(
                "playlist",
                t.icon_normal,
                disabled_color=t.icon_disabled,
                active_color=t.accent,
                size=18,
            )
        )
        theme_icon_name = "sun" if t.is_dark else "moon"
        self.toggle_theme_action.setIcon(
            create_icon(theme_icon_name, t.icon_normal, size=18)
        )
        self.toggle_theme_action.setText("淺色模式" if t.is_dark else "深色模式")

        self.add_files_action.setIcon(create_icon("add", t.icon_normal, size=16))
        self.remove_item_action.setIcon(create_icon("remove", t.icon_normal, size=16))
        self.clear_list_action.setIcon(create_icon("clear", t.icon_normal, size=16))
        self.dock_close_button.setIcon(create_icon("close", t.text_secondary, size=14))

        # 3. 底部控制列按鈕圖示
        self.prev_button.setIcon(
            create_icon("prev", t.icon_normal, disabled_color=t.icon_disabled, size=18)
        )
        self.next_button.setIcon(
            create_icon("next", t.icon_normal, disabled_color=t.icon_disabled, size=18)
        )
        self.stop_button.setIcon(
            create_icon("stop", t.icon_normal, disabled_color=t.icon_disabled, size=18)
        )
        self.shuffle_button.setIcon(
            create_icon(
                "shuffle",
                t.icon_normal,
                disabled_color=t.icon_disabled,
                active_color=t.accent,
                size=18,
            )
        )
        self.fullscreen_button.setIcon(
            self._icon_exit_fs if self.isFullScreen() else self._icon_fs
        )

        # 4. 更新動態狀態圖示與空狀態引導頁
        self._apply_repeat_button_ui(self.playlist.repeat_mode)
        self._update_volume_icon(self.volume_slider.value(), self.is_muted)
        self._update_ui_state(self.media_player.playbackState())
        self.empty_state_widget.apply_theme(t.accent, t.icon_normal)

    # --------------------------------------------------------------------------
    # 公開功能
    # --------------------------------------------------------------------------

    def _get_default_video_dir(self) -> str:
        """取得系統預設影片目錄。"""
        video_dirs = QStandardPaths.standardLocations(
            QStandardPaths.StandardLocation.MoviesLocation
        )
        return video_dirs[0] if video_dirs else os.path.expanduser("~")

    def open_file_dialog(self) -> None:
        """開啟單一影片檔案選擇對話框。"""
        exts_str = " ".join(f"*{ext}" for ext in Config.SUPPORTED_VIDEO_FORMATS)
        path, _ = QFileDialog.getOpenFileName(
            self,
            "開啟影片",
            self._get_default_video_dir(),
            f"影片檔案 ({exts_str});;所有檔案 (*.*)",
        )
        if path:
            norm = normalize_path(path)
            self.playlist.scan_folder(os.path.dirname(norm))
            self._sync_playlist_widget()
            self.load_video(norm)

    def open_folder_dialog(self) -> None:
        """開啟資料夾並載入所有支援影片。"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "開啟資料夾", self._get_default_video_dir()
        )
        if dir_path:
            files = self.playlist.scan_folder(dir_path)
            self._sync_playlist_widget()
            if files:
                self.load_video(files[0])

    def load_video(self, path: str) -> None:
        """載入並播放指定的影片路徑（保留目前的播放倍速）。"""
        norm = normalize_path(path)
        self.current_path = norm
        self.canvas_stack.setCurrentIndex(1)

        self.media_player.setSource(QUrl.fromLocalFile(norm))
        self._apply_current_playback_rate()
        self.media_player.play()

        filename = os.path.basename(norm)
        self.setWindowTitle(f"{filename} - {Config.APP_TITLE}")
        self.header_file_label.setText(filename)
        self.status_bar.showMessage(f"正在播放: {filename}")
        self._update_ui_state(QMediaPlayer.PlaybackState.PlayingState)

        index = self.playlist.set_current_path(norm)
        if index != -1:
            self.playlist_widget.setCurrentRow(index)

    def toggle_play_pause(self) -> None:
        """切換播放或暫停。"""
        state = self.media_player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        elif state in (
            QMediaPlayer.PlaybackState.PausedState,
            QMediaPlayer.PlaybackState.StoppedState,
        ):
            if (
                state == QMediaPlayer.PlaybackState.StoppedState
                and self.media_player.mediaStatus() == QMediaPlayer.MediaStatus.EndOfMedia
            ):
                self.media_player.setPosition(0)
            self.media_player.play()

    def toggle_fullscreen(self) -> None:
        """切換無邊框全螢幕模式，並同步隱藏/恢復周邊工具列與清單面板。"""
        if self.isFullScreen():
            self.showNormal()
            self.header_toolbar.setVisible(True)
            self.status_bar.setVisible(True)
            self.playlist_dock.setVisible(self._dock_was_visible_before_fullscreen)
            self.fullscreen_button.setIcon(self._icon_fs)
        else:
            self._dock_was_visible_before_fullscreen = self.playlist_dock.isVisible()
            self.header_toolbar.setVisible(False)
            self.status_bar.setVisible(False)
            self.playlist_dock.setVisible(False)
            self.fullscreen_button.setIcon(self._icon_exit_fs)
            self.showFullScreen()

    # --------------------------------------------------------------------------
    # 訊號處理槽 (Slots)
    # --------------------------------------------------------------------------

    @pyqtSlot("qint64")
    def _on_position_changed(self, position_ms: int) -> None:
        if not self._is_slider_pressed:
            self.seek_slider.setValue(position_ms)
        self._update_time_label(position_ms, self.media_player.duration())

    @pyqtSlot("qint64")
    def _on_duration_changed(self, duration_ms: int) -> None:
        self.seek_slider.setRange(0, max(0, duration_ms))
        self._update_time_label(self.media_player.position(), duration_ms)

    @pyqtSlot(QMediaPlayer.PlaybackState)
    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        self._update_ui_state(state)

    @pyqtSlot(QMediaPlayer.MediaStatus)
    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        """僅在媒體真正播放結束時觸發下一首，避免手動停止誤觸發。"""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._play_next()

    @pyqtSlot()
    def _on_stop_clicked(self) -> None:
        self.media_player.stop()

    @pyqtSlot(int)
    def _on_volume_changed(self, value: int) -> None:
        self.audio_output.setVolume(value / 100.0)

        if self.is_muted and value > 0:
            self.is_muted = False
            self.audio_output.setMuted(False)
        elif value == 0 and not self.is_muted:
            self.is_muted = True
            self.audio_output.setMuted(True)

        self._update_volume_icon(value, self.is_muted)

    @pyqtSlot()
    def _on_slider_pressed(self) -> None:
        self._is_slider_pressed = True

    @pyqtSlot(int)
    def _on_slider_moved(self, position_ms: int) -> None:
        self._update_time_label(position_ms, self.media_player.duration())

    @pyqtSlot()
    def _on_slider_released(self) -> None:
        if self._is_slider_pressed:
            self.media_player.setPosition(self.seek_slider.value())
        self._is_slider_pressed = False

    @pyqtSlot(int)
    def _on_seek_clicked(self, position_ms: int) -> None:
        self.media_player.setPosition(position_ms)

    @pyqtSlot(QListWidgetItem)
    def _on_playlist_item_double_clicked(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.load_video(path)

    @pyqtSlot()
    def _on_add_files(self) -> None:
        exts_str = " ".join(f"*{ext}" for ext in Config.SUPPORTED_VIDEO_FORMATS)
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "新增影片到清單",
            self._get_default_video_dir(),
            f"影片檔案 ({exts_str});;所有檔案 (*.*)",
        )
        if not paths:
            return

        added = self.playlist.add_files(paths)
        if added:
            self._sync_playlist_widget()
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.StoppedState:
                self.load_video(added[0])

    @pyqtSlot()
    def _on_remove_items(self) -> None:
        selected_items = self.playlist_widget.selectedItems()
        if not selected_items:
            return

        rows = [self.playlist_widget.row(item) for item in selected_items]
        current_removed = self.playlist.remove_indices(rows)
        self._sync_playlist_widget()

        if current_removed:
            self._reset_to_empty_state()

    @pyqtSlot()
    def _on_clear_list(self) -> None:
        self.playlist.clear()
        self._sync_playlist_widget()
        self._reset_to_empty_state()

    @pyqtSlot()
    def _on_repeat_toggled(self) -> None:
        mode = self.playlist.cycle_repeat_mode()
        self._apply_repeat_button_ui(mode)

    @pyqtSlot(bool)
    def _on_shuffle_toggled(self, checked: bool) -> None:
        self.playlist.set_shuffle(checked)
        self.shuffle_button.setToolTip(f"隨機播放: {'開' if checked else '關'}")
        self._sync_playlist_widget()

    @pyqtSlot(QPoint)
    def _show_video_context_menu(self, pos: QPoint) -> None:
        if self.media_player.source().isNull():
            return

        menu = QMenu(self)
        state = self.media_player.playbackState()
        play_text = "暫停" if state == QMediaPlayer.PlaybackState.PlayingState else "播放"
        play_action = QAction(play_text, self)
        play_action.triggered.connect(self.toggle_play_pause)
        menu.addAction(play_action)

        self.mute_action.setText("取消靜音" if self.is_muted else "靜音")
        menu.addAction(self.mute_action)

        fs_text = "退出全螢幕" if self.isFullScreen() else "全螢幕"
        fs_action = QAction(fs_text, self)
        fs_action.triggered.connect(self.toggle_fullscreen)
        menu.addAction(fs_action)

        menu.addSeparator()
        menu.addAction(self.seek_forward_action)
        menu.addAction(self.seek_backward_action)
        menu.addSeparator()
        menu.addAction(self.open_action)

        menu.exec(self.video_widget.mapToGlobal(pos))

    @pyqtSlot(str)
    def _on_rate_changed(self, text: str) -> None:
        self._apply_current_playback_rate(text)

    @pyqtSlot()
    def _toggle_mute(self) -> None:
        self.is_muted = not self.is_muted
        self.audio_output.setMuted(self.is_muted)

        if not self.is_muted and self.volume_slider.value() == 0:
            self.volume_slider.setValue(int(Config.DEFAULT_VOLUME * 100))

        self._update_volume_icon(self.volume_slider.value(), self.is_muted)

    @pyqtSlot()
    def _on_media_error(self) -> None:
        error_string = self.media_player.errorString() or "發生未知的媒體錯誤。"
        logger.warning("媒體播放錯誤: %s", error_string)
        QMessageBox.warning(self, "媒體錯誤", f"無法播放檔案：\n{error_string}")
        self.status_bar.showMessage(f"錯誤: {error_string}", 5000)
        self._update_ui_state(QMediaPlayer.PlaybackState.StoppedState)

    # --------------------------------------------------------------------------
    # 輔助方法
    # --------------------------------------------------------------------------

    def _create_action(
        self,
        text: str,
        shortcut: Optional[Union[str, QKeySequence]],
        slot: Callable[..., object],
        tooltip: Optional[str] = None,
    ) -> QAction:
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        if tooltip:
            action.setToolTip(tooltip)
        action.triggered.connect(slot)
        return action

    def _reset_to_empty_state(self) -> None:
        """停止播放並恢復至空狀態引導畫面。"""
        self.media_player.stop()
        self.media_player.setSource(QUrl())
        self.current_path = None
        self.setWindowTitle(Config.APP_TITLE)
        self.header_file_label.setText("")
        self.time_label.setText("00:00 / 00:00")
        self.seek_slider.setValue(0)
        self.canvas_stack.setCurrentIndex(0)
        self._update_ui_state(QMediaPlayer.PlaybackState.StoppedState)
        self.status_bar.showMessage("準備就緒 — 拖放影片或點擊「開啟影片」開始播放")

    def _apply_current_playback_rate(self, text: Optional[str] = None) -> None:
        rate_text = text if text is not None else self.rate_combo.currentText()
        try:
            rate = float(rate_text.replace("x", ""))
        except ValueError:
            rate = 1.0
        self.media_player.setPlaybackRate(rate)

    def _update_time_label(self, position_ms: int, duration_ms: int) -> None:
        self.time_label.setText(
            f"{format_time(position_ms)} / {format_time(duration_ms)}"
        )

    def _apply_repeat_button_ui(self, mode: RepeatMode) -> None:
        if mode == RepeatMode.NONE:
            self.repeat_button.setToolTip("循環: 關")
            self.repeat_button.setIcon(self._icon_repeat)
            self.repeat_button.setChecked(False)
        elif mode == RepeatMode.ONE:
            self.repeat_button.setToolTip("循環: 單一影片")
            self.repeat_button.setIcon(self._icon_repeat_one)
            self.repeat_button.setChecked(True)
        else:
            self.repeat_button.setToolTip("循環: 全部清單")
            self.repeat_button.setIcon(self._icon_repeat)
            self.repeat_button.setChecked(True)

    def _sync_playlist_widget(self) -> None:
        """依據 PlaylistManager 同步播放清單 UI 與計數徽章。"""
        self.playlist_widget.clear()
        for path in self.playlist.files:
            item = QListWidgetItem(os.path.basename(path))
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setToolTip(path)
            self.playlist_widget.addItem(item)

        self.playlist_count_badge.setText(str(len(self.playlist.files)))

        if 0 <= self.playlist.current_index < self.playlist_widget.count():
            self.playlist_widget.setCurrentRow(self.playlist.current_index)
        self._update_playlist_nav_buttons()

    def _update_playlist_nav_buttons(self) -> None:
        """依據清單數量更新上一首/下一首按鈕啟用狀態。"""
        has_playlist = len(self.playlist.files) > 0
        self.prev_button.setEnabled(has_playlist)
        self.next_button.setEnabled(has_playlist)

    def _update_ui_state(self, state: QMediaPlayer.PlaybackState) -> None:
        has_media = self.media_player.source().isValid()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_pause_button.setIcon(self._icon_pause)
            self.play_pause_button.setToolTip("暫停 (Space)")
        else:
            self.play_pause_button.setIcon(self._icon_play)
            self.play_pause_button.setToolTip("播放 (Space)")

        self.play_pause_button.setEnabled(has_media)
        self.stop_button.setEnabled(has_media)
        self.seek_slider.setEnabled(has_media)
        self.rate_combo.setEnabled(has_media)
        self._update_playlist_nav_buttons()

    @pyqtSlot()
    def _play_next(self) -> None:
        next_path = self.playlist.get_next_path()
        if next_path is None:
            self.media_player.stop()
            return

        if self.playlist.repeat_mode == RepeatMode.ONE and next_path == self.current_path:
            self.media_player.setPosition(0)
            self.media_player.play()
        else:
            self.load_video(next_path)

    @pyqtSlot()
    def _play_previous(self) -> None:
        prev_path = self.playlist.get_previous_path()
        if prev_path is None:
            return

        if self.playlist.repeat_mode == RepeatMode.ONE and prev_path == self.current_path:
            self.media_player.setPosition(0)
            self.media_player.play()
        else:
            self.load_video(prev_path)

    @pyqtSlot()
    def _seek_forward(self) -> None:
        dur = self.media_player.duration()
        new_pos = self.media_player.position() + Config.SEEK_STEP_MS
        if dur > 0:
            new_pos = min(dur, new_pos)
        self.media_player.setPosition(new_pos)

    @pyqtSlot()
    def _seek_backward(self) -> None:
        new_pos = max(0, self.media_player.position() - Config.SEEK_STEP_MS)
        self.media_player.setPosition(new_pos)

    def _change_volume(self, delta: int) -> None:
        new_vol = max(0, min(100, self.volume_slider.value() + delta))
        self.volume_slider.setValue(new_vol)

    def _update_volume_icon(self, value: int, is_muted: bool) -> None:
        muted = is_muted or value == 0
        self.volume_button.setIcon(self._icon_muted if muted else self._icon_vol)
        self.volume_button.setToolTip("取消靜音 (M)" if muted else "靜音 (M)")

    # --------------------------------------------------------------------------
    # 事件處理與設定持久化
    # --------------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """全域快捷鍵處理（避開輸入與清單焦點衝突）。"""
        key = event.key()
        focused_widget = QApplication.focusWidget()

        if isinstance(focused_widget, (QListWidget, QComboBox)):
            if isinstance(focused_widget, QListWidget) and key == Qt.Key.Key_Delete:
                self._on_remove_items()
                event.accept()
                return
            super().keyPressEvent(event)
            return

        if event.modifiers() == Qt.KeyboardModifier.NoModifier:
            if key == Qt.Key.Key_Space:
                self.toggle_play_pause()
                return
            if key == Qt.Key.Key_M:
                self._toggle_mute()
                return
            if key == Qt.Key.Key_Left:
                self._seek_backward()
                return
            if key == Qt.Key.Key_Right:
                self._seek_forward()
                return
            if key == Qt.Key.Key_Up:
                self._change_volume(Config.VOLUME_STEP)
                return
            if key == Qt.Key.Key_Down:
                self._change_volume(-Config.VOLUME_STEP)
                return
            if key == Qt.Key.Key_F11:
                self.toggle_fullscreen()
                return
            if key == Qt.Key.Key_Escape and self.isFullScreen():
                self.toggle_fullscreen()
                return

        super().keyPressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """僅在拖曳項目包含資料夾或支援的影片檔案時接受。"""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                local = url.toLocalFile()
                if os.path.isdir(local) or (
                    os.path.isfile(local) and is_supported_video(local)
                ):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event: QDropEvent) -> None:
        """支援拖放資料夾或單一/多個影片檔案。"""
        urls = event.mimeData().urls()
        if not urls:
            return

        local_paths = [normalize_path(u.toLocalFile()) for u in urls if u.toLocalFile()]
        video_files = [
            p for p in local_paths if os.path.isfile(p) and is_supported_video(p)
        ]

        if len(video_files) == 1 and len(local_paths) == 1:
            self.playlist.scan_folder(os.path.dirname(video_files[0]))
            self._sync_playlist_widget()
            self.load_video(video_files[0])
            return

        if video_files:
            added = self.playlist.add_files(video_files)
            self._sync_playlist_widget()
            if added:
                self.load_video(added[0])
            return

        for p in local_paths:
            if os.path.isdir(p):
                files = self.playlist.scan_folder(p)
                self._sync_playlist_widget()
                if files:
                    self.load_video(files[0])
                break

    def closeEvent(self, event: QCloseEvent) -> None:
        """關閉視窗時停止播放並保存應用程式設定。"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("volume", self.audio_output.volume())
        self.settings.setValue("isMuted", self.is_muted)
        self.settings.setValue("repeatMode", int(self.playlist.repeat_mode))
        self.settings.setValue("shuffleEnabled", self.playlist.shuffle_enabled)
        self.settings.setValue("isDarkTheme", self.theme_manager.is_dark)

        self.media_player.stop()
        event.accept()

    def load_settings(self) -> None:
        """載入上次儲存的使用者設定。"""
        if geometry := self.settings.value("geometry"):
            self.restoreGeometry(geometry)
        if state := self.settings.value("windowState"):
            self.restoreState(state)

        is_dark = self.settings.value("isDarkTheme", True, type=bool)
        self.theme_manager.toggle_theme(is_dark=is_dark)

        volume = self.settings.value("volume", Config.DEFAULT_VOLUME, type=float)
        volume = max(0.0, min(1.0, volume))
        self.audio_output.setVolume(volume)
        self.volume_slider.setValue(int(volume * 100))

        self.is_muted = self.settings.value("isMuted", False, type=bool)
        self.audio_output.setMuted(self.is_muted)

        repeat_val = self.settings.value("repeatMode", int(RepeatMode.NONE), type=int)
        self.playlist.repeat_mode = RepeatMode(repeat_val % 3)

        shuffle_val = self.settings.value("shuffleEnabled", False, type=bool)
        self.playlist.shuffle_enabled = shuffle_val
        self.shuffle_button.setChecked(shuffle_val)
        self.shuffle_button.setToolTip(f"隨機播放: {'開' if shuffle_val else '關'}")


def main() -> None:
    """應用程式進入點。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    QApplication.setOrganizationName(Config.ORGANIZATION_NAME)
    QApplication.setApplicationName(Config.APP_NAME)

    app = QApplication(sys.argv)

    if not QT_MULTIMEDIA_AVAILABLE:
        sys.exit(1)

    window = VideoPlayerWindow()
    if getattr(window, "media_player", None):
        window.show()
    else:
        sys.exit(1)

    sys.exit(app.exec())
