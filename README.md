# PyQt6 影片播放器 (PyQt6 Video Player) v1.4.0

這是一個使用 Python 和 PyQt6 (`QtMultimedia` & `QtSvg`) 建構的現代化、輕量級桌面影片播放器。

## 功能特色

- **核心播放**：
  - 使用 `QMediaPlayer` 與 `QVideoWidget` 實現流暢的影片播放。
  - 支援常見影片格式（`.mp4`, `.avi`, `.mkv`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`）。
- **進階媒體功能 (v1.4.0 新增)**：
  - **一鍵影片截圖 (Snapshot)**：擷取影片畫面並自動存為 PNG 圖片（快捷鍵：`S`）。
  - **字幕與多音軌切換**：支援切換影片內嵌音軌、內嵌字幕，以及自動偵測/手動載入外掛 `.srt` / `.vtt` 字幕檔（快捷鍵：`C`）。
  - **畫面比例切換**：支援 `自動`、`16:9`、`4:3` 與 `填滿` 四種畫面比例模式（快捷鍵：`A`）。
- **播放控制**：
  - 播放 / 暫停 / 停止 / 上一首 / 下一首（快捷鍵：`Space`）。
  - 支援**點擊進度條任意位置直接跳轉**與滑桿拖曳預覽。
  - 支援超過 1 小時的 `HH:MM:SS` 時間顯示。
  - 循環播放（關閉 / 單一 / 清單全部）與隨機播放（自動記憶與還原原始清單順序）。
  - 播放速度控制（`0.5x` ~ `2.0x`），切換影片時自動保留所選倍速。
- **播放清單與拖放**：
  - 可停靠的播放清單面板，支援多選刪除與工具列操作。
  - 支援一次拖放單一或多個影片檔案、資料夾或 `.srt` / `.vtt` 外掛字幕檔。
- **現代化介面與設定記憶**：
  - 高 DPI SVG 向量圖示與 Modern Dark / Modern Light 雙主題切換（快捷鍵：`Ctrl+T`）。
  - 無邊框全螢幕模式（快捷鍵：`F11`、`Esc` 或**雙擊影片畫面**），自動隱藏工具列、清單與狀態列。
  - 自動保存視窗幾何位置、音量、靜音、循環、隨機、畫面比例與主題設定。

## 快捷鍵一覽

| 按鍵 | 功能 |
| :--- | :--- |
| `Space` | 播放 / 暫停 |
| `M` | 切換靜音 |
| `S` | 擷取影片畫面截圖 (Snapshot) |
| `A` | 循環切換畫面比例 (自動 / 16:9 / 4:3 / 填滿) |
| `C` | 開啟字幕與音軌切換選單 |
| `←` / `→` | 倒退 / 快轉 5 秒 |
| `↑` / `↓` | 音量增加 / 減少 5% |
| `F11` / `Esc` | 切換 / 退出全螢幕 |
| `Ctrl+O` / `Ctrl+Shift+O` | 開啟影片檔案 / 開啟資料夾 |
| `Ctrl+T` | 切換深色 / 淺色主題 |

## 專案結構

```text
pyqt_video_player_github/
├── pyqt_video_player.py   # 相容啟動入口
├── player/                # 核心模組套件
│   ├── config.py          # 設定常數、列舉與時間/路徑/比例計算工具
│   ├── icons.py           # 高 DPI SVG 向量圖示渲染器
│   ├── playlist.py        # PlaylistManager 播放清單狀態管理
│   ├── subtitle.py        # SubtitleParser (.srt/.vtt) 外掛字幕解析與自動匹配
│   ├── theme.py           # ThemeManager 深/淺色設計系統
│   ├── widgets.py         # ClickableSlider, VideoCanvasContainer, EmptyStateWidget
│   └── main_window.py     # VideoPlayerWindow 主視窗協調器
├── tests/                 # pytest 單元測試
├── build.py               # PyInstaller Windows 打包腳本
└── requirements.txt       # 依賴套件清單
```

## 安裝與執行

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\activate
# macOS / Linux: source .venv/bin/activate

pip install -r requirements.txt
python pyqt_video_player.py
```

## 執行單元測試

```bash
python -m pytest -v
```
