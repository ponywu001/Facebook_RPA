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

class NavigateManager:
    def __init__(self, driver, worker_id):
        self.driver = driver  # 初始化 WebDriver
        self.worker_id = worker_id  # 設置工作者 ID
        self.utils = WebDriverUtils(driver, worker_id)  # 初始化工具類，用於輔助操作

    def process_navigates(self, navigates_data, task_status):
        """
        處理跳轉資料。
        :param navigates_data: 跳轉資料列表
        """
        for navigate_data in navigates_data:  # 遍歷每條爬蟲數據
            if task_status.get("stop"):  # 檢查任務是否需要停止
                break

            if not navigate_data.get("action"):  # 如果沒有動作
                continue  # 跳過

            # click_type = click_data.get("type")  # 獲取爬蟲類型
            url = navigate_data.get("url")  # 獲取 URL
            out_url = navigate_data.get("out_url")  # 獲取外部 URL
            
            try:
                self.navigate_out_url(url, out_url)  # 點擊 URL 並導航到貼文頁面
            except Exception as e:            # 如果發生錯誤
                print(f"Worker {self.worker_id}: 跳轉 URL 時發生錯誤: {e}")  # print點擊 URL 時的錯誤
            
    
    def navigate_out_url(self, url, out_url):
        """
        跳轉 URL 導航到新頁面。
        """
        print(f"Worker {self.worker_id}: 正在開啟貼文: {url}")
        self.driver.get(url)  # 打開 URL
        
        random_stay_time = random.randint(6, 8)
        print(f"Worker {self.worker_id} 隨機停留 {random_stay_time} 秒")
        time.sleep(random_stay_time)  # 等待隨機時間
        
        like_button = self.utils.retry_find_element(By.XPATH, "//div[@role='dialog']//div[@aria-label='赞' or @aria-label='移除赞' or @aria-label='讚' or @aria-label='移除讚']", retries=5)

        if like_button:  # 如果找到按鈕
            # 確保元素進入視野
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_button)

            # 確認是否可點擊
            aria_label = like_button.get_attribute("aria-label")  # 獲取按鈕的 aria-label 屬性
            if aria_label in ["移除讚", "移除赞"]:  # 如果按讚已經存在
                print(f"Worker {self.worker_id}: 貼文已按過讚，無需重複操作")
            else:
                self.driver.execute_script("arguments[0].click();", like_button)  # 點擊按讚按鈕
                print(f"Worker {self.worker_id}: 成功按讚")
            
            # 隨機停留時間並模擬頁面滑動
            random_stay_time = random.randint(3, 5)
            print(f"Worker {self.worker_id} 按讚後隨機停留 {random_stay_time} 秒")
            time.sleep(random_stay_time)  # 等待隨機時間
            
            print(f"Worker {self.worker_id}: 正在開啟網站: {out_url}")
            self.driver.get(out_url)  # 打開外部 URL
                     
            # 隨機停留時間並模擬頁面滑動
            random_stay_time = random.randint(140, 200)
            print(f"Worker {self.worker_id} 隨機停留時間: {random_stay_time} 秒")
            start_time = time.time()

            while time.time() - start_time < random_stay_time:
                # 隨機向下滑動一段距離
                scroll_distance = random.randint(200, 400)  # 滑動距離
                scroll_wait_time = random.uniform(3, 5)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
                time.sleep(scroll_wait_time)  # 等待 3-5 秒，模擬人類操作
                print(f"Worker {self.worker_id}: 向下滑動: {scroll_distance} 像素，並等待 {scroll_wait_time} 秒")
            

