# ==============================================================================
# PyQt6 影片播放器 - v1.1.3
#
# 說明：
# 這是一個使用 PyQt6.QtMultimedia 建構的現代影片播放器。
#
# v1.1.3 更新日誌:
# - [修正] 修正 v1.1.2 中 create_docks() 仍包含
#           playlist_widget.addAction(self.remove_item_action)
#           導致的 AttributeError。
#           - 該行程式碼已移至 create_toolbars()，確保 action 已被建立。
#
# v1.1.2 更新日誌:
# - [修正] 修正 v1.1.1 中 create_docks() 和 create_actions() 之間的
#           相互依賴錯誤。
#           - create_docks() 現在只建立 UI。
#           - create_toolbars() 現在負責填充 *所有* 工具列 (包含播放清單的)。
#
# v1.1.1 更新日誌:
# - [修正] 修正 v1.1.0 中 create_actions() 比 create_docks() 先調用
#           導致 'playlist_dock' 尚未建立的 AttributeError。
#
# v1.1.0 更新日誌:
# - [新增] 狀態保存 (QSettings): 記住視窗大小/位置和音量。
# - [新增] 播放清單控制: 新增 "新增/移除/清空" 工具列。
# - [新增] 播放控制: 新增 "循環" (3種模式) 和 "隨機" 按鈕。
# - [新增] 自動播放: 影片結束時根據 循環/隨機 設定播放下一首。
# - [修正] 修正 v1.0.0 中 QT_MULTIMEDIA_AVAILABLE 的拼寫錯誤。
# - [修正] 修正拖曳資料夾無法正確載入的問題。
#
# ==============================================================================

import sys
import os
import random
from typing import Optional, List

# 核心 PyQt6 模組
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QToolBar, QStatusBar,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem, QDockWidget,
    QPushButton, QSlider, QLabel, QHBoxLayout, QVBoxLayout,
    QStyle, QAbstractItemView
)
from PyQt6.QtGui import (
    QAction, QIcon, QKeySequence, QPalette, QColor, QCloseEvent
)
from PyQt6.QtCore import (
    Qt, QSize, QUrl, QTimer, QStandardPaths, pyqtSlot, QSettings
)

# 關鍵的 QtMultimedia 模組
try:
    from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PyQt6.QtMultimediaWidgets import QVideoWidget
    QT_MULTIMEDIA_AVAILABLE = True
except ImportError:
    print("錯誤：找不到 PyQt6.QtMultimedia 或 QtMultimediaWidgets 模組。")
    print("請確保 PyQt6 已正確安裝： pip install PyQt6")
    QT_MULTIMEDIA_AVAILABLE = False


# ==============================================================================
# 1. 設定類別 (Config)
# ==============================================================================
class Config:
    """集中管理應用程式的所有設定。"""
    APP_TITLE: str = "PyQt6 影片播放器 v1.1.3"
    ORGANIZATION_NAME: str = "MyVideoPlayer" # 用於 QSettings
    APP_NAME: str = "PyQt6VideoPlayer"    # 用於 QSettings
    DEFAULT_WINDOW_SIZE: QSize = QSize(1000, 700)
    DEFAULT_VOLUME: float = 0.8  # 0.0 到 1.0
    # 支援的影片格式 (小寫)
    SUPPORTED_VIDEO_FORMATS: tuple = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv')
    SEEK_SLIDER_PRECISION: int = 1000 # 進度條的精細度

# ==============================================================================
# 2. 主題管理器 (ThemeManager)
# ==============================================================================
class ThemeManager:
    """管理應用程式的深色/淺色主題。"""
    def __init__(self, app: QApplication):
        self.app = app
        self.is_dark = False

    def toggle_theme(self, is_dark: Optional[bool] = None):
        """切換或設定指定的主題模式。"""
        self.is_dark = not self.is_dark if is_dark is None else is_dark
        if self.is_dark:
            self._apply_dark_palette()
            self.app.setStyleSheet(self._get_modern_dark_stylesheet())
        else:
            self.app.setPalette(self.app.style().standardPalette())
            self.app.setStyleSheet("")

    def _apply_dark_palette(self):
        """套用深色調色板。"""
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(37, 37, 37))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        self.app.setPalette(dark_palette)

    def _get_modern_dark_stylesheet(self) -> str:
        """返回深色主題的 QSS 樣式表。"""
        # [v1.1] 為播放清單的 QToolBar 添加樣式
        return """
        QWidget {
            color: #dcdcdc;
            font-family: 'Segoe UI', 'Microsoft JhengHei', 'Helvetica', sans-serif;
        }
        QMainWindow { background-color: #252525; }
        QDialog { background-color: #252525; }

        /* === 影片畫布 === */
        QVideoWidget {
            background-color: #000000; /* 影片背景為純黑 */
        }

        /* === Dock (播放清單) === */
        QDockWidget::title {
            background-color: #333333;
            padding: 8px;
            font-weight: bold;
        }
        QDockWidget > QWidget {
            border: 1px solid #3c3c3c;
        }
        /* [v1.1] 播放清單的工具列 */
        QDockWidget QToolBar {
            background-color: #2c2c2c;
            border-bottom: 1px solid #3c3c3c;
            padding: 2px;
        }

        QListWidget {
            background-color: #2c2c2c;
            border: none;
            padding: 5px;
        }
        QListWidget::item:hover { background-color: #383838; }
        QListWidget::item:selected {
            background-color: #0078d7;
            color: #ffffff;
        }

        /* === 按鈕 === */
        QPushButton {
            background-color: #3e3e3e;
            border: 1px solid #555555;
            padding: 8px;
            border-radius: 4px;
        }
        QPushButton:hover { background-color: #4a4a4a; }
        QPushButton:pressed { background-color: #333333; }
        QPushButton:disabled {
            background-color: #303030;
            color: #777777;
        }
        /* [v1.1] 可選中的按鈕 (循環/隨機) */
        QPushButton:checkable:checked {
            background-color: #0078d7;
            border-color: #005a9e;
        }
        QPushButton:checkable:hover:!checked {
             background-color: #4a4a4a;
        }

        /* === Sliders (進度條 & 音量) === */
        QSlider {
            height: 20px; /* 增加點擊區域 */
        }
        QSlider::groove:horizontal {
            height: 6px;
            background: #444444;
            margin: 2px 0;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #0078d7;
            border: 1px solid #0078d7;
            width: 14px;
            height: 14px;
            margin: -4px 0; /* 垂直居中 */
            border-radius: 7px;
        }
        QSlider::add-page:horizontal {
            background: #444444; /* 尚未播放的部分 */
        }
        QSlider::sub-page:horizontal {
            background: #0078d7; /* 已播放的部分 */
        }

        /* === 狀態列、選單列、工具列 === */
        QStatusBar, QToolBar, QMenuBar {
            background-color: #2d2d2d;
            border: none;
            padding: 4px;
        }
        QMenu {
            background-color: #2c2c2c;
            border: 1px solid #444444;
        }
        QMenu::item:selected { background-color: #0078d7; }
        """

# ==============================================================================
# 3. 主視窗 (VideoPlayerWindow)
# ==============================================================================
class VideoPlayerWindow(QMainWindow):
    """影片播放器的主視窗。"""

    def __init__(self) -> None:
        super().__init__()

        # 檢查 QtMultimedia 是否可用
        if not QT_MULTIMEDIA_AVAILABLE:
            QMessageBox.critical(
                self, "缺少模組",
                "找不到 PyQt6.QtMultimedia 或 QtMultimediaWidgets 模組。\n"
                "請確保已安裝 `PyQt6`。\n"
                "應用程式即將退出。"
            )
            QTimer.singleShot(100, self.close) # 延遲退出以顯示訊息
            return

        # [v1.1] 初始化 QSettings
        self.settings = QSettings(Config.ORGANIZATION_NAME, Config.APP_NAME)

        self.setWindowTitle(Config.APP_TITLE)
        # 幾何資訊將由 load_settings 恢復
        # self.setGeometry(100, 100, Config.DEFAULT_WINDOW_SIZE.width(), Config.DEFAULT_WINDOW_SIZE.height())
        self.setAcceptDrops(True) # 允許拖曳檔案

        self.theme_manager = ThemeManager(QApplication.instance())
        self.theme_manager.toggle_theme(is_dark=True) # 預設啟用深色主題

        self.current_path: Optional[str] = None
        self.playlist_files: List[str] = []
        self.current_playlist_index: int = -1 # [v1.1] 追蹤目前播放索引
        self._is_slider_pressed: bool = False

        # [v1.1] 播放狀態屬性
        self.repeat_mode: int = 0  # 0: 不循環, 1: 單一循環, 2: 清單循環
        self.shuffle_enabled: bool = False

        # 1. 建立核心媒體元件
        self.video_widget = QVideoWidget()
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()

        # 2. 關鍵連結：將播放器、音訊和影片畫布連結起來
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setAudioOutput(self.audio_output)

        # 音量將由 load_settings 設定
        # self.audio_output.setVolume(Config.DEFAULT_VOLUME)

        # 3. 建立 UI
        # [v1.1.2 修正] 調整初始化順序以解決依賴問題
        self.create_docks() # [v1.1] 必須先建立 Docks (playlist_dock, playlist_toolbar)
        self.create_actions() # [v1.1] 接著建立 Actions (add_files_action 等)
        self.create_toolbars() # [v1.1] 最後填充所有 Toolbars (包含 playlist_toolbar 和 playlist_widget 的 actions)
        self.create_controls_bar() # [v1.1] 建立主控制列

        # 4. 建立狀態列
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("準備就緒。請開啟影片檔案。")

        # 5. 連接所有訊號
        self.connect_signals()

        self._update_ui_state(QMediaPlayer.PlaybackState.StoppedState)

        # 6. [v1.1] 載入上次的設定
        self.load_settings()

    def create_actions(self) -> None:
        """建立選單和工具列的 QAction"""
        self.open_action = self._create_action(
            "開啟影片...", "document-open", QKeySequence.StandardKey.Open, self.open_file_dialog
        )
        self.open_folder_action = self._create_action(
            "開啟資料夾...", "folder-open", "Ctrl+Shift+O", self.open_folder_dialog
        )
        self.exit_action = self._create_action(
            "離開", "application-exit", QKeySequence.StandardKey.Quit, self.close
        )
        self.toggle_playlist_action = QAction("切換播放清單", self)
        # [v1.1.1 修正] 連接到 self.playlist_dock (現在已存在)
        self.toggle_playlist_action.triggered.connect(self.playlist_dock.toggleViewAction)
        self.toggle_theme_action = self._create_action(
            "切換主題", "preferences-desktop-theme", "Ctrl+T", self.theme_manager.toggle_theme
        )

        # [v1.1] 播放清單動作
        self.add_files_action = self._create_action(
            "新增檔案", "list-add", None, self._on_add_files
        )
        self.remove_item_action = self._create_action(
            "移除選中", "list-remove", QKeySequence.StandardKey.Delete, self._on_remove_items
        )
        self.clear_list_action = self._create_action(
            "清空清單", "edit-clear", None, self._on_clear_list
        )

    def create_toolbars(self) -> None:
        """建立頂部工具列，並填充所有工具列和 UI 動作"""
        file_toolbar = self.addToolBar("檔案")
        file_toolbar.setIconSize(QSize(20, 20))
        file_toolbar.addActions([self.open_action, self.open_folder_action])

        view_toolbar = self.addToolBar("檢視")
        view_toolbar.setIconSize(QSize(20, 20))
        view_toolbar.addActions([self.toggle_playlist_action, self.toggle_theme_action])

        # [v1.1.2] 填充播放清單工具列的邏輯移到這裡
        # 因為此時 self.playlist_toolbar 和 self.add_files_action 都已存在
        self.playlist_toolbar.addActions([self.add_files_action, self.remove_item_action, self.clear_list_action])

        # [v1.1.3] 將 playlist_widget 的 addAction 移到這裡
        # 因為此時 self.playlist_widget 和 self.remove_item_action 都已存在
        self.playlist_widget.addAction(self.remove_item_action) # [v1.1] 允許按 Del 鍵刪除


    def create_docks(self) -> None:
        """建立可停靠的播放清單 (v1.1 帶有工具列)"""
        self.playlist_dock = QDockWidget("播放清單", self)
        
        # 建立一個容器 Widget
        playlist_container = QWidget()
        layout = QVBoxLayout(playlist_container)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        # 1. [v1.1] 建立播放清單工具列
        self.playlist_toolbar = QToolBar("播放清單工具列")
        self.playlist_toolbar.setIconSize(QSize(18, 18))
        # [v1.1.2] 移除 addActions，移至 create_toolbars()
        layout.addWidget(self.playlist_toolbar)

        # 2. 建立 QListWidget
        self.playlist_widget = QListWidget()
        self.playlist_widget.itemDoubleClicked.connect(self._on_playlist_item_double_clicked)
        # [v1.1] 允許多選
        self.playlist_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        # [v1.1.3] 移除 addAction，移至 create_toolbars()
        # self.playlist_widget.addAction(self.remove_item_action) 
        layout.addWidget(self.playlist_widget, 1) # 佔據剩餘空間

        self.playlist_dock.setWidget(playlist_container)
        self.playlist_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.playlist_dock)
        self.playlist_dock.setVisible(True)

    def create_controls_bar(self) -> None:
        """建立底部的播放控制列 (v1.1 帶有循環/隨機)"""
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.video_widget, 1)

        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(5, 5, 5, 5)
        controls_layout.setSpacing(5)

        # 1. 進度條
        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, Config.SEEK_SLIDER_PRECISION)
        controls_layout.addWidget(self.seek_slider)

        # 2. 按鈕和標籤列
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        # 播放/暫停 按鈕
        self.play_pause_button = QPushButton()
        self.play_pause_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        buttons_layout.addWidget(self.play_pause_button)

        # 停止 按鈕
        self.stop_button = QPushButton()
        self.stop_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.stop_button.clicked.connect(self._on_stop_clicked)
        buttons_layout.addWidget(self.stop_button)

        # 時間標籤
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setFixedWidth(90)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        buttons_layout.addWidget(self.time_label)
        
        buttons_layout.addSpacing(10)

        # [v1.1] 循環 按鈕
        self.repeat_button = QPushButton()
        self.repeat_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.repeat_button.setCheckable(True)
        self.repeat_button.setToolTip("循環: 關")
        self.repeat_button.setFixedSize(28, 28) # 統一樣式
        self.repeat_button.clicked.connect(self._on_repeat_toggled)
        buttons_layout.addWidget(self.repeat_button)

        # [v1.1] 隨機 按鈕
        self.shuffle_button = QPushButton()
        # (v1.2 待辦: 尋找更好的圖示)
        self.shuffle_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipForward)) 
        self.shuffle_button.setCheckable(True)
        self.shuffle_button.setToolTip("隨機播放: 關")
        self.shuffle_button.setFixedSize(28, 28) # 統一樣式
        self.shuffle_button.clicked.connect(self._on_shuffle_toggled)
        buttons_layout.addWidget(self.shuffle_button)


        buttons_layout.addStretch(1) # 彈性空間

        # 音量圖示
        self.volume_label_icon = QLabel()
        self.volume_label_icon.setPixmap(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume).pixmap(QSize(20, 20)))
        buttons_layout.addWidget(self.volume_label_icon)

        # 音量條
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        # self.volume_slider.setValue(int(Config.DEFAULT_VOLUME * 100)) # [v1.1] 由 load_settings 設定
        self.volume_slider.setFixedWidth(120)
        buttons_layout.addWidget(self.volume_slider)

        # 全螢幕 按鈕
        self.fullscreen_button = QPushButton()
        self.fullscreen_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarMaxButton)) # [v1.1] 更好看的圖示
        self.fullscreen_button.setToolTip("切換全螢幕 (F11)")
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        buttons_layout.addWidget(self.fullscreen_button)

        controls_layout.addLayout(buttons_layout)
        
        main_layout.addWidget(controls_widget, 0)

        main_wrapper_widget = QWidget()
        main_wrapper_widget.setLayout(main_layout)
        self.setCentralWidget(main_wrapper_widget)

    def connect_signals(self) -> None:
        """連接所有 QMediaPlayer 和 UI 的訊號"""
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.media_player.errorOccurred.connect(self._on_media_error)

        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)

        self.seek_slider.sliderPressed.connect(self._on_slider_pressed)
        self.seek_slider.sliderMoved.connect(self._on_slider_moved)
        self.seek_slider.sliderReleased.connect(self._on_slider_released)

    # --------------------------------------------------------------------------
    # 核心功能 (Public Methods)
    # --------------------------------------------------------------------------

    def open_file_dialog(self) -> None:
        """開啟檔案選擇對話框"""
        video_dir = QStandardPaths.standardLocations(QStandardPaths.StandardLocation.MoviesLocation)
        start_dir = video_dir[0] if video_dir else os.path.expanduser("~")
        
        exts_str = " ".join([f"*{ext}" for ext in Config.SUPPORTED_VIDEO_FORMATS])
        path, _ = QFileDialog.getOpenFileName(
            self, "開啟影片", start_dir, f"影片檔案 ({exts_str});;所有檔案 (*.*)"
        )
        if path:
            self._scan_folder_for_playlist(os.path.dirname(path))
            # [v1.1] 載入選中的影片，而不是清單第一個
            self.load_video(path)

    def open_folder_dialog(self) -> None:
        """開啟資料夾並將所有影片載入播放清單"""
        video_dir = QStandardPaths.standardLocations(QStandardPaths.StandardLocation.MoviesLocation)
        start_dir = video_dir[0] if video_dir else os.path.expanduser("~")
        
        dir_path = QFileDialog.getExistingDirectory(self, "開啟資料夾", start_dir)
        if dir_path:
            self._scan_folder_for_playlist(dir_path)
            if self.playlist_files:
                # [v1.1] 載入清單第一個 (並設定索引)
                self.current_playlist_index = 0
                self.load_video(self.playlist_files[0])
                self.playlist_widget.setCurrentRow(0)

    def load_video(self, path: str) -> None:
        """載入並播放指定的影片路徑"""
        self.current_path = path
        self.media_player.setSource(QUrl.fromLocalFile(path))
        self.media_player.play()
        self.setWindowTitle(f"{os.path.basename(path)} - {Config.APP_TITLE}")
        self.status_bar.showMessage(f"正在播放: {os.path.basename(path)}")
        self._update_ui_state(QMediaPlayer.PlaybackState.PlayingState)
        
        # [v1.1] 更新播放清單索引
        if path in self.playlist_files:
            self.current_playlist_index = self.playlist_files.index(path)
            self.playlist_widget.setCurrentRow(self.current_playlist_index)
        else:
            self.current_playlist_index = -1 # 不在清單中

    def toggle_play_pause(self) -> None:
        """切換播放或暫停"""
        state = self.media_player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        elif state == QMediaPlayer.PlaybackState.PausedState or state == QMediaPlayer.PlaybackState.StoppedState:
            # 如果已停止 (播放完畢)，重新播放
            if state == QMediaPlayer.PlaybackState.StoppedState and self.media_player.position() == self.media_player.duration():
                self.media_player.setPosition(0)
            self.media_player.play()

    def toggle_fullscreen(self) -> None:
        """切換全螢幕"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
            
    # --------------------------------------------------------------------------
    # 訊號處理槽 (Slots)
    # --------------------------------------------------------------------------

    @pyqtSlot('qint64')
    def _on_position_changed(self, position_ms: int) -> None:
        """(MediaPlayer) 播放位置改變時呼叫"""
        if not self._is_slider_pressed:
            self.seek_slider.setValue(position_ms)
        duration_ms = self.media_player.duration()
        self.time_label.setText(
            f"{self._format_time(position_ms)} / {self._format_time(duration_ms)}"
        )

    @pyqtSlot('qint64')
    def _on_duration_changed(self, duration_ms: int) -> None:
        """(MediaPlayer) 影片總長度載入完成時呼叫"""
        self.seek_slider.setRange(0, duration_ms)
        position_ms = self.media_player.position()
        self.time_label.setText(
            f"{self._format_time(position_ms)} / {self._format_time(duration_ms)}"
        )

    @pyqtSlot(QMediaPlayer.PlaybackState)
    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        """(MediaPlayer) 播放狀態改變時呼叫 (播放、暫停、停止)"""
        self._update_ui_state(state)

        # [v1.1] 處理自動播放
        # 檢查是否是 "自然" 停止 (非使用者點擊 stop)
        if state == QMediaPlayer.PlaybackState.StoppedState:
            # 檢查是否播放到結尾 (允許一點誤差)
            pos = self.media_player.position()
            dur = self.media_player.duration()
            if dur > 0 and pos >= dur - 100: # 接近或等於結尾
                self._play_next()

    @pyqtSlot()
    def _on_stop_clicked(self) -> None:
        self.media_player.stop()

    @pyqtSlot(int)
    def _on_volume_changed(self, value: int) -> None:
        """(UI) 音量條被拖動時"""
        volume = value / 100.0
        self.audio_output.setVolume(volume)
        if value == 0:
            icon = QStyle.StandardPixmap.SP_MediaVolumeMuted
        else:
            icon = QStyle.StandardPixmap.SP_MediaVolume
        self.volume_label_icon.setPixmap(self.style().standardIcon(icon).pixmap(QSize(20, 20)))

    # --- 進度條拖動處理 ---
    @pyqtSlot()
    def _on_slider_pressed(self) -> None:
        self._is_slider_pressed = True

    @pyqtSlot(int)
    def _on_slider_moved(self, position_ms: int) -> None:
        duration_ms = self.media_player.duration()
        self.time_label.setText(
            f"{self._format_time(position_ms)} / {self._format_time(duration_ms)}"
        )
        
    @pyqtSlot()
    def _on_slider_released(self) -> None:
        if self._is_slider_pressed:
            self.media_player.setPosition(self.seek_slider.value())
        self._is_slider_pressed = False

    # --- 播放清單處理 (v1.1) ---
    @pyqtSlot(QListWidgetItem)
    def _on_playlist_item_double_clicked(self, item: QListWidgetItem) -> None:
        """(UI) 雙擊播放清單項目時"""
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.current_playlist_index = self.playlist_widget.row(item) # [v1.1] 更新索引
            self.load_video(path)

    @pyqtSlot()
    def _on_add_files(self) -> None:
        """(UI) [v1.1] "新增檔案" 按鈕點擊"""
        video_dir = QStandardPaths.standardLocations(QStandardPaths.StandardLocation.MoviesLocation)
        start_dir = video_dir[0] if video_dir else os.path.expanduser("~")
        
        exts_str = " ".join([f"*{ext}" for ext in Config.SUPPORTED_VIDEO_FORMATS])
        paths, _ = QFileDialog.getOpenFileNames(
            self, "新增影片到清單", start_dir, f"影片檔案 ({exts_str});;所有檔案 (*.*)"
        )
        
        if paths:
            for path in paths:
                if path not in self.playlist_files:
                    self.playlist_files.append(path)
                    item = QListWidgetItem()
                    item.setText(os.path.basename(path))
                    item.setData(Qt.ItemDataRole.UserRole, path)
                    self.playlist_widget.addItem(item)
            
            # 如果當前沒有播放，自動播放新增的第一個
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.StoppedState:
                self.current_playlist_index = self.playlist_files.index(paths[0])
                self.load_video(paths[0])


    @pyqtSlot()
    def _on_remove_items(self) -> None:
        """(UI) [v1.1] "移除選中" 按鈕點擊 (或 Delete 鍵)"""
        selected_items = self.playlist_widget.selectedItems()
        if not selected_items:
            return

        # 從後往前刪除，避免索引錯亂
        selected_rows = sorted([self.playlist_widget.row(item) for item in selected_items], reverse=True)
        
        for row in selected_rows:
            item = self.playlist_widget.takeItem(row) # 從 QListWidget 移除
            path = item.data(Qt.ItemDataRole.UserRole)
            if path in self.playlist_files:
                self.playlist_files.remove(path) # 從 list 移除
            
            # 如果刪除的是正在播放的影片
            if row == self.current_playlist_index:
                self.media_player.stop()
                self.current_path = None
                self.current_playlist_index = -1
                
            # 如果刪除的項目在當前播放的項目之前，更新索引
            elif row < self.current_playlist_index:
                self.current_playlist_index -= 1

    @pyqtSlot()
    def _on_clear_list(self) -> None:
        """(UI) [v1.1] "清空清單" 按鈕點擊"""
        self.media_player.stop()
        self.playlist_widget.clear()
        self.playlist_files.clear()
        self.current_path = None
        self.current_playlist_index = -1
        self.setWindowTitle(Config.APP_TITLE)

    # --- 播放控制 (v1.1) ---
    
    @pyqtSlot()
    def _on_repeat_toggled(self) -> None:
        """(UI) [v1.1] 循環按鈕點擊 (0->1->2->0)"""
        self.repeat_mode = (self.repeat_mode + 1) % 3
        
        if self.repeat_mode == 0:
            self.repeat_button.setToolTip("循環: 關")
            self.repeat_button.setChecked(False)
        elif self.repeat_mode == 1:
            self.repeat_button.setToolTip("循環: 單一")
            self.repeat_button.setChecked(True)
        else: # self.repeat_mode == 2
            self.repeat_button.setToolTip("循環: 全部")
            self.repeat_button.setChecked(True) # 保持按下的狀態

    @pyqtSlot(bool)
    def _on_shuffle_toggled(self, checked: bool) -> None:
        """(UI) [v1.1] 隨機按鈕點擊"""
        self.shuffle_enabled = checked
        self.shuffle_button.setToolTip(f"隨機播放: {'開' if checked else '關'}")
        
        # (可選) 切換隨機時立即重新排序 (但保留當前播放的)
        if checked and len(self.playlist_files) > 1 and self.current_playlist_index != -1:
            current_path = self.playlist_files.pop(self.current_playlist_index)
            random.shuffle(self.playlist_files)
            self.playlist_files.insert(0, current_path) # 將當前的放回第一位
            self.current_playlist_index = 0
            
            # 重新填充 QListWidget 以匹配順序
            self.playlist_widget.clear()
            for path in self.playlist_files:
                item = QListWidgetItem()
                item.setText(os.path.basename(path))
                item.setData(Qt.ItemDataRole.UserRole, path)
                self.playlist_widget.addItem(item)
            self.playlist_widget.setCurrentRow(self.current_playlist_index)

    # --- 錯誤處理 ---
    @pyqtSlot()
    def _on_media_error(self) -> None:
        """(MediaPlayer) 發生錯誤時"""
        error_string = self.media_player.errorString()
        if not error_string:
            error_string = "發生未知的媒體錯誤。"
            
        QMessageBox.warning(self, "媒體錯誤", f"無法播放檔案：\n{error_string}")
        self.status_bar.showMessage(f"錯誤: {error_string}", 5000)
        self._update_ui_state(QMediaPlayer.PlaybackState.StoppedState)

    # --------------------------------------------------------------------------
    # 輔助方法 (Helper Methods)
    # --------------------------------------------------------------------------

    def _create_action(self, text, icon_name, shortcut, slot) -> QAction:
        """輔助函數：建立 QAction"""
        icon = QIcon.fromTheme(icon_name)
        if icon.isNull():
            try:
                # 將 "document-open" 轉為 "SP_DialogOpenButton"
                pixmap_name = "SP_" + icon_name.replace("-", " ").title().replace(" ", "")
                if "Open" in pixmap_name: pixmap_name = "SP_DialogOpenButton"
                if "Save" in pixmap_name: pixmap_name = "SP_DialogSaveButton"
                if "Exit" in pixmap_name: pixmap_name = "SP_DialogCloseButton"
                if "Theme" in pixmap_name: pixmap_name = "SP_DesktopIcon"
                if "Folder-Open" in pixmap_name: pixmap_name = "SP_DirOpenIcon"
                if "List-Add" in pixmap_name: pixmap_name = "SP_FileDialogNewFolder"
                if "List-Remove" in pixmap_name: pixmap_name = "SP_DialogCancelButton"
                if "Edit-Clear" in pixmap_name: pixmap_name = "SP_DialogResetButton"


                std_icon = getattr(QStyle.StandardPixmap, pixmap_name, QStyle.StandardPixmap.SP_FileIcon)
                icon = self.style().standardIcon(std_icon)
            except Exception:
                icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
                
        action = QAction(icon, text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(slot)
        return action

    def _format_time(self, ms: int) -> str:
        """將毫秒轉換為 MM:SS 格式的字串"""
        if ms < 0: ms = 0
        s = ms // 1000
        m = s // 60
        s = s % 60
        return f"{m:02}:{s:02}"

    def _update_ui_state(self, state: QMediaPlayer.PlaybackState) -> None:
        """根據播放狀態更新 UI (按鈕圖示、啟用狀態)"""
        has_media = self.media_player.source().isValid()

        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_pause_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
            self.play_pause_button.setToolTip("暫停 (Space)")
        else:
            self.play_pause_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
            self.play_pause_button.setToolTip("播放 (Space)")
            
        self.play_pause_button.setEnabled(has_media)
        self.stop_button.setEnabled(has_media)
        self.seek_slider.setEnabled(has_media)

    def _scan_folder_for_playlist(self, dir_path: str) -> None:
        """掃描資料夾並更新播放清單"""
        if not os.path.isdir(dir_path):
            return
            
        self.playlist_widget.clear()
        self.playlist_files.clear()

        try:
            temp_files = []
            for filename in sorted(os.listdir(dir_path)):
                if filename.lower().endswith(Config.SUPPORTED_VIDEO_FORMATS):
                    full_path = os.path.join(dir_path, filename)
                    temp_files.append(full_path)
            
            # [v1.1] 處理隨機
            if self.shuffle_enabled:
                random.shuffle(temp_files)
            
            self.playlist_files = temp_files
            
            # 重新填充
            for path in self.playlist_files:
                item = QListWidgetItem()
                item.setText(os.path.basename(path))
                item.setData(Qt.ItemDataRole.UserRole, path)
                self.playlist_widget.addItem(item)
                    
        except Exception as e:
            print(f"掃描資料夾時出錯: {e}")
            
    def _play_next(self) -> None:
        """[v1.1] 播放清單中的下一個項目"""
        if not self.playlist_files:
            return

        # 1. 檢查單一循環
        if self.repeat_mode == 1: # 單一循環
            self.media_player.setPosition(0)
            self.media_player.play()
            return

        # 2. 決定下一個索引
        next_index = -1
        if self.shuffle_enabled:
            next_index = random.randint(0, len(self.playlist_files) - 1)
        elif self.current_playlist_index < len(self.playlist_files) - 1:
            next_index = self.current_playlist_index + 1
        elif self.repeat_mode == 2: # 清單循環
            next_index = 0

        # 3. 播放
        if next_index != -1:
            self.current_playlist_index = next_index
            path = self.playlist_files[self.current_playlist_index]
            self.load_video(path)
        else:
            # 沒有下一個了 (非循環，且已是最後一首)
            self.media_player.stop()

    # --------------------------------------------------------------------------
    # 事件處理 (Event Handlers)
    # --------------------------------------------------------------------------

    def keyPressEvent(self, event) -> None:
        """全域快捷鍵"""
        key = event.key()
        
        # 檢查焦點是否在 QListWidget 上，如果是，則讓它處理 Delete 鍵
        if key == Qt.Key.Key_Delete and self.playlist_widget.hasFocus():
            self._on_remove_items()
            return

        if key == Qt.Key.Key_Space:
            self.toggle_play_pause()
        elif key == Qt.Key.Key_F11:
            self.toggle_fullscreen()
        elif key == Qt.Key.Key_Escape and self.isFullScreen():
            self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)
            
    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        if (urls := event.mimeData().urls()):
            path = urls[0].toLocalFile()
            if os.path.isfile(path) and path.lower().endswith(Config.SUPPORTED_VIDEO_FORMATS):
                self._scan_folder_for_playlist(os.path.dirname(path))
                self.load_video(path) # 載入拖曳的檔案
            elif os.path.isdir(path):
                 self._scan_folder_for_playlist(path) # [v1.1] 修正
                 if self.playlist_files:
                     self.load_video(self.playlist_files[0]) # 載入第一個

    def closeEvent(self, event: QCloseEvent) -> None:
        """關閉應用程式時確保媒體播放器停止並儲存設定"""
        # [v1.1] 儲存 QSettings
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("volume", self.audio_output.volume())

        self.media_player.stop()
        event.accept()

    def load_settings(self) -> None:
        """[v1.1] 載入 QSettings"""
        if geometry := self.settings.value("geometry"):
            self.restoreGeometry(geometry)
        if state := self.settings.value("windowState"):
            self.restoreState(state)
        
        volume = self.settings.value("volume", Config.DEFAULT_VOLUME, type=float)
        self.audio_output.setVolume(volume)
        self.volume_slider.setValue(int(volume * 100))

# ==============================================================================
# 4. 應用程式入口
# ==============================================================================
def main() -> None:
    """主函式，用於啟動應用程式。"""
    # [v1.1] 確保 QSettings 能正常運作
    QApplication.setOrganizationName(Config.ORGANIZATION_NAME)
    QApplication.setApplicationName(Config.APP_NAME)

    app = QApplication(sys.argv)
    
    # [v1.1] 修正 v1.0 的拼寫錯誤
    if not QT_MULTIMEDIA_AVAILABLE:
        sys.exit(1)

    window = VideoPlayerWindow()
    if getattr(window, 'media_player', None): # 確保 __init__ 成功
        window.show()
    else:
        sys.exit(1) # 如果 __init__ 失敗則退出

    sys.exit(app.exec())

if __name__ == '__main__':
    main()