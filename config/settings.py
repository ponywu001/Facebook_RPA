import os
from tkinter import Tk, filedialog
import sys
from modules.log_manager import LogManager

# 定義 BASE_DIR 作為項目根目錄
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 設定 Cookies 資料夾的預設路徑
COOKIES_FOLDER = os.path.join(BASE_DIR, "data", "cookies")

# 設定 Log 資料夾的預設路徑
LOG_DIR = os.path.join(BASE_DIR, "logs")

# 初始化 LogManager
log_manager = LogManager(log_dir="logs/", log_prefix="facebook_rpa")
logger = log_manager.get_logger()

# 隱藏主視窗並顯示提醒訊息
root = Tk()
root.withdraw()

print("請選擇您要使用的 Excel 檔案...")

# 使用 tkinter 文件選擇器來選擇 Excel 檔案
excel_path = filedialog.askopenfilename(title="選擇 Excel 檔案", filetypes=[("Excel Files", "*.xlsx *.xls")])

# 使用選擇的 Excel 檔案路徑或預設路徑
if excel_path:
    EXCEL_PATH = excel_path
    print(f"選擇的 Excel 檔案路徑：{EXCEL_PATH}")
else:
    print(f"未選擇檔案，程式即將退出...")
    sys.exit(0)

root.destroy()  # 關閉 Tkinter 主視窗

# 用戶輸入最大多開數量
def get_max_workers():
    try:
        max_workers = input("請輸入最大多開數量 (1-10，預設為 1): ").strip()
        if not max_workers:
            print("未輸入值，使用預設值 1")
            return 1
        max_workers = int(max_workers)
        if 1 <= max_workers <= 10:
            return max_workers
        elif max_workers < 1:
            print("輸入值太小，使用預設值 1")
            return 1
        else:
            print("輸入值超出範圍，使用預設值 10")
            return 10
    except ValueError:
        print("輸入無效，請輸入數字。使用預設值 1")
        return 1

# 設置 max_workers
MAX_WORKERS = get_max_workers()
print(f"最大多開數量已設定為：{MAX_WORKERS}")