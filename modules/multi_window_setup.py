from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from screeninfo import get_monitors
from ctypes import windll
import os

class MultiWindowSetup:
    def __init__(self, columns=5, rows=2, horizontal_margin=50, browser_path="C:/Program Files/Mozilla Firefox/firefox.exe"):
        """初始化窗口設置參數。"""
        self.columns = columns  # 設置列數  
        self.rows = rows  # 設置行數
        self.horizontal_margin = horizontal_margin  # 設置水平間距
        self.browser_path = browser_path  # 設置瀏覽器路徑
        self.positions, self.window_size = self.calculate_positions()  # 計算分頁位置和尺寸

    def calculate_positions(self):
        """計算窗口位置和尺寸。"""
        monitor = get_monitors()[0]  # 獲取主監視器
        screen_width = monitor.width  # 獲取螢幕寬度
        screen_height = monitor.height  # 獲取螢幕高度

        # 獲取縮放比例
        scaling_factor = self._get_scaling_factor()  # 獲取縮放比例

        print(f"螢幕寬度：{screen_width}，螢幕高度：{screen_height}，縮放比例：{scaling_factor}")

        window_width = int((screen_width - (self.columns - 1) * self.horizontal_margin) // self.columns / scaling_factor)  # 計算分頁寬度
        window_height = int((screen_height // self.rows) / scaling_factor)  # 計算分頁高度

        positions = [
            (col * (window_width + self.horizontal_margin), row * window_height)  # 計算分頁位置
            for row in range(self.rows)  # 遍歷行數
            for col in range(self.columns)  # 遍歷列數
        ]
        return positions, (window_width, window_height)  # 返回分頁位置和尺寸
    
    def _get_scaling_factor(self):
        """獲取 Windows 的縮放比例"""
        # 確保應用程序設置為 DPI 感知
        DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE = -4
        windll.user32.SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE)  # 設置 DPI 感知
        
        # 創建一個虛擬窗口以獲取 DPI
        hdc = windll.user32.GetDC(0)  # 獲取屏幕上下文
        dpi = windll.gdi32.GetDeviceCaps(hdc, 90)  # 獲取屏幕 DPI（Pixels per Inch）
        windll.user32.ReleaseDC(0, hdc)  # 釋放上下文

        # Windows 默認 DPI 是 96
        scaling_factor = dpi / 96.0
        return scaling_factor
    
    def setup_driver(self, position):
        """初始化 Firefox 驅動器並設置窗口位置和大小。"""
        geckodriver_path = "./geckodriver.exe"  # 設置 geckodriver 路徑
        if not os.path.exists(geckodriver_path):  # 如果 geckodriver 不存在
            geckodriver_path = GeckoDriverManager().install()  # 安裝 geckodriver

        # 設置 Firefox 選項並指定執行檔位置
        options = Options()
        # options.add_argument("--headless")
        options.add_argument(f"--width={self.window_size[0]}")  # 設置分頁寬度
        options.add_argument(f"--height={self.window_size[1]}")  # 設置分頁高度
        options.binary_location = self.browser_path  # 設置瀏覽器路徑

        driver = webdriver.Firefox(service=Service(geckodriver_path), options=options)  # 初始化 Firefox 驅動器
        driver.install_addon("foxyproxy_standard-7.4.2.xpi", temporary=True)  # 安裝 FoxyProxy 擴充套件 

        # 設置視窗位置和大小
        driver.set_window_position(*position)  # 設置分頁位置
        driver.set_window_size(*self.window_size)  # 設置分頁大小
        return driver