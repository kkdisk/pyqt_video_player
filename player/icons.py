"""使用 PyQt6.QtSvg 繪製高畫質、主題自適應的現代化向量圖示。"""

from typing import Dict
from PyQt6.QtCore import QByteArray, QRectF, QSize, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

# 現代極簡風格 SVG 路徑 (24x24 viewBox)
_SVG_TEMPLATES: Dict[str, str] = {
    "play": (
        '<svg viewBox="0 0 24 24" fill="{color}">'
        '<path d="M8 5.14v14l11-7-11-7z"/>'
        "</svg>"
    ),
    "pause": (
        '<svg viewBox="0 0 24 24" fill="{color}">'
        '<rect x="6" y="4" width="4" height="16" rx="1.2"/>'
        '<rect x="14" y="4" width="4" height="16" rx="1.2"/>'
        "</svg>"
    ),
    "stop": (
        '<svg viewBox="0 0 24 24" fill="{color}">'
        '<rect x="6" y="6" width="12" height="12" rx="2"/>'
        "</svg>"
    ),
    "prev": (
        '<svg viewBox="0 0 24 24" fill="{color}">'
        '<rect x="5" y="5" width="2.5" height="14" rx="1"/>'
        '<path d="M19 5.5v13l-9.5-6.5L19 5.5z"/>'
        "</svg>"
    ),
    "next": (
        '<svg viewBox="0 0 24 24" fill="{color}">'
        '<rect x="16.5" y="5" width="2.5" height="14" rx="1"/>'
        '<path d="M5 5.5v13l9.5-6.5L5 5.5z"/>'
        "</svg>"
    ),
    "repeat": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="17 1 21 5 17 9"/>'
        '<path d="M3 11V9a4 4 0 0 1 4-4h14"/>'
        '<polyline points="7 23 3 19 7 15"/>'
        '<path d="M21 13v2a4 4 0 0 1-4 4H3"/>'
        "</svg>"
    ),
    "repeat_one": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="17 1 21 5 17 9"/>'
        '<path d="M3 11V9a4 4 0 0 1 4-4h14"/>'
        '<polyline points="7 23 3 19 7 15"/>'
        '<path d="M21 13v2a4 4 0 0 1-4 4H3"/>'
        '<path d="M11.5 9.5L13 8.5v7" stroke-width="2.2"/>'
        "</svg>"
    ),
    "shuffle": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="16 3 21 3 21 8"/>'
        '<line x1="4" y1="20" x2="21" y2="3"/>'
        '<polyline points="21 16 21 21 16 21"/>'
        '<line x1="15" y1="15" x2="21" y2="21"/>'
        '<line x1="4" y1="4" x2="9" y2="9"/>'
        "</svg>"
    ),
    "volume": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" fill="{color}"/>'
        '<path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>'
        '<path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>'
        "</svg>"
    ),
    "volume_muted": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" fill="{color}"/>'
        '<line x1="23" y1="9" x2="17" y2="15"/>'
        '<line x1="17" y1="9" x2="23" y2="15"/>'
        "</svg>"
    ),
    "fullscreen": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="15 3 21 3 21 9"/>'
        '<polyline points="9 21 3 21 3 15"/>'
        '<line x1="21" y1="3" x2="14" y2="10"/>'
        '<line x1="3" y1="21" x2="10" y2="14"/>'
        "</svg>"
    ),
    "exit_fullscreen": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="4 14 10 14 10 20"/>'
        '<polyline points="20 10 14 10 14 4"/>'
        '<line x1="14" y1="10" x2="21" y2="3"/>'
        '<line x1="3" y1="21" x2="10" y2="14"/>'
        "</svg>"
    ),
    "open_file": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" '
        'stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="2" y="4" width="20" height="16" rx="2.5"/>'
        '<polygon points="10 9 16 12 10 15 10 9" fill="{color}"/>'
        "</svg>"
    ),
    "open_folder": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" '
        'stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>'
        "</svg>"
    ),
    "playlist": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<line x1="8" y1="6" x2="21" y2="6"/>'
        '<line x1="8" y1="12" x2="21" y2="12"/>'
        '<line x1="8" y1="18" x2="21" y2="18"/>'
        '<circle cx="4" cy="6" r="1" fill="{color}"/>'
        '<circle cx="4" cy="12" r="1" fill="{color}"/>'
        '<circle cx="4" cy="18" r="1" fill="{color}"/>'
        "</svg>"
    ),
    "sun": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="4"/>'
        '<path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41'
        'M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>'
        "</svg>"
    ),
    "moon": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>'
        "</svg>"
    ),
    "add": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" '
        'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
        '<line x1="12" y1="5" x2="12" y2="19"/>'
        '<line x1="5" y1="12" x2="19" y2="12"/>'
        "</svg>"
    ),
    "remove": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="3 6 5 6 21 6"/>'
        '<path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>'
        '<path d="M10 11v6M14 11v6"/>'
        '<path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>'
        "</svg>"
    ),
    "clear": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M3 6h18"/>'
        '<path d="M8 12h10"/>'
        '<path d="M5 18h8"/>'
        '<line x1="18" y1="14" x2="22" y2="18"/>'
        '<line x1="22" y1="14" x2="18" y2="18"/>'
        "</svg>"
    ),
    "close": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" '
        'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
        '<line x1="18" y1="6" x2="6" y2="18"/>'
        '<line x1="6" y1="6" x2="18" y2="18"/>'
        "</svg>"
    ),
    "film": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" '
        'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="2" y="3" width="20" height="18" rx="3"/>'
        '<line x1="7" y1="3" x2="7" y2="21"/>'
        '<line x1="17" y1="3" x2="17" y2="21"/>'
        '<line x1="2" y1="8" x2="7" y2="8"/>'
        '<line x1="2" y1="16" x2="7" y2="16"/>'
        '<line x1="17" y1="8" x2="22" y2="8"/>'
        '<line x1="17" y1="16" x2="22" y2="16"/>'
        '<polygon points="10.5 9.5 15 12 10.5 14.5 10.5 9.5" fill="{color}"/>'
        "</svg>"
    ),
    "camera": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>'
        '<circle cx="12" cy="13" r="4"/>'
        "</svg>"
    ),
    "subtitles": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="2" y="4" width="20" height="16" rx="2.5"/>'
        '<path d="M6 12h4M14 12h4M6 16h8M16 16h2"/>'
        "</svg>"
    ),
    "aspect_ratio": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="2" y="4" width="20" height="16" rx="2.5"/>'
        '<polyline points="6 10 6 7 9 7"/>'
        '<polyline points="18 14 18 17 15 17"/>'
        "</svg>"
    ),
}


def render_svg_pixmap(name: str, color: str, size: int = 24, dpr: float = 2.0) -> QPixmap:
    """將內建 SVG 樣板渲染為支援高 DPI 的 QPixmap。"""
    svg_template = _SVG_TEMPLATES.get(name)
    if svg_template is None:
        return QPixmap()

    svg_bytes = QByteArray(svg_template.format(color=color).encode("utf-8"))
    renderer = QSvgRenderer(svg_bytes)

    px_size = max(1, int(size * dpr))
    pixmap = QPixmap(QSize(px_size, px_size))
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    renderer.render(painter, QRectF(0, 0, px_size, px_size))
    painter.end()

    pixmap.setDevicePixelRatio(dpr)
    return pixmap


def create_icon(
    name: str,
    normal_color: str,
    disabled_color: str = "#6B7280",
    active_color: str = "",
    size: int = 24,
) -> QIcon:
    """建立具備 Normal / Disabled / Checked 狀態色的高解析 QIcon。"""
    icon = QIcon()
    normal_pm = render_svg_pixmap(name, normal_color, size=size)
    disabled_pm = render_svg_pixmap(name, disabled_color, size=size)
    icon.addPixmap(normal_pm, QIcon.Mode.Normal, QIcon.State.Off)
    icon.addPixmap(disabled_pm, QIcon.Mode.Disabled, QIcon.State.Off)

    if active_color:
        active_pm = render_svg_pixmap(name, active_color, size=size)
        icon.addPixmap(active_pm, QIcon.Mode.Normal, QIcon.State.On)
        icon.addPixmap(active_pm, QIcon.Mode.Active, QIcon.State.On)

    return icon
