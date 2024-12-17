from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from modules.utils import WebDriverUtils
import requests 
from urllib.parse import urlparse
from selenium.common.exceptions import TimeoutException


class CommentManager:
    """
    負責處理 Facebook 貼文的互動操作，包括按讚、留言和分享。
    """
    def __init__(self, driver, worker_id=None):
        """
        初始化 CommentManager
        :param driver: Selenium WebDriver 實例
        :param worker_id: 工作者 ID，用於打印日誌
        """
        self.driver = driver # 初始化 WebDriver
        self.utils = WebDriverUtils(driver, worker_id)  # 初始化工具類，用於輔助操作
        self.worker_id = worker_id  # 設置工作者 ID

    def process_comments(self, comments_data, task_status):
        """
        根據提供的留言資料，按順序處理按讚、留言和分享操作。
        :param comments_data: 留言資料的列表
        :param task_status: 用於監控任務狀態的字典
        """
        for comment_data in comments_data:  # 遍歷每條留言數據
            if task_status.get("stop"):  # 檢查任務是否需要停止
                break

            url = comment_data.get("url")  # 獲取貼文的 URL
            try:
                # 解開縮網址並判斷類型
                expanded_url = self._expand_url(url)  # 解開縮網址
                post_type = self._determine_post_type(expanded_url)  # 判斷貼文類型
                print(f"Worker {self.worker_id}: 開始處理貼文 URL: {url}")  # 判斷貼文類型

                self.driver.get(url)  # 打開貼文 URL

                # 按讚
                if comment_data.get("like_action"):  # 如果需要按讚
                    self._like_post(post_type)  # 執行按讚操作
                
                # 分享
                if comment_data.get("share_action"):  # 如果需要分享
                    self._share_post(post_type)  # 執行分享操作

                self.utils.random_wait(1, 2)  # 等待一段隨機時間

                # 分享
                if comment_data.get("share_action"):  # 再次檢查是否需要分享（似乎是多餘的重複檢查）
                    self._share_post(post_type)  # 執行分享操作
                
                self.utils.random_wait(1, 2)  # 再次等待一段隨機時間

                # 留言
                if comment_data.get("comment_action"):  # 如果需要留言
                    comment_text = comment_data.get("content", "").strip()  # 獲取留言內容並去除空白
                    if comment_text:  # 如果留言內容不為空
                        self._comment_on_post(comment_text, post_type)  # 執行留言操作
                    else:
                        print(f"Worker {self.worker_id}: 留言操作啟用但未提供留言內容，跳過留言")

            except Exception as e:  # 捕獲任何異常
                print(f"Worker {self.worker_id}: 處理貼文時發生錯誤: {e}")

    def _like_post(self, post_type):
        """
        按讚功能，直接嘗試點擊「讚」按鈕。
        """
        try:
            # 如果是社團貼文，使用社團的按鈕 XPath
            if post_type == "group":
                like_button = self.utils.retry_find_element(By.XPATH, "//div[@aria-label='赞' or @aria-label='移除赞' or @aria-label='讚' or @aria-label='移除讚']", retries=5)
                
            # 如果是個人貼文，使用個人貼文的按鈕 XPath（位於 role="dialog" 節點內）
            else:
                like_button = self.utils.retry_find_element(By.XPATH, "//div[@role='dialog']//div[@aria-label='赞' or @aria-label='移除赞' or @aria-label='讚' or @aria-label='移除讚']", retries=5)

            if like_button:  # 如果找到按讚按鈕
                # 確保元素進入視野
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_button)

                # 確認是否可點擊
                aria_label = like_button.get_attribute("aria-label")  # 獲取按鈕的 aria-label 屬性
                if aria_label in ["移除讚", "移除赞"]:  # 如果按讚已經存在
                    print(f"Worker {self.worker_id}: 貼文已按過讚，無需重複操作")
                else:
                    self.driver.execute_script("arguments[0].click();", like_button)  # 點擊按讚按鈕
                    print(f"Worker {self.worker_id}: 成功按讚")

            else:  # 如果未找到按讚按鈕
                print(f"Worker {self.worker_id}: 未找到按讚按鈕")

        except Exception as e:  # 捕獲任何異常
            print(f"Worker {self.worker_id}: 按讚過程中出現錯誤: {e}")

    def _comment_on_post(self, comment_text, post_type):
        """
        留言功能。
        :param comment_text: 要發佈的留言內容
        """
        try:
            # 如果是社團貼文，檢查是否有待審內容限制
            if post_type == "group":
                pending_limit_message = self.utils.retry_find_element(
                    By.XPATH,
                    "//span[contains(text(), '你在此社團的待審內容已達到數量上限') or contains(text(), '你在这个小组中的待审核内容已达上限')]",
                    retries=1,
                )
                if pending_limit_message:  # 如果有待審限制
                    print(f"Worker {self.worker_id}: 無法留言，因社團待審內容已達到數量上限，跳過留言")
                    return
            
            comment_box = self.utils.retry_find_element(
                By.XPATH,
                "//div[@role='textbox' and (contains(@aria-label, '留言') or contains(@aria-label, '评论'))]",
                retries=5,
            )
                 
            if not comment_box:  # 如果未找到留言框
                print(f"Worker {self.worker_id}: 未找到留言框")
                return
            
            # 滾動到留言框並點擊
            self.driver.execute_script("arguments[0].scrollIntoView(true);", comment_box)
            self.driver.execute_script("arguments[0].click();", comment_box)

            for char in comment_text:  # 逐字輸入留言內容
                comment_box.send_keys(char)  
                self.utils.random_wait(0.667, 0.1)  # 等待一段隨機時間
            comment_box.send_keys(Keys.RETURN)  # 發送留言
            print(f"Worker {self.worker_id}: 成功留言: {comment_text}")
        except Exception as e:  # 捕獲任何異常
            print(f"Worker {self.worker_id}: 留言過程中出現錯誤: {e}")

    def _share_post(self, post_type):
        """
        分享功能。
        """
        try:
            if post_type == "group":  # 如果是社團貼文
                share_button = self.utils.retry_find_element(
                    By.XPATH, "//div[contains(@aria-label, '傳送給朋友') or contains(@aria-label, '发送给好友')]", retries=5
                )
            else:  # 如果是個人貼文
                share_button = self.utils.retry_find_element(
                    By.XPATH, "//div[@role='dialog']//div[contains(@aria-label, '傳送給朋友') or contains(@aria-label, '发送给好友')]", retries=5
                )

            if not share_button:  # 如果未找到分享按鈕
                print(f"Worker {self.worker_id}: 未找到分享按鈕")
                return

            # 確保按鈕可見並嘗試點擊
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", share_button)  # 滾動到分享按鈕
                self.driver.execute_script("arguments[0].click();", share_button)  # 點擊分享按鈕 
                print(f"Worker {self.worker_id}: 成功點擊分享按鈕，發佈中......")
            except Exception as e:  # 捕獲任何異常
                print(f"Worker {self.worker_id}: 分享按鈕初次點擊失敗，嘗試強制點擊: {e}")

            immediately_share_button = self.utils.retry_find_element(  # 找到立即分享按鈕
                By.XPATH, "//span[text()='立即分享']", retries=5
            )

            if immediately_share_button:  # 如果找到立即分享按鈕    
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", immediately_share_button)  # 滾動到立即分享按鈕
                self.driver.execute_script("arguments[0].click();", immediately_share_button)  # 點擊立即分享按鈕

                # 等待成功訊息顯示
                success_message = self.utils.retry_find_element(By.XPATH, "//span[contains(text(), '已分享到你的個人檔案')] | //span[contains(text(), '已分享到你的个人主页')]", retries=6)
                if success_message:  # 如果找到成功分享訊息
                    print(f"Worker {self.worker_id}: 成功分享")
                else:  # 如果未找到成功分享訊息
                    print(f"Worker {self.worker_id}: 未找到成功分享訊息，可能未成功")
            else:
                print(f"Worker {self.worker_id}: 未找到最終分享按鈕")

        except Exception as e:  # 捕獲任何異常
            print(f"Worker {self.worker_id}: 分享過程中出現錯誤: {e}")
    
    def _expand_url(self, url):
        """
        解開縮網址
        :param url: 短鏈接 URL
        :return: 解開後的完整 URL
        """
        try:  # 嘗試解開縮網址
            response = requests.head(url, allow_redirects=True, timeout=10)  # 發送 HTTP HEAD 請求
            expanded_url = response.url  # 獲取最終的 URL
            return expanded_url
        except requests.RequestException as e:
            print(f"Worker {self.worker_id}: 無法解開縮網址: {url}，錯誤: {e}")
            return url  # 如果解開失敗，返回原始 URL

    def _determine_post_type(self, url):
        """
        判斷是個人貼文還是社團貼文
        :param url: 解開後的完整 URL
        :return: "group" 或 "personal"
        """
        try:  # 嘗試判斷貼文類型
            path = urlparse(url).path  # 獲取 URL 的路徑部分
            if "/groups/" in path:  # 如果路徑包含 "/groups/"
                return "group"  # 返回社團貼文
            else:  # 如果路徑不包含 "/groups/"  
                return "personal"  # 返回個人貼文
        except Exception as e:  # 捕獲任何異常
            print(f"Worker {self.worker_id}: 無法判斷貼文類型，錯誤: {e}")
            return "unknown"
