# ==============================================================================
# PyInstaller 打包腳本 for PyQt6 影片播放器
#
# 說明：
# 此腳本使用 PyInstaller 將 pyqt_video_player.py 與 player 套件打包成單一執行檔 (.exe)。
#
# 它會自動處理 PyQt6 和 QtMultimedia 的隱藏導入 (hidden-import) 問題。
#
# 使用方法 (在終端機中):
# 1. 確保已安裝 pyinstaller: pip install pyinstaller
# 2. (可選) 準備一個 'icon.ico' 檔案放在同目錄下
# 3. 執行此腳本: python build.py
#
# ==============================================================================

import PyInstaller.__main__
import os
import shutil

# --- 設定 ---
SCRIPT_NAME = 'pyqt_video_player.py'
EXE_NAME = 'MyVideoPlayer'
ICON_FILE = 'icon.ico' # 您的應用程式圖示 (可選)

BUILD_DIR = 'build'
DIST_DIR = 'dist'
# -------------

# 檢查圖示是否存在
use_icon = os.path.exists(ICON_FILE)
icon_arg = f'--icon={ICON_FILE}' if use_icon else '--icon=NONE'

if use_icon:
    print(f"找到圖示: {ICON_FILE}")
else:
    print(f"未找到圖示 '{ICON_FILE}'，將使用預設圖示。")

# PyInstaller 參數
# 參考: https://pyinstaller.org/en/stable/usage.html
pyinstaller_args = [
    '--name=%s' % EXE_NAME,
    '--onefile',         # 打包成單一 .exe 檔案 (方便分發)
    '--windowed',      # GUI 應用程式，執行時不顯示黑色主控台
    '--clean',           # 建置前清理快取
    
    # --- 關鍵：處理 PyQt6 多媒體與內部套件依賴 ---
    '--hidden-import=PyQt6.QtMultimedia',
    '--hidden-import=PyQt6.QtMultimediaWidgets',
    '--hidden-import=PyQt6.QtSvg',
    '--collect-submodules=player',
    
    # --- 圖示 (可選) ---
    icon_arg,
]

# 組合最終命令
full_command = pyinstaller_args + [SCRIPT_NAME]

print("\n" + "="*50)
print(f"--- 正在執行 PyInstaller ---")
print(f"命令: pyinstaller {' '.join(full_command)}")
print("="*50 + "\n")

# 執行 PyInstaller
try:
    PyInstaller.__main__.run(full_command)
    print("\n" + "="*50)
    print(f"--- 建置成功 ---")
    print(f"可執行檔案位於: {os.path.abspath(DIST_DIR)}")
    print("="*50 + "\n")

except Exception as e:
    print("\n" + "!"*50)
    print(f"--- 建置失敗 ---")
    print(f"錯誤: {e}")
    print("!"*50 + "\n")

finally:
    # --- 清理 (可選) ---
    # PyInstaller 會留下 .spec 檔案和 'build' 資料夾
    print("--- 正在清理暫存檔案 ---")
    try:
        if os.path.exists(BUILD_DIR):
            shutil.rmtree(BUILD_DIR)
            print(f"已刪除 '{BUILD_DIR}' 資料夾")
            
        spec_file = f'{EXE_NAME}.spec'
        if os.path.exists(spec_file):
            os.remove(spec_file)
            print(f"已刪除 '{spec_file}' 檔案")
            
        print("--- 清理完成 ---")
        
    except OSError as e:
        print(f"清理時發生錯誤 (可能是檔案被占用): {e}")

print("--- 腳本執行完畢 ---")