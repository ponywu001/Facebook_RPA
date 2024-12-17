import time
import random
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.by import By

class WebDriverUtils:
    def __init__(self, driver, worker_id=None):
        """
        初始化 WebDriverUtils 類別
        :param driver: WebDriver 實例
        :param worker_id: 工作者 ID，用於打印日誌
        """
        self.driver = driver  # 初始化 WebDriver 實例
        self.worker_id = worker_id  # 初始化 worker_id

    def retry_find_element(self, by, value, retries=5, delay=2, timeout=10):
        """
        重試等待某個元素的出現
        :param driver: WebDriver 實例
        :param by: 定位方式 (e.g., By.ID, By.XPATH)
        :param value: 定位的值
        :param retries: 最大重試次數，默認為 5 次
        :param delay: 每次重試之間的延遲（秒），默認為 2 秒
        :param timeout: 每次重試時的等待時間，默認為 10 秒
        :return: 定位到的元素，或 None 如果所有重試均失敗
        """
        for attempt in range(retries):  # 遍歷重試次數
            try:  # 嘗試查找元素
                element = WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, value)))  # 等待元素出現
                return element
            except TimeoutException:  # 如果出現 TimeoutException 錯誤
                time.sleep(delay)  # 等待 delay 秒
        print(f"Worker {self.worker_id}: 重試等待元素失敗，超出最大次數")  # print錯誤信息
        return None  # 返回 None

    def retry_click(self, by, value, retries=5, delay=2, timeout=10):
        """
        重試點擊操作
        :param driver: WebDriver 實例
        :param by: 定位方式 (e.g., By.ID, By.XPATH)
        :param value: 定位的值
        :param retries: 最大重試次數，默認為 5 次
        :param delay: 每次重試之間的延遲（秒），默認為 2 秒
        :param timeout: 每次重試時的等待時間，默認為 10 秒
        :return: True 如果點擊成功，或 False 如果所有重試均失敗
        """
        for attempt in range(retries):  # 遍歷重試次數
            try:  # 嘗試點擊元素
                element = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((by, value)))  # 等待元素可點擊
                element.click()  # 點擊元素
                return True  # 返回 True
            except (TimeoutException, ElementClickInterceptedException) as e:  # 如果出現 TimeoutException 或 ElementClickInterceptedException 錯誤
                time.sleep(delay)  # 等待 delay 秒
        print(f"Worker {self.worker_id}: 重試點擊操作失敗，超出最大次數")  # print錯誤信息
        return False  # 返回 False
    
    def scroll_to_element(self, element):
        """
        滾動到指定的元素，使其出現在可視範圍內。
        :param element: 要滾動到的 WebElement
        """
        try:  # 嘗試滾動到元素
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element
            )
        except Exception as e:  # 如果出現錯誤
            print(f"Worker {self.worker_id}: 滾動到元素時發生錯誤: {e}")  # print錯誤信息
        
    def retry_find_elements(self, by, value, retries=5, delay=1, timeout=10):
        """
        多次嘗試查找元素組。
        :param by: 定位方式，例如 By.XPATH, By.ID 等。
        :param value: 定位的值，例如元素的 XPATH。
        :param retries: 重試次數，默認為 5。
        :param delay: 每次重試間隔時間，默認為 1 秒。
        :param timeout: 等待元素的最大超時時間，默認為 10 秒。
        :return: 匹配的元素列表，如果未找到則返回空列表。
        """
        for attempt in range(retries):  # 遍歷重試次數
            try:  # 嘗試查找元素
                # 使用 WebDriverWait 等待元素
                elements = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_all_elements_located((by, value))
                )  # 等待元素出現
                print(f"Worker {self.worker_id}: 成功找到元素組，共找到 {len(elements)} 個")  # print成功信息
                return elements  # 返回元素列表
            except Exception as e:  # 如果出現錯誤
                print(f"Worker {self.worker_id}: 第 {attempt + 1} 次嘗試查找元素組失敗: {e}")  # print錯誤信息
                time.sleep(delay)  # 等待 delay 秒

        print(f"Worker {self.worker_id}: 查找元素組失敗，定位方式: {by}, 值: {value}")  # print錯誤信息
        return []  # 返回空列表
    
    def scroll_to_bottom(self, delay=0.5, timeout=15):
        """
        滾動到頁面底部，直到 15 秒內頁面高度不再改變。
        :param delay: 每次滾動之間的延遲時間，默認為 0.5 秒。
        :param timeout: 超時時間（秒），如果頁面高度在該時間內未改變則停止滾動，默認為 15 秒。
        """
        print(f"Worker {self.worker_id}: 開始滾動到頁面底部...")  # 打印開始信息    
        start_time = time.time()  # 記錄開始時間
        last_change_time = start_time  # 記錄最後一次高度變化的時間
        last_height = self.driver.execute_script("return document.body.scrollHeight")  # 獲取初始頁面高度

        while True:
            # 滾動到底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # 滾動到底部
            time.sleep(delay)  # 等待新內容加載
            new_height = self.driver.execute_script("return document.body.scrollHeight")  # 獲取新頁面高度

            # 檢查是否有新內容
            if new_height == last_height:
                # 如果超過 timeout 時間沒有高度變化，停止滾動
                if time.time() - last_change_time > timeout:  
                    print(f"Worker {self.worker_id}: 已到達頁面底部")
                    break
            else:  # 如果高度改變
                # 更新最後變化時間
                last_change_time = time.time()

            # 更新 last_height 為新高度
            last_height = new_height

    def scroll_modal_content(self, modal, delay=1, timeout=15):
        """
        滾動互動視窗內容，直到到底部或超時為止。
        :param modal: 主模態框的 WebElement。
        :param delay: 每次滾動之間的延遲時間，默認為 1 秒。
        :param timeout: 超時時間（秒），如果超過該時間則結束滾動，默認為 15 秒。
        """
        print(f"Worker {self.worker_id}: 開始滾動到頁面底部...")
        try:
            time.time()  # 記錄開始時間
            last_change_time = time.time()  # 記錄最後一次變化的時間

            # 獲取目標可滾動元素
            xpath = "/html/body/div[1]/div/div[1]/div/div[5]/div/div/div[2]/div/div/div/div/div/div/div/div[2]"  # 目標元素的 XPath
            scrollable_container = modal.find_element(By.XPATH, xpath)  # 找到目標元素  

            # 初始記錄(留言)數量
            initial_div_count = len(scrollable_container.find_elements(By.CSS_SELECTOR, "div.html-div"))  # 獲取初始留言數量

            while True:  # 無限循環
                # 滾動操作
                self.driver.execute_script("arguments[0].scrollTop += 500", scrollable_container)  # 滾動 500 像素  

                # 等待新內容加載，使用顯式等待來確保新元素已經出現
                WebDriverWait(self.driver, delay).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.html-div"))
                )

                new_div_count = len(scrollable_container.find_elements(By.CSS_SELECTOR, "div.html-div"))  # 獲取新留言數量

                # 如果元素數量未變化
                if new_div_count == initial_div_count:
                    # 如果已經等待超過 15 秒，則認為已經到達底部
                    if time.time() - last_change_time > timeout:  
                        print(f"Worker {self.worker_id}: 15秒內未發現新元素，滾動結束，可能已到達底部")
                        return True
                else:  # 如果元素數量發生變化
                    # 如果元素數量發生變化，重設倒計時
                    initial_div_count = new_div_count
                    last_change_time = time.time()  # 更新最後一次變化的時間
                
                time.sleep(delay)  # 等待 delay 秒

        except Exception as e:  # 如果出現錯誤
            print(f"Worker {self.worker_id}: 互動視窗滾動時出現錯誤: {e}")  # print 錯誤信息
            return False

    # 隨機等待時間
    def random_wait(self, min_time=0.5, max_time=2.5):
        """
        產生隨機等待時間
        """
        time.sleep(random.uniform(min_time, max_time))  
