"""自訂 PyQt6 播放器 UI 元件。"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QStyle,
    QStyleOptionSlider,
    QVBoxLayout,
    QWidget,
)

from player.icons import create_icon, render_svg_pixmap


class ClickableSlider(QSlider):
    """支援點擊軌道任意位置直接跳轉數值的滑桿。"""

    clickedValue = pyqtSignal(int)

    def __init__(self, orientation: Qt.Orientation, parent=None) -> None:
        super().__init__(orientation, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            groove = self.style().subControlRect(
                QStyle.ComplexControl.CC_Slider,
                opt,
                QStyle.SubControl.SC_SliderGroove,
                self,
            )
            handle = self.style().subControlRect(
                QStyle.ComplexControl.CC_Slider,
                opt,
                QStyle.SubControl.SC_SliderHandle,
                self,
            )

            if self.orientation() == Qt.Orientation.Horizontal:
                slider_length = handle.width()
                slider_min = groove.x()
                slider_max = groove.right() - slider_length + 1
                pos = int(event.position().x()) - slider_length // 2
            else:
                slider_length = handle.height()
                slider_min = groove.y()
                slider_max = groove.bottom() - slider_length + 1
                pos = int(event.position().y()) - slider_length // 2

            value = QStyle.sliderValueFromPosition(
                self.minimum(),
                self.maximum(),
                pos - slider_min,
                max(1, slider_max - slider_min),
                opt.upsideDown,
            )
            self.setValue(value)
            self.clickedValue.emit(value)

        super().mousePressEvent(event)


class PlayerVideoWidget(QVideoWidget):
    """支援雙擊切換全螢幕的影片畫布元件。"""

    doubleClicked = pyqtSignal()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.doubleClicked.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class EmptyStateWidget(QWidget):
    """尚未載入影片時顯示的現代化引導畫面。"""

    openFileRequested = pyqtSignal()
    openFolderRequested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("EmptyStateContainer")

        outer_layout = QVBoxLayout(self)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("EmptyStateCard")
        card.setFixedWidth(400)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 36, 32, 32)
        card_layout.setSpacing(12)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.hero_icon_label = QLabel()
        self.hero_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.hero_icon_label)

        title = QLabel("尚未載入影片")
        title.setObjectName("EmptyStateTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        subtitle = QLabel("將影片檔案或資料夾拖曳至此處\n或點擊下方按鈕開始播放")
        subtitle.setObjectName("EmptyStateSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        card_layout.addWidget(subtitle)

        card_layout.addSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.open_file_btn = QPushButton(" 開啟影片")
        self.open_file_btn.setObjectName("PrimaryActionButton")
        self.open_file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_file_btn.clicked.connect(self.openFileRequested.emit)
        btn_row.addWidget(self.open_file_btn)

        self.open_folder_btn = QPushButton(" 開啟資料夾")
        self.open_folder_btn.setObjectName("SecondaryActionButton")
        self.open_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_folder_btn.clicked.connect(self.openFolderRequested.emit)
        btn_row.addWidget(self.open_folder_btn)

        card_layout.addLayout(btn_row)
        outer_layout.addWidget(card)

    def apply_theme(self, accent_color: str, normal_color: str) -> None:
        """依據目前主題更新空狀態圖示色彩。"""
        self.hero_icon_label.setPixmap(
            render_svg_pixmap("film", accent_color, size=56)
        )
        self.open_file_btn.setIcon(create_icon("open_file", "#FFFFFF", size=16))
        self.open_folder_btn.setIcon(create_icon("open_folder", normal_color, size=16))
