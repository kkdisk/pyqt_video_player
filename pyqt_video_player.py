# ==============================================================================
# PyQt6 影片播放器 - v1.2.1 (修訂版)
#
# 說明：
# 這是一個使用 PyQt6.QtMultimedia 建構的現代影片播放器。
#
# v1.2.1 修訂日誌:
# - [修正] 快捷鍵焦點: 修正當 QComboBox (播放速度) 或 QListWidget (播放清單)
#   取得焦點時，空白鍵 (Space) 仍會觸發播放/暫停的 Bug。
# - [優化] 圖示處理: 重構 _create_action() 函式，改為使用 QStyle.StandardPixmap
#   以確保圖示的跨平台一致性。
#
# v1.2.0 更新日誌:
# - [新增] 播放速度控制: 新增 QComboBox 以調整 0.5x ~ 2.0x 速度。
# - [新增] 快捷鍵強化 (M, ←/→, ↑/↓)
# - [新增] 影片右鍵選單。
# - [修正] 音量圖示: 圖示現在會正確反映靜音狀態。
# - [修正] 調整音量時會自動取消靜音。
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
    QStyle, QAbstractItemView, QComboBox, QMenu
)
from PyQt6.QtGui import (
    QAction, QIcon, QKeySequence, QPalette, QColor, QCloseEvent
)
from PyQt6.QtCore import (
    Qt, QSize, QUrl, QTimer, QStandardPaths, pyqtSlot, QSettings, QPoint
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
    APP_TITLE: str = "PyQt6 影片播放器 v1.2.1" # [修改 v1.2.1] 更新標題版本
    ORGANIZATION_NAME: str = "MyVideoPlayer" # 用於 QSettings
    APP_NAME: str = "PyQt6VideoPlayer"    # 用於 QSettings
    DEFAULT_WINDOW_SIZE: QSize = QSize(1000, 700)
    DEFAULT_VOLUME: float = 0.7  # 0.0 到 1.0
    # 支援的影片格式 (小寫)
    SUPPORTED_VIDEO_FORMATS: tuple = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv')
    SEEK_SLIDER_PRECISION: int = 1000 # 進度條的精細度
    
    # [v1.2] 新增設定
    PLAYBACK_RATES: List[float] = [0.5, 0.75, 1.0, 1.5, 2.0]
    SEEK_STEP_MS: int = 5000  # 5 秒
    VOLUME_STEP: int = 5        # 5%

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
        # [v1.2] 為 QComboBox 和 QMenu 添加樣式
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

        /* === [v1.2] QComboBox (播放速度) === */
        QComboBox {
            background-color: #3e3e3e;
            border: 1px solid #555555;
            padding: 5px;
            border-radius: 4px;
            min-width: 60px;
        }
        QComboBox:hover {
            background-color: #4a4a4a;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox QAbstractItemView {
            background-color: #2c2c2c;
            border: 1px solid #444444;
            selection-background-color: #0078d7;
        }

        /* === 狀態列、選單列、工具列 === */
        QStatusBar, QToolBar, QMenuBar {
            background-color: #2d2d2d;
            border: none;
            padding: 4px;
        }
        
        /* === [v1.2] QMenu (右鍵選單) === */
        QMenu {
            background-color: #2c2c2c;
            border: 1px solid #444444;
            padding: 4px;
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

        if not QT_MULTIMEDIA_AVAILABLE:
            QMessageBox.critical(
                self, "缺少模組",
                "找不到 PyQt6.QtMultimedia 或 QtMultimediaWidgets 模組。\n"
                "請確保已安裝 `PyQt6`。\n"
                "應用程式即將退出。"
            )
            QTimer.singleShot(100, self.close) 
            return

        self.settings = QSettings(Config.ORGANIZATION_NAME, Config.APP_NAME)
        self.setWindowTitle(Config.APP_TITLE)
        self.setAcceptDrops(True) 

        self.theme_manager = ThemeManager(QApplication.instance())
        self.theme_manager.toggle_theme(is_dark=True) 

        self.current_path: Optional[str] = None
        self.playlist_files: List[str] = []
        self.current_playlist_index: int = -1 
        self._is_slider_pressed: bool = False

        self.repeat_mode: int = 0  
        self.shuffle_enabled: bool = False
        self.is_muted: bool = False # [v1.2] 靜音狀態

        # 1. 建立核心媒體元件
        self.video_widget = QVideoWidget()
        # [v1.2] 設定右鍵選單策略
        self.video_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()

        # 2. 關鍵連結
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setAudioOutput(self.audio_output)

        # 3. 建立 UI
        self.create_docks() 
        self.create_actions() 
        self.create_toolbars() 
        self.create_controls_bar() 

        # 4. 建立狀態列
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("準備就緒。請開啟影片檔案。")

        # 5. 連接所有訊號
        self.connect_signals()

        self._update_ui_state(QMediaPlayer.PlaybackState.StoppedState)

        # 6. 載入上次的設定
        self.load_settings()

    # [修改 v1.2.1] 替換 create_actions
    def create_actions(self) -> None:
        """建立選單和工具列的 QAction"""
        
        # (修正) 改為傳遞 QStyle.StandardPixmap 枚舉
        self.open_action = self._create_action(
            "開啟影片...", QStyle.StandardPixmap.SP_DialogOpenButton, 
            QKeySequence.StandardKey.Open, self.open_file_dialog
        )
        self.open_folder_action = self._create_action(
            "開啟資料夾...", QStyle.StandardPixmap.SP_DirOpenIcon, 
            "Ctrl+Shift+O", self.open_folder_dialog
        )
        self.exit_action = self._create_action(
            "離開", QStyle.StandardPixmap.SP_DialogCloseButton, 
            QKeySequence.StandardKey.Quit, self.close
        )
        
        self.toggle_playlist_action = QAction("切換播放清單", self)
        self.toggle_playlist_action.triggered.connect(self.playlist_dock.toggleViewAction)
        
        self.toggle_theme_action = self._create_action(
            "切換主題", QStyle.StandardPixmap.SP_DesktopIcon, # (示意圖示)
            "Ctrl+T", self.theme_manager.toggle_theme
        )

        self.add_files_action = self._create_action(
            "新增檔案", QStyle.StandardPixmap.SP_FileDialogNewFolder, # (示意圖示)
            None, self._on_add_files
        )
        self.remove_item_action = self._create_action(
            "移除選中", QStyle.StandardPixmap.SP_DialogCancelButton, # (示意圖示)
            QKeySequence.StandardKey.Delete, self._on_remove_items
        )
        self.clear_list_action = self._create_action(
            "清空清單", QStyle.StandardPixmap.SP_DialogResetButton, # (示意圖示)
            None, self._on_clear_list
        )
        
        # [v1.2] 右鍵選單和快捷鍵會用到的動作
        self.mute_action = QAction("靜音", self)
        self.mute_action.triggered.connect(self._toggle_mute)
        
        self.seek_forward_action = QAction(f"快轉 {Config.SEEK_STEP_MS // 1000} 秒", self)
        self.seek_forward_action.triggered.connect(self._seek_forward)
        
        self.seek_backward_action = QAction(f"倒退 {Config.SEEK_STEP_MS // 1000} 秒", self)
        self.seek_backward_action.triggered.connect(self._seek_backward)


    def create_toolbars(self) -> None:
        """建立頂部工具列，並填充所有工具列和 UI 動作"""
        file_toolbar = self.addToolBar("檔案")
        file_toolbar.setIconSize(QSize(20, 20))
        file_toolbar.addActions([self.open_action, self.open_folder_action])

        view_toolbar = self.addToolBar("檢視")
        view_toolbar.setIconSize(QSize(20, 20))
        view_toolbar.addActions([self.toggle_playlist_action, self.toggle_theme_action])

        self.playlist_toolbar.addActions([self.add_files_action, self.remove_item_action, self.clear_list_action])
        self.playlist_widget.addAction(self.remove_item_action) 


    def create_docks(self) -> None:
        """建立可停靠的播放清單 (v1.1 帶有工具列)"""
        self.playlist_dock = QDockWidget("播放清單", self)
        
        playlist_container = QWidget()
        layout = QVBoxLayout(playlist_container)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        self.playlist_toolbar = QToolBar("播放清單工具列")
        self.playlist_toolbar.setIconSize(QSize(18, 18))
        layout.addWidget(self.playlist_toolbar)

        self.playlist_widget = QListWidget()
        self.playlist_widget.itemDoubleClicked.connect(self._on_playlist_item_double_clicked)
        self.playlist_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(self.playlist_widget, 1) 

        self.playlist_dock.setWidget(playlist_container)
        self.playlist_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.playlist_dock)
        self.playlist_dock.setVisible(True)

    def create_controls_bar(self) -> None:
        """建立底部的播放控制列 (v1.2 帶有速度控制)"""
        
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

        self.play_pause_button = QPushButton()
        self.play_pause_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        buttons_layout.addWidget(self.play_pause_button)

        self.stop_button = QPushButton()
        self.stop_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.stop_button.clicked.connect(self._on_stop_clicked)
        buttons_layout.addWidget(self.stop_button)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setFixedWidth(90)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        buttons_layout.addWidget(self.time_label)
        
        buttons_layout.addSpacing(10)

        self.repeat_button = QPushButton()
        self.repeat_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.repeat_button.setCheckable(True)
        self.repeat_button.setToolTip("循環: 關")
        self.repeat_button.setFixedSize(28, 28) 
        self.repeat_button.clicked.connect(self._on_repeat_toggled)
        buttons_layout.addWidget(self.repeat_button)

        self.shuffle_button = QPushButton()
        self.shuffle_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipForward)) 
        self.shuffle_button.setCheckable(True)
        self.shuffle_button.setToolTip("隨機播放: 關")
        self.shuffle_button.setFixedSize(28, 28) 
        self.shuffle_button.clicked.connect(self._on_shuffle_toggled)
        buttons_layout.addWidget(self.shuffle_button)

        buttons_layout.addStretch(1) # 彈性空間
        
        # [v1.2] 播放速度控制
        self.rate_combo = QComboBox()
        self.rate_combo.addItems([f"{rate}x" for rate in Config.PLAYBACK_RATES])
        self.rate_combo.setCurrentText("1.0x")
        self.rate_combo.setFixedWidth(70)
        self.rate_combo.setToolTip("播放速度")
        self.rate_combo.currentTextChanged.connect(self._on_rate_changed)
        buttons_layout.addWidget(self.rate_combo)
        buttons_layout.addSpacing(10)

        # 音量圖示
        self.volume_label_icon = QLabel()
        # 圖示將由 load_settings 和 _update_volume_icon 設定
        buttons_layout.addWidget(self.volume_label_icon)

        # 音量條
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setFixedWidth(120)
        buttons_layout.addWidget(self.volume_slider)

        # 全螢幕 按鈕
        self.fullscreen_button = QPushButton()
        self.fullscreen_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarMaxButton)) # [v1.1]
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

        # [v1.2] 右鍵選單訊號
        self.video_widget.customContextMenuRequested.connect(self._show_video_context_menu)

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
            self.load_video(path)

    def open_folder_dialog(self) -> None:
        """開啟資料夾並將所有影片載入播放清單"""
        video_dir = QStandardPaths.standardLocations(QStandardPaths.StandardLocation.MoviesLocation)
        start_dir = video_dir[0] if video_dir else os.path.expanduser("~")
        
        dir_path = QFileDialog.getExistingDirectory(self, "開啟資料資料夾", start_dir)
        if dir_path:
            self._scan_folder_for_playlist(dir_path)
            if self.playlist_files:
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
        
        # [v1.2] 重設播放速度為 1.0x
        self.rate_combo.setCurrentText("1.0x")
        self.media_player.setPlaybackRate(1.0)
        
        if path in self.playlist_files:
            self.current_playlist_index = self.playlist_files.index(path)
            self.playlist_widget.setCurrentRow(self.current_playlist_index)
        else:
            self.current_playlist_index = -1 

    def toggle_play_pause(self) -> None:
        """切換播放或暫停"""
        state = self.media_player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        elif state == QMediaPlayer.PlaybackState.PausedState or state == QMediaPlayer.PlaybackState.StoppedState:
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
        if not self._is_slider_pressed:
            self.seek_slider.setValue(position_ms)
        duration_ms = self.media_player.duration()
        self.time_label.setText(
            f"{self._format_time(position_ms)} / {self._format_time(duration_ms)}"
        )

    @pyqtSlot('qint64')
    def _on_duration_changed(self, duration_ms: int) -> None:
        self.seek_slider.setRange(0, duration_ms)
        position_ms = self.media_player.position()
        self.time_label.setText(
            f"{self._format_time(position_ms)} / {self._format_time(duration_ms)}"
        )

    @pyqtSlot(QMediaPlayer.PlaybackState)
    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        self._update_ui_state(state)
        if state == QMediaPlayer.PlaybackState.StoppedState:
            pos = self.media_player.position()
            dur = self.media_player.duration()
            if dur > 0 and pos >= dur - 100: 
                self._play_next()

    @pyqtSlot()
    def _on_stop_clicked(self) -> None:
        self.media_player.stop()

    @pyqtSlot(int)
    def _on_volume_changed(self, value: int) -> None:
        """(UI) 音量條被拖動時"""
        volume = value / 100.0
        self.audio_output.setVolume(volume)
        
        # [v1.2] 如果使用者調整音量，則取消靜音
        if self.is_muted and value > 0:
            self.is_muted = False
            self.audio_output.setMuted(False)
        
        # [v1.2] 如果音量為 0，則視為靜音
        if value == 0 and not self.is_muted:
            self.is_muted = True
            self.audio_output.setMuted(True)
            
        self._update_volume_icon(value, self.is_muted)

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
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.current_playlist_index = self.playlist_widget.row(item) 
            self.load_video(path)

    @pyqtSlot()
    def _on_add_files(self) -> None:
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
            
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.StoppedState:
                self.current_playlist_index = self.playlist_files.index(paths[0])
                self.load_video(paths[0])


    @pyqtSlot()
    def _on_remove_items(self) -> None:
        selected_items = self.playlist_widget.selectedItems()
        if not selected_items:
            return

        selected_rows = sorted([self.playlist_widget.row(item) for item in selected_items], reverse=True)
        
        for row in selected_rows:
            item = self.playlist_widget.takeItem(row) 
            path = item.data(Qt.ItemDataRole.UserRole)
            if path in self.playlist_files:
                self.playlist_files.remove(path) 
            
            if row == self.current_playlist_index:
                self.media_player.stop()
                self.current_path = None
                self.current_playlist_index = -1
                
            elif row < self.current_playlist_index:
                self.current_playlist_index -= 1

    @pyqtSlot()
    def _on_clear_list(self) -> None:
        self.media_player.stop()
        self.playlist_widget.clear()
        self.playlist_files.clear()
        self.current_path = None
        self.current_playlist_index = -1
        self.setWindowTitle(Config.APP_TITLE)

    # --- 播放控制 (v1.1) ---
    
    @pyqtSlot()
    def _on_repeat_toggled(self) -> None:
        self.repeat_mode = (self.repeat_mode + 1) % 3
        
        if self.repeat_mode == 0:
            self.repeat_button.setToolTip("循環: 關")
            self.repeat_button.setChecked(False)
        elif self.repeat_mode == 1:
            self.repeat_button.setToolTip("循環: 單一")
            self.repeat_button.setChecked(True)
        else: # self.repeat_mode == 2
            self.repeat_button.setToolTip("循環: 全部")
            self.repeat_button.setChecked(True) 

    @pyqtSlot(bool)
    def _on_shuffle_toggled(self, checked: bool) -> None:
        self.shuffle_enabled = checked
        self.shuffle_button.setToolTip(f"隨機播放: {'開' if checked else '關'}")
        
        if checked and len(self.playlist_files) > 1 and self.current_playlist_index != -1:
            current_path = self.playlist_files.pop(self.current_playlist_index)
            random.shuffle(self.playlist_files)
            self.playlist_files.insert(0, current_path) 
            self.current_playlist_index = 0
            
            self.playlist_widget.clear()
            for path in self.playlist_files:
                item = QListWidgetItem()
                item.setText(os.path.basename(path))
                item.setData(Qt.ItemDataRole.UserRole, path)
                self.playlist_widget.addItem(item)
            self.playlist_widget.setCurrentRow(self.current_playlist_index)

    # --- v1.2 新增槽 (Slots) ---
            
    @pyqtSlot(QPoint)
    def _show_video_context_menu(self, pos: QPoint) -> None:
        """[v1.2] 顯示影片右鍵選單"""
        if self.media_player.source().isNull():
            return

        menu = QMenu(self)

        # 1. 播放/暫停
        state = self.media_player.playbackState()
        play_pause_text = "暫停" if state == QMediaPlayer.PlaybackState.PlayingState else "播放"
        play_pause_action = QAction(play_pause_text, self)
        play_pause_action.triggered.connect(self.toggle_play_pause)
        menu.addAction(play_pause_action)

        # 2. 靜音
        mute_text = "取消靜音" if self.is_muted else "靜音"
        mute_action = QAction(mute_text, self)
        mute_action.triggered.connect(self._toggle_mute)
        menu.addAction(mute_action)
        
        # 3. 全螢幕
        fullscreen_text = "退出全螢幕" if self.isFullScreen() else "全螢幕"
        fullscreen_action = QAction(fullscreen_text, self)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        menu.addAction(fullscreen_action)

        menu.addSeparator()

        # 4. 快轉/倒退
        seek_forward_action = QAction(f"快轉 {Config.SEEK_STEP_MS // 1000} 秒 (→)", self)
        seek_forward_action.triggered.connect(self._seek_forward)
        menu.addAction(seek_forward_action)
        
        seek_backward_action = QAction(f"倒退 {Config.SEEK_STEP_MS // 1000} 秒 (←)", self)
        seek_backward_action.triggered.connect(self._seek_backward)
        menu.addAction(seek_backward_action)

        menu.addSeparator()
        
        # 5. 開啟檔案
        menu.addAction(self.open_action) # 重用 existing action

        # 顯示選單
        menu.exec(self.video_widget.mapToGlobal(pos))

    @pyqtSlot(str)
    def _on_rate_changed(self, text: str) -> None:
        """[v1.2] 播放速度改變時"""
        if 'x' in text:
            try:
                rate = float(text.replace('x', ''))
                self.media_player.setPlaybackRate(rate)
            except ValueError:
                self.media_player.setPlaybackRate(1.0)

    @pyqtSlot()
    def _toggle_mute(self) -> None:
        """[v1.2] 切換靜音"""
        self.is_muted = not self.is_muted
        self.audio_output.setMuted(self.is_muted)
        
        # 如果取消靜音且音量為0，則設定一個預設音量
        if not self.is_muted and self.volume_slider.value() == 0:
            self.volume_slider.setValue(int(Config.DEFAULT_VOLUME * 100))
            
        self._update_volume_icon(self.volume_slider.value(), self.is_muted)

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

    # [修改 v1.2.1] 替換 _create_action
    def _create_action(self, 
                         text: str, 
                         std_icon: Optional[QStyle.StandardPixmap], 
                         shortcut: Optional[str | QKeySequence], 
                         slot: callable) -> QAction:
        """輔助函數：建立 QAction (優先使用 QStyle.StandardPixmap)"""
        
        icon = QIcon()
        if std_icon is not None:
            # 使用標準圖示
            icon = self.style().standardIcon(std_icon)

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
        # [v1.2] 啟用/禁用速度控制
        self.rate_combo.setEnabled(has_media)

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
            
            if self.shuffle_enabled:
                random.shuffle(temp_files)
            
            self.playlist_files = temp_files
            
            for path in self.playlist_files:
                item = QListWidgetItem()
                item.setText(os.path.basename(path))
                item.setData(Qt.ItemDataRole.UserRole, path)
                self.playlist_widget.addItem(item)
                    
        except Exception as e:
            print(f"掃描資料G時出錯: {e}")
            
    def _play_next(self) -> None:
        """[v1.1] 播放清單中的下一個項目"""
        if not self.playlist_files:
            return

        if self.repeat_mode == 1: 
            self.media_player.setPosition(0)
            self.media_player.play()
            return

        next_index = -1
        if self.shuffle_enabled:
            next_index = random.randint(0, len(self.playlist_files) - 1)
        elif self.current_playlist_index < len(self.playlist_files) - 1:
            next_index = self.current_playlist_index + 1
        elif self.repeat_mode == 2: 
            next_index = 0

        if next_index != -1:
            self.current_playlist_index = next_index
            path = self.playlist_files[self.current_playlist_index]
            self.load_video(path)
        else:
            self.media_player.stop()

    # --- v1.2 新增輔助方法 ---
            
    @pyqtSlot()
    def _seek_forward(self) -> None:
        """[v1.2] 快轉"""
        dur = self.media_player.duration()
        new_pos = self.media_player.position() + Config.SEEK_STEP_MS
        if dur > 0:
            new_pos = min(dur, new_pos)
        self.media_player.setPosition(new_pos)

    @pyqtSlot()
    def _seek_backward(self) -> None:
        """[v1.2] 倒退"""
        new_pos = max(0, self.media_player.position() - Config.SEEK_STEP_MS)
        self.media_player.setPosition(new_pos)

    @pyqtSlot(int)
    def _change_volume(self, delta: int) -> None:
        """[v1.2] 透過快捷鍵改變音量"""
        new_vol = max(0, min(100, self.volume_slider.value() + delta))
        self.volume_slider.setValue(new_vol)
    
    @pyqtSlot(int, bool)
    def _update_volume_icon(self, value: int, is_muted: bool):
        """[v1.2] 根據音量和靜音狀態更新圖示"""
        if is_muted or value == 0:
            icon = QStyle.StandardPixmap.SP_MediaVolumeMuted
        else:
            icon = QStyle.StandardPixmap.SP_MediaVolume
        self.volume_label_icon.setPixmap(self.style().standardIcon(icon).pixmap(QSize(20, 20)))

    # --------------------------------------------------------------------------
    # 事件處理 (Event Handlers)
    # --------------------------------------------------------------------------

    # [修改 v1.2.1] 替換 keyPressEvent
    def keyPressEvent(self, event) -> None:
        """[v1.2.1] 全域快捷鍵 (焦點修正版)"""
        key = event.key()
        
        # [修正] 檢查焦點是否在 QListWidget 或 QComboBox 上
        focused_widget = QApplication.focusWidget()

        if focused_widget == self.playlist_widget or focused_widget == self.rate_combo:
            # 如果焦點在播放清單上
            if focused_widget == self.playlist_widget:
                if key == Qt.Key.Key_Delete:
                    self._on_remove_items()
                    event.accept() # 標記事件已處理
                    return # (修正) 直接返回
            
            # (修正) 對於所有其他按鍵 (例如 QComboBox 的空白鍵、方向鍵等)
            # 讓元件自行處理
            super().keyPressEvent(event)
            return # (修正) 直接返回，不觸發下面的全域快捷鍵

        # --- 全域快捷鍵 (不在輸入元件上時) ---
        if event.modifiers() == Qt.KeyboardModifier.NoModifier:
            if key == Qt.Key.Key_Space:
                self.toggle_play_pause()
            elif key == Qt.Key.Key_M:
                self._toggle_mute()
            elif key == Qt.Key.Key_Left:
                self._seek_backward()
            elif key == Qt.Key.Key_Right:
                self._seek_forward()
            elif key == Qt.Key.Key_Up:
                self._change_volume(Config.VOLUME_STEP)
            elif key == Qt.Key.Key_Down:
                self._change_volume(-Config.VOLUME_STEP)
            elif key == Qt.Key.Key_F11:
                self.toggle_fullscreen()
            elif key == Qt.Key.Key_Escape and self.isFullScreen():
                self.toggle_fullscreen()
            else:
                super().keyPressEvent(event)
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
                self.load_video(path) 
            elif os.path.isdir(path):
                 self._scan_folder_for_playlist(path) 
                 if self.playlist_files:
                     self.load_video(self.playlist_files[0]) 

    def closeEvent(self, event: QCloseEvent) -> None:
        """關閉應用程式時確保媒體播放器停止並儲存設定"""
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
        
        # [v1.2] 確保啟動時圖示正確
        self._update_volume_icon(self.volume_slider.value(), self.is_muted)

# ==============================================================================
# 4. 應用程式入口
# ==============================================================================
def main() -> None:
    """主函式，用於啟動應用程式。"""
    QApplication.setOrganizationName(Config.ORGANIZATION_NAME)
    QApplication.setApplicationName(Config.APP_NAME)

    app = QApplication(sys.argv)
    
    if not QT_MULTIMEDIA_AVAILABLE:
        sys.exit(1)

    window = VideoPlayerWindow()
    if getattr(window, 'media_player', None): 
        window.show()
    else:
        sys.exit(1) 

    sys.exit(app.exec())

if __name__ == '__main__':
    main()