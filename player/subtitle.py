"""外掛字幕 (.srt / .vtt) 解析器與媒體軌道名稱格式化工具。"""

import os
import re
from dataclasses import dataclass
from typing import List, Optional

_TIMECODE_PATTERN = re.compile(
    r"(?:(\d{1,2}):)?(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(?:(\d{1,2}):)?(\d{2}):(\d{2})[,.](\d{3})"
)
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class SubtitleCue:
    """單一字幕時間區間與文字。"""

    start_ms: int
    end_ms: int
    text: str


def _to_ms(hours: Optional[str], minutes: str, seconds: str, millis: str) -> int:
    h = int(hours) if hours else 0
    m = int(minutes)
    s = int(seconds)
    ms = int(millis)
    return ((h * 3600 + m * 60 + s) * 1000) + ms


class SubtitleParser:
    """管理外掛字幕解析與依毫秒時間點查詢對白。"""

    def __init__(self) -> None:
        self._cues: List[SubtitleCue] = []
        self.source_path: Optional[str] = None

    @property
    def cues(self) -> List[SubtitleCue]:
        return list(self._cues)

    def clear(self) -> None:
        self._cues.clear()
        self.source_path = None

    def load_file(self, path: str) -> bool:
        """讀取並解析 .srt 或 .vtt 字幕檔案（自動嘗試常見中文與萬國碼編碼）。"""
        if not path or not os.path.isfile(path):
            return False

        content: Optional[str] = None
        for encoding in ("utf-8-sig", "utf-8", "cp950", "big5", "utf-16"):
            try:
                with open(path, "r", encoding=encoding) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, OSError):
                continue

        if content is None:
            return False

        self.parse_text(content)
        self.source_path = path
        return len(self._cues) > 0

    def parse_text(self, raw_text: str) -> List[SubtitleCue]:
        """從 SRT 或 WebVTT 字串內容解析出排序後的 SubtitleCue 列表。"""
        self._cues.clear()
        normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not normalized:
            return []

        blocks = re.split(r"\n\s*\n", normalized)
        parsed: List[SubtitleCue] = []

        for block in blocks:
            lines = [line.strip() for line in block.split("\n") if line.strip()]
            if not lines or lines[0].upper().startswith("WEBVTT"):
                continue

            match_idx = -1
            match_obj = None
            for idx, line in enumerate(lines):
                m = _TIMECODE_PATTERN.search(line)
                if m:
                    match_idx = idx
                    match_obj = m
                    break

            if match_obj is None or match_idx == -1:
                continue

            start_ms = _to_ms(
                match_obj.group(1),
                match_obj.group(2),
                match_obj.group(3),
                match_obj.group(4),
            )
            end_ms = _to_ms(
                match_obj.group(5),
                match_obj.group(6),
                match_obj.group(7),
                match_obj.group(8),
            )
            text_lines = [
                _HTML_TAG_PATTERN.sub("", tl).strip()
                for tl in lines[match_idx + 1 :]
            ]
            clean_text = "\n".join(tl for tl in text_lines if tl)
            if clean_text and end_ms > start_ms:
                parsed.append(SubtitleCue(start_ms=start_ms, end_ms=end_ms, text=clean_text))

        parsed.sort(key=lambda c: c.start_ms)
        self._cues = parsed
        return list(self._cues)

    def get_text_at(self, position_ms: int) -> str:
        """查詢指定毫秒位置對應的字幕文字（若無則回傳空字串）。"""
        if position_ms < 0 or not self._cues:
            return ""

        active_texts: List[str] = []
        for cue in self._cues:
            if cue.start_ms <= position_ms <= cue.end_ms:
                active_texts.append(cue.text)
            elif cue.start_ms > position_ms:
                break
        return "\n".join(active_texts)


def find_matching_subtitle_file(video_path: str) -> Optional[str]:
    """在影片同目錄下尋找同名的 .srt 或 .vtt 字幕檔。"""
    if not video_path or not os.path.isfile(video_path):
        return None

    folder = os.path.dirname(video_path)
    stem = os.path.splitext(os.path.basename(video_path))[0].lower()

    try:
        for fname in sorted(os.listdir(folder)):
            f_stem, f_ext = os.path.splitext(fname)
            if f_ext.lower() in (".srt", ".vtt") and f_stem.lower() == stem:
                return os.path.normpath(os.path.join(folder, fname))
    except OSError:
        return None
    return None
