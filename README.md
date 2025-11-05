# PyQt6 影片播放器 (PyQt6 Video Player) v1.0.0

這是一個使用 Python 和 PyQt6 (QtMultimedia) 建構的現代化、輕量級影片播放器。

本專案旨在展示如何使用 PyQt6 打造一個功能完整、介面美觀且響應流暢的桌面媒體應用程式。

## v1.0.0 功能

- 核心播放:
    - 使用 QMediaPlayer 和 QVideoWidget 實現流暢的影片播放。
    - 支援常見影片格式 (MP4, AVI, MKV, MOV 等)。

- 播放控制:
    - 播放 / 暫停 (快捷鍵: Space)
    - 停止
    - 可拖動的影片進度條
    - 可調整的音量條
    - 即時時間顯示 (例如 01:23 / 10:45)

- 播放清單:
    - 可停靠的播放清單面板。
    - 自動載入: 開啟影片或資料夾時，自動掃描並載入同目錄下的所有支援影片。
    - 雙擊播放: 雙擊清單中的項目可立即播放。

- 介面 (UI):

    - 預設啟用精美的深色主題。
    - 支援全螢幕切換 (快捷鍵: F11 或 Esc 退出)。
    - 支援拖曳檔案或資料夾到視窗中以開啟。

## 安裝

在開始之前，請確保您的系統已安裝 Python 3.x。

1. 克隆 (Clone) 或下載此儲存庫:

```
 git clone [您的 GitHub 儲存庫 URL] 
 cd [您的專案資料夾] `
```

2. 安裝所需的套件: 本專案使用 PyQt6。建議在虛擬環境 (virtual environment) 中安裝：
```
# (可選) 建立虛擬環境
python -m venv .venv
# (可選) 啟動虛擬環境
# Windows:
# .\.venv\Scripts\activate
# macOS / Linux:
# source .venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

## 如何執行

安裝完依賴後，直接執行 pyqt_video_player.py 檔案：

` python pyqt_video_player.py `


##　未來規劃 (Roadmap)

請參閱 video_player_roadmap.md 檔案，了解 v1.1 及更高版本的開發計畫。

v1.1: UX 與播放清單強化 (狀態保存、清單控制、循環/隨機播放)

v1.2: 播放精細控制 (播放速度、右鍵選單、更多快捷鍵)

v1.3: 進階媒體功能 (字幕支援、影片資訊)