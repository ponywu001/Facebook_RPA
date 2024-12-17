import os
from modules.utils import WebDriverUtils
from selenium.webdriver.common.by import By
import time
from selenium.common.exceptions import WebDriverException

class PostManager:
    def __init__(self, driver, worker_id=None):
        """
        初始化 PostManager 類別。
        :param driver: Selenium WebDriver 實例
        """
        self.driver = driver  # 初始化 WebDriver
        self.worker_id = worker_id  # 設置工作者 ID
        self.utils = WebDriverUtils(driver, worker_id)  # 初始化工具類，用於輔助操作
    
    def process_posts(self, posts, task_status):
        """
        處理發文的主流程
        """
        for post_data in posts:  # 遍歷每個貼文數據
            if task_status.get("stop"):  # 檢查任務是否需要停止
                break
            
            # 確認發文條件，只有發文操作為 "TRUE" 才發文
            if post_data["action"]:  # 如果發文操作為 "TRUE"
                post_type = post_data["type"]  # 獲取貼文類型
                group_url = post_data.get("group_url", "")  # 獲取社團 URL
                content = post_data["content"]  # 獲取貼文文字內容
                image_path = post_data["image_path"]  # 獲取貼文圖片路徑

                try:
                    self.publish(post_type, group_url, content, image_path)
                except Exception as e:  # 處理發文過程中的錯誤
                    print(f"Worker {self.worker_id}: 發文過程中出現錯誤: {e}")  # 打印發文過程中的錯誤
    
    def publish(self, post_type, group_url=None, content=None, image_path=None):
        """
        發佈貼文（個人或社團）。
        :param post_type: 貼文類型（"個人" 或 "社團"）
        :param group_url: 社團的 URL（僅限社團貼文）
        :param content: 貼文文字內容
        :param image_path: 貼文圖片路徑
        """
        try:
            # 檢查發文類型並執行對應操作
            if post_type == '個人':  # 如果貼文類型是個人貼文
                self.publish_personal_post({'content': content, 'image_path': image_path})  # 發佈個人貼文
                
            elif post_type == '社團':  # 如果貼文類型是社團貼文
                if not group_url:  # 如果社團 URL 不存在
                    print(f"Worker {self.worker_id}: 社團發文失敗，缺少社團 URL")  # 打印社團發文失敗，缺少社團 URL
                    return
                self.publish_group_post({'content': content, 'image_path': image_path}, group_url)  # 發佈社團貼文

            else:
                print(f"Worker {self.worker_id}: 發文失敗，未知的發文類型 {post_type}")  # 打印發文失敗，未知的發文類型

        except WebDriverException as e:  # 處理瀏覽器錯誤
            print(f"Worker {self.worker_id}: 瀏覽器錯誤（可能已被關閉或無法連接）")  # 打印瀏覽器錯誤
        except Exception as e:  # 處理其他未知錯誤
            print(f"Worker {self.worker_id}: 發文過程中出現未知錯誤: {e}")  # 打印發文過程中出現未知錯誤

    def publish_personal_post(self, post_data):
        """
        發佈單篇貼文。
        :param post_data: 包含貼文內容和圖片路徑的字典
        """
        print(f"Worker {self.worker_id}: 開始發佈貼文...")

        # 打開 Facebook 首頁
        self.driver.get("https://www.facebook.com/")
        
        # 點擊分享你的新鮮事
        if self.utils.retry_click(By.XPATH, "//span[contains(text(), '分享你的新鲜事吧') or contains(text(), '在想些什麼？')]"):  # 點擊分享你的新鮮事按鈕
            print(f"Worker {self.worker_id}: 已點擊分享你的新鮮事")  # 打印已點擊分享你的新鮮事
        else:  # 如果無法點擊分享你的新鮮事按鈕
            print(f"Worker {self.worker_id}: 無法點擊分享你的新鮮事按鈕")  # 打印無法點擊分享你的新鮮事按鈕
            return

        # 選擇分享對象
        if self.set_privacy():  # 設置分享對象
            print(f"Worker {self.worker_id}: 已設置分享對象")  # 打印已設置分享對象
        else:  # 如果無法設置分享對象
            print(f"Worker {self.worker_id}: 無法設置分享對象")  # 打印無法設置分享對象
            return

        # 點擊留言框
        text_area = self.utils.retry_find_element(By.XPATH, '//div[contains(@aria-placeholder, "在想些什麼") and @role="textbox"]')
        if text_area:  # 如果找到留言框
            self.driver.execute_script("arguments[0].scrollIntoView(true);", text_area)  # 將留言框滾動到可見區域
            text_area.click()  # 點擊留言框
        
        # 上傳圖片
        if post_data['image_path']:
            self.upload_image(post_data['image_path'])  # 上傳圖片
            print(f"Worker {self.worker_id}: 成功上傳圖片：{post_data['image_path']}")  # 打印成功上傳圖片
        
        self.utils.random_wait(1, 2)
        
        # 文字內容  
        if post_data['content']:
            self.input_text_content(text_area, post_data['content'])  # 輸入文字內容
            print(f"Worker {self.worker_id}: 成功輸入文字內容：{post_data['content']}")  # 打印成功輸入文字內容

        self.utils.random_wait(1, 2)

        # 點擊發佈按鈕
        if self.click_publish_button():  # 點擊發佈按鈕
            print(f"Worker {self.worker_id}: 點擊發佈按鈕成功，等待貼文完成...")  # 打印點擊發佈按鈕成功，等待貼文完成

            # 等待發佈完成的邏輯
            if self.wait_for_publish_success():  # 等待發佈完成
                print(f"Worker {self.worker_id}: 個人貼文發佈成功")  # 打印個人貼文發佈成功
            else:
                print(f"Worker {self.worker_id}: 貼文發佈過程中可能出現錯誤")  # 打印貼文發佈過程中可能出現錯誤
        else:
            print(f"Worker {self.worker_id}: 無法發佈個人貼文")  # 打印無法發佈個人貼文
    
    def publish_group_post(self, post_data, group_url):
        """
        發佈單篇社團貼文。
        :param post_data: 包含貼文內容和圖片路徑的字典
        :param group_url: 社團頁面的 URL
        """
        print(f"Worker {self.worker_id}: 開始發佈社團貼文...")

        # 打開社團頁面
        try:  # 嘗試打開社團頁面
            self.driver.get(group_url)  # 打開社團頁面
            print(f"Worker {self.worker_id}: 已進入社團頁面 {group_url}")  # 打印已進入社團頁面
        except Exception as e:  # 如果無法進入社團頁面
            print(f"Worker {self.worker_id}: 無法進入社團頁面，原因：{e}")  # 打印無法進入社團頁面，原因
            return
        
        # 點擊分享你的新鮮事
        if self.utils.retry_click(By.XPATH, '//span[contains(text(), "留個言吧……") or contains(@text(), "分享心情...")]'):
            print(f"Worker {self.worker_id}: 已點擊留言框")
        else:  # 如果無法點擊留言框
            print(f"Worker {self.worker_id}: 無法點擊留言框")  # 打印無法點擊留言框
            return
        
        # 點擊留言框
        text_area = self.utils.retry_find_element(By.XPATH, '//div[contains(@aria-label, "建立公開貼文……") or contains(@aria-label, "发布公开帖…")]')  # 找到留言框

        # 上傳圖片
        if post_data['image_path']:
            self.upload_image(post_data['image_path'])  # 上傳圖片
            print(f"Worker {self.worker_id}: 成功上傳圖片：{post_data['image_path']}")  # 打印成功上傳圖片
        
        self.utils.random_wait(1, 2)

        # 輸入文字內容
        if post_data['content']:
            self.input_text_content(text_area, post_data['content'])  # 輸入文字內容
            print(f"Worker {self.worker_id}: 成功輸入文字內容：{post_data['content']}")  # 打印成功輸入文字內容

        self.utils.random_wait(1, 2)
        
        # 點擊發佈按鈕
        if self.click_publish_button():  # 點擊發佈按鈕
            print(f"Worker {self.worker_id}: 點擊發佈按鈕成功，等待貼文完成...")  # 打印點擊發佈按鈕成功，等待貼文完成

            # 等待發佈完成的邏輯
            if self.wait_for_publish_success():  # 等待發佈完成
                print(f"Worker {self.worker_id}: 社團貼文發佈成功")  # 打印社團貼文發佈成功
            else:  # 如果無法等待發佈完成
                print(f"Worker {self.worker_id}: 貼文發佈過程中可能出現錯誤")  # 打印貼文發佈過程中可能出現錯誤
        else:  # 如果無法點擊發佈按鈕
            print(f"Worker {self.worker_id}: 無法點擊發佈按鈕")

    def set_privacy(self):
        """
        設置貼文的隱私設定為 "所有人"
        """
        try:
            # 開啟隱私設定並選擇 "所有人"
            self.utils.retry_find_element(By.XPATH, '//div[@role="dialog"]')  # 找到隱私設定對話框
            self.utils.retry_click(By.XPATH, '//div[contains(@aria-label, "編輯隱私設定。分享對象")]')  # 點擊編輯隱私設定
            self.utils.retry_click(By.XPATH, '//span[contains(text(), "所有 Facebook 的用戶和非用戶")]')  # 選擇 "所有人"
            self.utils.retry_click(By.XPATH, '//div[@aria-label="完成" or @aria-label="儲存" and @role="button"]')  # 點擊完成按鈕
            return True
        except Exception as e:  # 如果無法設置隱私設定
            return False

    def input_text_content(self, text_area, content):
        """
        輸入文字內容到留言框。
        :param text_area: 留言框的元素
        :param content: 要輸入的文字內容
        """
        try:  # 嘗試輸入文字內容
            for char in content:  # 遍歷每個字元
                text_area.send_keys(char)  # 輸入字元
                self.utils.random_wait(0.667, 0.1)  # 等待輸入字元
            return True
        except Exception as e:  # 如果無法輸入文字內容
            return False

    def upload_image(self, image_names):
        """
        上傳多張圖片到貼文。
        :param image_names: 逗號分隔的圖片檔名字串
        """
        try:
            # 確保圖片名稱以逗號分隔，並分解成清單
            image_files = [img.strip() for img in image_names.split(",")]
            
            # 點擊圖片上傳按鈕
            if self.utils.retry_click(By.XPATH, '//div[contains(@aria-label, "相片／影片") and @role="button"]'):
                for image_name in image_files:  # 遍歷每個圖片名稱
                    upload_input = self.utils.retry_find_element(By.XPATH, "//form[@method='POST']//input[@type='file' and contains(@accept, 'image/')]", retries=10, delay=1)  # 找到上傳圖片輸入框
                    
                    if upload_input:  # 如果找到上傳圖片輸入框
                        # 確保每個圖片名稱為絕對路徑
                        image_path = os.path.join(os.path.abspath("images"), image_name)

                        # 檢查圖片文件是否存在
                        if not os.path.exists(image_path):  # 如果圖片文件不存在
                            print(f"Worker {self.worker_id}: 圖片 {image_path} 不存在，跳過該圖片")  # 打印圖片不存在，跳過該圖片   
                            continue

                        upload_input.send_keys(image_path)  # 上傳圖片
                        self.utils.random_wait(3, 5)  # 等待每張圖片上傳的時間
                    else:  # 如果無法找到上傳圖片輸入框
                        print(f"Worker {self.worker_id}: 無法找到圖片上傳的 input 元素")  # 打印無法找到圖片上傳的 input 元素   
                        return False

                # 等待圖片上傳完成
                success = self.utils.retry_find_element(
                    By.XPATH, '//span[contains(text(), "新增相片／影片")]', retries=10, delay=1
                )

                self.utils.random_wait(8, 10)  # 等待圖片上傳完成

                if success:  # 如果成功上傳圖片
                    print(f"Worker {self.worker_id}: 圖片已成功上傳")  # 打印圖片已成功上傳
                    return True
                else:  # 如果無法成功上傳圖片
                    print(f"Worker {self.worker_id}: 等待圖片上傳完成超時")  # 打印等待圖片上傳完成超時
                    return False
                
            return False
        except Exception as e:
            print(f"Worker {self.worker_id}: 圖片上傳過程中出現錯誤: {e}")
            return False

    def click_publish_button(self):
        """
        使用 JavaScript 點擊發佈按鈕以發佈貼文。
        """
        try:  # 嘗試點擊發佈按鈕
            publish_button = self.utils.retry_find_element(By.XPATH, "//span[text()='發佈'] | //span[text()='发布']")  # 找到發佈按鈕
            if publish_button:  # 如果找到發佈按鈕
                self.driver.execute_script("arguments[0].click();", publish_button)  # 點擊發佈按鈕
                return True
            return False
        except Exception as e:  # 如果無法點擊發佈按鈕
            return False
    
    def wait_for_publish_success(self, timeout=60, check_interval=2):
        """
        等待貼文完成 (檢測發佈按鈕消失)
        :param timeout: 最大等待時間
        :param check_interval: 每次檢查的間隔
        :return: 是否成功完成發佈
        """
        elapsed_time = 0  # 計時器
        publish_button_xpath = "//span[text()='發佈'] | //span[text()='发布']"  # 發佈按鈕的 XPath

        while elapsed_time < timeout:
            try:
                # 嘗試查找發佈按鈕
                self.driver.find_element(By.XPATH, publish_button_xpath)  # 查找發佈按鈕
            except Exception:
                # 如果找不到按鈕，認為發佈已完成
                return True

            time.sleep(check_interval)  # 等待檢查間隔
            elapsed_time += check_interval  # 增加計時器

        return False







