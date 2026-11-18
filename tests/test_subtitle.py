"""測試 player.subtitle 字幕解析與自動匹配功能。"""

from pathlib import Path
from player.subtitle import SubtitleParser, find_matching_subtitle_file


def test_parse_srt_and_query_time() -> None:
    srt_content = """1
00:00:01,000 --> 00:00:03,500
第一句繁體中文字幕

2
00:00:05,000 --> 00:00:08,000
<i>第二句帶 HTML 標籤</i>
第二行文字
"""
    parser = SubtitleParser()
    cues = parser.parse_text(srt_content)
    assert len(cues) == 2
    assert parser.get_text_at(500) == ""
    assert parser.get_text_at(2_000) == "第一句繁體中文字幕"
    assert parser.get_text_at(6_000) == "第二句帶 HTML 標籤\n第二行文字"
    assert parser.get_text_at(9_000) == ""


def test_parse_webvtt() -> None:
    vtt_content = """WEBVTT

00:01.000 --> 00:04.000
WebVTT 簡短時間格式測試
"""
    parser = SubtitleParser()
    cues = parser.parse_text(vtt_content)
    assert len(cues) == 1
    assert parser.get_text_at(2_500) == "WebVTT 簡短時間格式測試"


def test_load_file_and_find_matching_subtitle(tmp_path: Path) -> None:
    video_file = tmp_path / "demo_video.mp4"
    sub_file = tmp_path / "demo_video.srt"
    video_file.write_text("")
    sub_file.write_text(
        "1\n00:00:00,500 --> 00:00:02,000\n自動偵測字幕成功\n",
        encoding="utf-8",
    )

    matched = find_matching_subtitle_file(str(video_file))
    assert matched == str(sub_file)

    parser = SubtitleParser()
    assert parser.load_file(matched) is True
    assert parser.get_text_at(1_000) == "自動偵測字幕成功"
