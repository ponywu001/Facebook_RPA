from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from modules.utils import WebDriverUtils 
import json
import requests
from urllib.parse import urlparse
import os
import random
import time

class ClickManager:
    def __init__(self, driver, worker_id):
        self.driver = driver  # 初始化 WebDriver
        self.worker_id = worker_id  # 設置工作者 ID
        self.utils = WebDriverUtils(driver, worker_id)  # 初始化工具類，用於輔助操作

    def process_clicks(self, clicks_data, task_status):
        """
        處理跳轉資料。
        :param crawls_data: 跳轉資料列表
        """
        for click_data in clicks_data:  # 遍歷每條爬蟲數據
            if task_status.get("stop"):  # 檢查任務是否需要停止
                break

            if not click_data.get("action"):  # 如果沒有動作
                continue  # 跳過

            # click_type = click_data.get("type")  # 獲取爬蟲類型
            url = click_data.get("url")  # 獲取 URL

            try:
                self.click_url_navigate_scroll(url)  # 點擊 URL 並導航到貼文頁面
            except Exception as e:            # 如果發生錯誤
                print(f"Worker {self.worker_id}: 點擊 URL 時發生錯誤: {e}")  # print點擊 URL 時的錯誤
            
    
    def click_url_navigate_scroll(self, url):
        """
        點擊 URL 並導航到新頁面。
        """
        print(f"Worker {self.worker_id}: 正在開啟貼文: {url}")
        self.driver.get(url)  # 打開 URL
        
        random_stay_time = random.randint(6, 8)
        print(f"Worker {self.worker_id} 隨機停留 {random_stay_time} 秒")
        time.sleep(random_stay_time)  # 等待隨機時間
        
        # wait = WebDriverWait(self.driver, 30)
        # like_button = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//div[@aria-label='赞' or @aria-label='移除赞' or @aria-label='讚' or @aria-label='移除讚']")))
        # time.sleep(3)
        # like_button = self.driver.find_element(By.XPATH, "//div[@role='dialog']//div[@aria-label='赞' or @aria-label='移除赞' or @aria-label='讚' or @aria-label='移除讚']")
        like_button = self.utils.retry_find_element(By.XPATH, "//div[@role='dialog']//div[@aria-label='赞' or @aria-label='移除赞' or @aria-label='讚' or @aria-label='移除讚']", retries=5)

        if like_button:  # 如果找到按鈕
            like_button.click()  # 點擊按鈕
            print(f"Worker {self.worker_id}: 成功按讚")
            
            # 隨機停留時間並模擬頁面滑動
            random_stay_time = random.randint(3, 5)
            print(f"Worker {self.worker_id} 按讚後隨機停留 {random_stay_time} 秒")
            time.sleep(random_stay_time)  # 等待隨機時間
            
            # 获取 Like 按钮的位置和大小
            location = like_button.location
            size = like_button.size

            # 模擬滑鼠點擊 URL 按鈕
            actions = ActionChains(self.driver)
            actions.move_by_offset(location['x'], location['y']-3*size['height'])  # 向上移动

            actions.click()  # 点击该位置
            actions.perform()
            
            self.driver.switch_to.window(self.driver.window_handles[1])
            
            # 隨機停留時間並模擬頁面滑動
            random_stay_time = random.randint(60, 120)
            print(f"Worker {self.worker_id} 隨機停留時間: {random_stay_time} 秒")
            start_time = time.time()

            while time.time() - start_time < random_stay_time:
                # 隨機向下滑動一段距離
                scroll_distance = random.randint(200, 400)  # 滑動距離
                self.driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
                print(f"Worker {self.worker_id}: 向下滑動: {scroll_distance} 像素")
                time.sleep(random.uniform(3, 5))  # 等待 3-5 秒，模擬人類操作
            

