from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from modules.utils import WebDriverUtils 
import json
import requests
from urllib.parse import urlparse
import os

class CrawlManager:
    def __init__(self, driver, worker_id):
        self.driver = driver  # 初始化 WebDriver
        self.worker_id = worker_id  # 設置工作者 ID
        self.utils = WebDriverUtils(driver, worker_id)  # 初始化工具類，用於輔助操作

    def process_crawls(self, crawls_data, task_status):
        """
        處理爬蟲資料。
        :param crawls_data: 爬蟲資料列表
        """
        for crawl_data in crawls_data:  # 遍歷每條爬蟲數據
            if task_status.get("stop"):  # 檢查任務是否需要停止
                break

            if not crawl_data.get("action"):  # 如果沒有動作
                continue  # 跳過

            crawl_type = crawl_data.get("type")  # 獲取爬蟲類型
            url = crawl_data.get("url")  # 獲取 URL

            expanded_url = self._expand_url(url)  # 展開 URL
            post_type = self._determine_post_type(expanded_url)  # 確定貼文類型

            try:
                if crawl_type == "爬文章":
                    if post_type == "personal":  # 如果是個人貼文
                        self.fetch_users_from_personal_post(url)  # 從個人貼文抓取用戶資訊
                    elif post_type == "group":  # 如果是社團貼文
                        self.fetch_users_from_group_post(url)  # 從社團貼文抓取用戶資訊
                elif crawl_type == "爬社團名單":  # 如果是爬社團名單
                    self.fetch_group_members(url)  # 從社團抓取成員資料     
                else:
                    print(f"Worker {self.worker_id}: 未知的爬蟲類型: {crawl_type}")  # print 未知的爬蟲類型   
            except Exception as e:
                print(f"Worker {self.worker_id}: 爬蟲操作時發生錯誤: {e}")  # print爬蟲操作時的錯誤
    
    def fetch_users_from_personal_post(self, url):
        """
        從貼文抓取用戶資訊。
        """
        print(f"Worker {self.worker_id}: 正在處理個人貼文...")
        try:  # 嘗試從貼文抓取用戶資訊
            self.driver.get(url)  # 打開貼文 URL    
            print(f"Worker {self.worker_id}: 正在抓取貼文 URL: {url}")

            # 點擊「最熱門留言」
            sort_button = self.utils.retry_find_element(By.XPATH, "//span[text()='最熱門留言' or text()='最相關' or text()='最相关']")  # 找到最熱門留言按鈕    
            if sort_button:  # 如果找到最熱門留言按鈕
                self.utils.scroll_to_element(sort_button)  # 滾動到最熱門留言按鈕
                sort_button.click()  # 點擊最熱門留言按鈕

                # 點擊「由新到舊」
                new_to_old_button = self.utils.retry_find_element(By.XPATH, "//span[text()='由新到舊' or text()='由新到旧']")  # 找到由新到舊按鈕   
                if new_to_old_button:  # 如果找到由新到舊按鈕
                    new_to_old_button.click()  # 點擊由新到舊按鈕

            # 檢測是否有互動視窗，並進行操作
            modal = self.utils.retry_find_element(By.XPATH, "//div[@role='dialog']", retries=5, delay=2, timeout=10)  # 找到互動視窗
            self.utils.scroll_modal_content(modal)  # 滾動互動視窗內容

            # 展開所有回覆
            self._click_all_replies()  # 點擊所有回覆按鈕
            print(f"Worker {self.worker_id}: 已展開所有回覆")  # print 已展開所有回覆

            # 抓取留言區塊
            comment_blocks = self.utils.retry_find_elements(By.XPATH, "//div[contains(@aria-label, '的留言') or contains(@aria-label, '评论者')]")  # 找到留言區塊
            print(f"Worker {self.worker_id}: 已找到 {len(comment_blocks)} 則留言")  # print 已找到留言數量

            # 初始化結果列表
            result_data = []

            if comment_blocks:  # 如果找到留言區塊  
                total_blocks = len(comment_blocks)  # 獲取留言區塊數量
                print(f"Worker {self.worker_id}: 開始抓取用戶資訊，共 {total_blocks} 則留言...")  # print 開始抓取用戶資訊

                # 逐一處理每個留言區塊
                for index, block in enumerate(comment_blocks, start=1):  # 遍歷每個留言區塊 
                    try:
                        # 提取用戶資訊
                        user_info = self._extract_user_info([block])[0]  # 單個區塊提取
                        result_data.append({  # 添加用戶資訊到結果列表
                            "keywords": url,  # 關鍵詞
                            "group_name": "",  # 群組名稱
                            "fb_user_id": user_info.get("user_id"),  # 用戶 ID
                            "fb_user_name": user_info.get("name"),  # 用戶名稱
                            "user_photo": user_info.get("photo"),  # 用戶照片
                            "fb_user_url": f"https://www.facebook.com/{user_info.get('user_id')}",  # 用戶 URL
                            "subject": user_info.get("subject"),  # 用戶職位/描述
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 時間
                        })

                        # 打印進度
                        print(f"Worker {self.worker_id}: 已完成 {index}/{total_blocks} ({(index / total_blocks) * 100:.2f}%)")

                    except Exception as block_error:  # 處理留言區塊時的錯誤
                        print(f"Worker {self.worker_id}: 處理第 {index} 則留言時發生錯誤: {block_error}")

            # 儲存結果到檔案
            self._save_crawl_results(result_data, post_type="personal")  # 儲存結果到檔案

        except Exception as e:
            print(f"Worker {self.worker_id}: 抓取用戶資訊失敗: {e}")  # print 抓取用戶資訊失敗

    def fetch_users_from_group_post(self, url):
        """
        從貼文抓取用戶資訊。
        """
        print(f"Worker {self.worker_id}: 正在處理社團貼文...")
        try:  # 嘗試從貼文抓取用戶資訊
            self.driver.get(url)  # 打開貼文 URL
            print(f"Worker {self.worker_id}: 正在抓取貼文 URL: {url}")

            # 抓取群組名稱
            try:  
                group_name_element = self.utils.retry_find_element(By.XPATH, "//h1//a[contains(@href, '/groups/')]")  # 找到群組名稱元素
                group_name = group_name_element.text.strip() if group_name_element else ""  # 獲取群組名稱
                print(f"Worker {self.worker_id}: 抓取群組名稱: {group_name}")  # print 抓取群組名稱
            except Exception as e:  # 處理抓取群組名稱時的錯誤
                group_name = ""
                print(f"Worker {self.worker_id}: 抓取群組名稱失敗: {e}")  # print 抓取群組名稱失敗

            # 點擊「最熱門留言」
            sort_button = self.utils.retry_find_element(By.XPATH, "//span[text()='最熱門留言' or text()='最相關' or text()='最相关']")  # 找到最熱門留言按鈕
            if sort_button:  # 如果找到最熱門留言按鈕
                self.utils.scroll_to_element(sort_button)  # 滾動到最熱門留言按鈕
                sort_button.click()  # 點擊最熱門留言按鈕

                # 點擊「由新到舊」
                new_to_old_button = self.utils.retry_find_element(By.XPATH, "//span[text()='由新到舊' or text()='由新到旧']")  # 找到由新到舊按鈕   
                if new_to_old_button:  # 如果找到由新到舊按鈕
                    new_to_old_button.click()  # 點擊由新到舊按鈕

            # 滾動加載所有留言
            self.utils.scroll_to_bottom()

            # 展開所有回覆
            self._click_all_replies()

            # 抓取留言區塊
            comment_blocks = self.utils.retry_find_elements(By.XPATH, "//div[contains(@aria-label, '的留言') or contains(@aria-label, '评论者')]")

            # 初始化結果列表
            result_data = []

            if comment_blocks:  # 如果找到留言區塊
                total_blocks = len(comment_blocks)  # 獲取留言區塊數量
                print(f"Worker {self.worker_id}: 開始抓取用戶資訊，共 {total_blocks} 則留言...")  # print 開始抓取用戶資訊

                # 逐一處理每個留言區塊
                for index, block in enumerate(comment_blocks, start=1):
                    try:
                        # 提取用戶資訊
                        user_info = self._extract_user_info([block])[0]  # 單個區塊提取
                        result_data.append({  # 添加用戶資訊到結果列表
                            "keywords": url,  # 關鍵詞
                            "group_name": group_name,  # 群組名稱
                            "fb_user_id": user_info.get("user_id"),  # 用戶 ID
                            "fb_user_name": user_info.get("name"),  # 用戶名稱
                            "user_photo": user_info.get("photo"),  # 用戶照片
                            "fb_user_url": f"https://www.facebook.com/{user_info.get('user_id')}",
                            "subject": user_info.get("subject"),
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })

                        # 打印進度
                        print(f"Worker {self.worker_id}: 已完成 {index}/{total_blocks} ({(index / total_blocks) * 100:.2f}%)")

                    except Exception as block_error:  # 處理留言區塊時的錯誤
                        print(f"Worker {self.worker_id}: 處理第 {index} 則留言時發生錯誤: {block_error}")

            # 將結果寫入 JSON 檔案
            self._save_crawl_results(result_data, post_type="group", group_name=group_name)

        except Exception as e:  # 處理抓取用戶資訊時的錯誤
            print(f"Worker {self.worker_id}: 抓取用戶資訊失敗: {e}")  # print 抓取用戶資訊失敗

    def fetch_group_members(self, url):
        """
        從社團抓取成員資料，避免重複抓取，並打印進度。
        """
        print(f"Worker {self.worker_id}: 正在爬社團名單...")

        # 確保 URL 包含 /members
        if not url.strip().endswith("/members"):  # 確保 URL 包含 /members
            url = url.rstrip("/") + "/members"  # 添加 /members 到 URL
        self.driver.get(url)  # 打開 URL

        try:
            # 抓取群組名稱
            try:
                group_name_element = self.utils.retry_find_element(By.XPATH, "//h1//a[contains(@href, '/groups/')]")  # 找到群組名稱元素
                group_name = group_name_element.text.strip() if group_name_element else ""  # 獲取群組名稱
                print(f"Worker {self.worker_id}: 抓取群組名稱: {group_name}")  # print 抓取群組名稱
            except Exception as e:  # 處理抓取群組名稱時的錯誤
                group_name = ""
                print(f"Worker {self.worker_id}: 抓取群組名稱失敗: {e}")  # print 抓取群組名稱失敗

            # 滾動加載所有成員
            self.utils.scroll_to_bottom()

            # 抓取成員區塊
            member_blocks = self.utils.retry_find_elements(By.XPATH, "//div[@data-visualcompletion='ignore-dynamic' and @role='listitem']")
            total_members = len(member_blocks)
            print(f"Worker {self.worker_id}: 找到 {total_members} 位成員")

            result_data = []  # 儲存結果的列表
            processed_user_ids = set()  # 已處理的用戶 ID 集合

            for index, block in enumerate(member_blocks, start=1):  # 遍歷每個成員區塊
                try:
                    try:
                        name_element = block.find_element(By.XPATH, ".//a[contains(@href, '/user/') and @aria-label]")  # 找到用戶名稱元素  
                        fb_user_name = name_element.get_attribute("aria-label").strip() if name_element else ""  # 獲取用戶名稱 
                    except Exception as e:  # 處理抓取用戶名稱時的錯誤
                        fb_user_name = ""  # 設置用戶名稱為空字串

                    # 抓取用戶的 Facebook URL
                    try:  
                        fb_user_url = name_element.get_attribute("href") if name_element else ""  # 獲取用戶 URL
                        fb_user_id = self._extract_fb_user_id(fb_user_url) if fb_user_url else ""  # 提取用戶 ID
                        fb_user_url = f"https://www.facebook.com/{fb_user_id}" if fb_user_id else ""  # 設置用戶 URL
                    except Exception as e:  # 處理抓取用戶 URL 時的錯誤
                        fb_user_url, fb_user_id = "", ""  # 設置用戶 URL 和 ID 為空字串

                    # 如果用戶已處理，跳過
                    if fb_user_id in processed_user_ids:  # 如果用戶 ID 已處理
                        print(f"Worker {self.worker_id}: 用戶 {fb_user_id} 已抓取，跳過，已完成 {index}/{total_members} ({(index / total_members) * 100:.2f}%)")  # print 用戶已抓取，跳過
                        continue  # 跳過
                    processed_user_ids.add(fb_user_id)  # 將用戶 ID 添加到已處理集合

                    # 抓取用戶照片
                    try:  
                        photo_element = block.find_element(By.CSS_SELECTOR, "g image")  # 找到用戶照片元素  
                        user_photo = photo_element.get_attribute("xlink:href") if photo_element else ""  # 獲取用戶照片
                    except Exception as e:  # 處理抓取用戶照片時的錯誤
                        user_photo = ""  # 設置用戶照片為空字串

                    # 抓取職位/描述
                    try:
                        # 抓取所有 <span> 元素
                        span_elements = block.find_elements(By.XPATH, ".//span[@dir='auto']")  # 找到所有 <span> 元素
                        subject_list = []  # 初始化描述列表

                        # 過濾並處理文字
                        for span in span_elements:
                            text = span.text.strip()  # 獲取文字

                            # 跳過與名稱相同的文字或包含無效關鍵詞的文字
                            if text and text != fb_user_name and not any(kw in text for kw in ["加入", "管理員", "管理员"]):  
                                subject_list.append(text)  # 添加到描述列表

                        # 合併符合條件的描述文字
                        subject = "\n".join(subject_list)  # 合併描述文字
                        subject = self._remove_unnecessary_subjects(subject, [fb_user_name])  # 移除不必要的描述文字
                    except Exception as e:  # 處理抓取職位/描述時的錯誤
                        subject = ""  # 設置描述為空字串
                        print(f"Worker {self.worker_id}: 抓取職位/描述失敗: {e}")

                    # 添加至結果
                    result_data.append({  # 添加到結果列表
                        "keywords": url,  # 關鍵詞
                        "group_name": group_name,  # 群組名稱
                        "fb_user_id": fb_user_id,  # 用戶 ID
                        "fb_user_name": fb_user_name,  # 用戶名稱
                        "user_photo": user_photo,  # 用戶照片
                        "subject": subject,  # 描述
                        "fb_user_url": fb_user_url,  # 用戶 URL
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 時間   
                    })

                    # 打印進度
                    print(f"Worker {self.worker_id}: 已完成 {index}/{total_members} ({(index / total_members) * 100:.2f}%)")

                except Exception as e:  # 處理成員區塊時的錯誤
                    print(f"Worker {self.worker_id}: 處理成員區塊時發生錯誤: {e}")

            # 儲存結果到檔案
            self._save_crawl_results(result_data, post_type="group_members")  # 儲存結果到檔案

        except Exception as e:  # 處理抓取社團成員信息時的錯誤
            print(f"Worker {self.worker_id}: 抓取社團成員信息失敗: {e}")


    def _click_all_replies(self):
        """
        點擊所有「查看 X 則回覆」按鈕以展開所有回覆。
        """
        print(f"Worker {self.worker_id}: 開始展開所有回覆...")
        reply_buttons = self.utils.retry_find_elements(By.XPATH, "//span[contains(text(), '則回覆')]")  # 找到所有「查看 X 則回覆」按鈕 
        for button in reply_buttons:  # 遍歷每個按鈕
            try:
                self.utils.scroll_to_element(button)  # 滾動到按鈕
                button.click()  # 點擊按鈕
            except Exception as e:  # 處理點擊按鈕時的錯誤
                print(f"Worker {self.worker_id}: 點擊回覆按鈕時出現錯誤: {e}")

    def _extract_user_info(self, blocks):
        """
        從區塊中提取用戶的 Facebook 用戶 ID、名稱、照片及其他信息。
    
        每個區塊代表一個用戶的信息，通過以下步驟提取數據：
        1. 從區塊中找到 Facebook 用戶 URL 並解析出用戶 ID。
        2. 提取用戶名稱和頭像。
        3. 利用滑鼠懸停行為（hover）提取附加信息，並驗證提取結果是否匹配。
        4. 確保用戶信息唯一性，並存入結果列表。

        :param blocks: 包含用戶信息的區塊元素列表
        :return: 包含用戶信息的列表，每個元素為字典
        """
        users_info = []  # 儲存用戶資訊的列表
        seen_user_ids = set()  # 用於去除重覆的集合
        processed_elements = set()  # 用於批量處理滑鼠懸停的元素

        for block in blocks:
            try:
                # 提取用戶的 Facebook URL
                fb_user_url_element = block.find_element(By.XPATH, ".//a[contains(@href, '/groups/') or contains(@href, 'profile.php') or contains(@href, 'facebook.com')]")
                fb_user_url = fb_user_url_element.get_attribute("href")  # 獲取用戶 URL
                user_id = self._extract_fb_user_id(fb_user_url)  # 提取用戶 ID  

                # 確保用戶 ID 唯一，避免重複提取
                if not user_id or user_id in seen_user_ids:  # 如果用戶 ID 不存在或已提取
                    continue  # 跳過
                seen_user_ids.add(user_id)  # 將用戶 ID 添加到已提取集合

                # 提取用戶名稱
                try:
                    user_name_element = block.find_element(By.XPATH, ".//span[@dir='auto']")  # 找到用戶名稱元素
                    user_name = user_name_element.text.strip() if user_name_element else ""  # 獲取用戶名稱 
                except Exception:  # 處理抓取用戶名稱時的錯誤
                    user_name = ""  # 設置用戶名稱為空字串

                # 提取用戶照片
                try:
                    user_photo_element = block.find_element(By.CSS_SELECTOR, "g image")  # 找到用戶照片元素
                    user_photo = user_photo_element.get_attribute("xlink:href") if user_photo_element else ""  # 獲取用戶照片

                    # 確保目標是有效的頭像
                    if not user_photo or user_photo_element in processed_elements:  # 如果用戶照片不存在或已處理
                        continue  # 跳過
                except Exception:  # 處理抓取用戶照片時的錯誤
                    user_photo = ""

                # 儲存用戶信息
                user_info = {  # 儲存用戶信息
                    "user_id": user_id,  # 用戶 ID
                    "name": user_name,  # 用戶名稱
                    "photo": user_photo,  # 用戶照片
                }

                # 滑鼠懸停行為提取附加信息
                try:
                    subject = self._hover_and_extract(user_photo_element)  # 滑鼠懸停行為提取附加信息

                    # 校驗滑鼠懸停結果是否與用戶名稱匹配
                    if self._validate_hover_result(subject, user_name):  # 校驗滑鼠懸停結果是否與用戶名稱匹配   
                        subject = self._remove_unnecessary_subjects(subject, [user_name])  # 移除不必要的附加信息
                        user_info["subject"] = subject  # 將附加信息添加到用戶信息

                        # 成功懸停後將元素加入 processed_elements 避免重複處理
                        processed_elements.add(user_photo_element)
                    else:
                        print(f"Worker {self.worker_id}: 用戶名稱 '{user_name}' 未能匹配從浮窗提取的資訊：{subject}")  # 打印未能匹配的用戶名稱和附加信息

                except Exception as e:  # 處理滑鼠懸停操作或提取過程中的錯誤
                    print(f"Worker {self.worker_id}: 滑鼠懸停操作或提取過程中發生錯誤: {e}")  # 打印滑鼠懸停操作或提取過程中的錯誤

                # 將用戶信息添加到結果列表
                users_info.append(user_info)  # 將用戶信息添加到結果列表    

            except Exception as e:
                # 印出提取哪個用戶資料時發生錯誤
                print(f"Worker {self.worker_id}: 提取用戶資料時發生錯誤: {e}")

        return users_info  # 返回用戶信息列表

    def _extract_fb_user_id(self, fb_user_url):
        """
        從 Facebook URL 提取用戶 ID。
        :param fb_user_url: 用戶的 Facebook URL
        :return: 提取的用戶 ID 或 None
        """
        
        # 提取用戶 ID
        if 'profile.php' in fb_user_url and 'id=' in fb_user_url:  # 如果 URL 包含 profile.php 和 id=   
            fb_user_id = fb_user_url.split('id=')[1].split('&')[0]  # 提取用戶 ID
        elif 'facebook.com' in fb_user_url and '/groups/' not in fb_user_url:  # 如果 URL 包含 facebook.com 和 /groups/
            fb_user_id = fb_user_url.split('facebook.com/')[-1].split('?')[0]  # 提取用戶 ID
        elif "/user/" in fb_user_url:  # 如果 URL 包含 /user/
            fb_user_id =  fb_user_url.split("user/")[-1].split("/")[0]  # 提取用戶 ID
        
        return fb_user_id if fb_user_id else None  # 返回用戶 ID 或 None

    def _validate_hover_result(self, subject, user_name, user_id=None):
        """
        驗證懸浮視窗提取的附加信息是否匹配當前用戶。
        :param subject: 從浮窗提取的附加信息
        :param user_name: 當前用戶的名稱
        :param user_id: 當前用戶的 ID（可選）
        :return: boolean，表示是否匹配
        """
        if not subject:
            return False

        # 去掉多餘空格並統一大小寫進行比對
        normalized_user_name = user_name.strip().lower().replace(" ", "") if user_name else None  # 去掉多餘空格並統一大小寫進行比對    
        normalized_user_id = str(user_id).strip().lower() if user_id else None  # 去掉多餘空格並統一大小寫進行比對
        normalized_subject = [
            info.strip().lower().replace(" ", "") for info in subject  # 去掉多餘空格並統一大小寫進行比對
        ]

        # 檢查用戶名稱是否出現在附加信息中
        if normalized_user_name and any(normalized_user_name in info for info in normalized_subject):
            return True

        # 檢查用戶 ID 是否出現在附加信息中
        if normalized_user_id and any(normalized_user_id in info for info in normalized_subject):
            return True

        return False

    def _hover_and_extract(self, element, retries=3):
        """
        滑鼠懸停指定的元素，等待浮窗出現並提取相關信息。
        增加重試機制，確保附加信息提取成功，並處理浮窗卡住問題。
        """
        try:
            # 確保目標元素仍在 DOM 中
            if not element.is_displayed():  # 如果目標元素不在 DOM 中   
                print(f"Worker {self.worker_id}: 目標元素已不在 DOM 中，跳過滑鼠懸停")  # 打印目標元素已不在 DOM 中
                return [""]  # 返回空列表

            for attempt in range(retries):
                try:
                    # 確保滑鼠狀態重置，清除卡住的浮窗
                    self._remove_stuck_hover_window()

                    # 滾動到元素並上移 10 像素
                    self.driver.execute_script("""
                        arguments[0].scrollIntoView({block: 'center', inline: 'center'});
                        const rect = arguments[0].getBoundingClientRect();
                        window.scrollBy(0, rect.top - 10);
                    """, element)

                    # 模擬滑鼠懸停行為
                    self.driver.execute_script(
                        "var event = new MouseEvent('mouseover', {bubbles: true}); arguments[0].dispatchEvent(event);",
                        element
                    )

                    # 等待浮窗出現
                    hover_window = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "div[aria-label='連結預覽'][aria-modal='true'][role='dialog']")
                        )
                    )

                    # 提取浮窗內的名字 (h2[dir='auto'])
                    names = self.driver.execute_script("""
                        let infoElems = arguments[0].querySelectorAll("h2[dir='auto']");
                        return Array.from(infoElems).map(elem => elem.textContent.trim()).filter(text => text);
                    """, hover_window) or []

                    # 提取浮窗內的其他細節 (span[dir='auto'])
                    details = self.driver.execute_script("""
                        let infoElems = arguments[0].querySelectorAll("span[dir='auto']");
                        return Array.from(infoElems).map(elem => elem.textContent.trim()).filter(text => text);
                    """, hover_window) or []

                    raw_subject = names + details

                    # 模擬滑鼠移出操作
                    self.driver.execute_script(
                        "var event = new MouseEvent('mouseout', {bubbles: true}); arguments[0].dispatchEvent(event);",
                        element
                    )

                    # 去重處理並保持順序
                    unique_subject = list(dict.fromkeys(raw_subject))
                    return unique_subject

                except Exception as hover_error:
                    continue  # 跳過

            print(f"Worker {self.worker_id}: 超過最大重試次數{retries}次，無法提取目標信息")  # 打印超過最大重試次數
            return [""]  # 返回空列表

        except Exception as e:  # 處理滑鼠懸停操作失敗的錯誤    
            print(f"Worker {self.worker_id}: 滑鼠懸停操作失敗: {e}")  # 打印滑鼠懸停操作失敗的錯誤
            return [""]  # 返回空列表

    def _remove_stuck_hover_window(self):
        """
        使用 Selenium 和 JavaScript 强制移除页面上的浮窗。
        """
        try:
            # 移除所有可能卡住的浮窗
            script = """
            var hoverWindows = document.querySelectorAll("div[aria-label='連結預覽'][aria-modal='true']");
            hoverWindows.forEach(hoverWindow => {
                if (hoverWindow && hoverWindow.parentNode) {
                    hoverWindow.parentNode.removeChild(hoverWindow);
                }
            });
            """
            self.driver.execute_script(script)  # 執行 JavaScript 腳本
        except Exception as e:  # 處理移除卡住的浮窗時的錯誤    
            print(f"Worker {self.worker_id}: 移除卡住的浮窗時發生錯誤: {e}")  # 打印移除卡住的浮窗時的錯誤

    def _expand_url(self, url):
        """
        解開縮網址
        :param url: 短鏈接 URL
        :return: 解開後的完整 URL
        """
        try:  # 嘗試解開縮網址
            response = requests.head(url, allow_redirects=True, timeout=10)  # 發送 HTTP 頭請求
            expanded_url = response.url  # 獲取解開後的完整 URL
            return expanded_url
        except requests.RequestException as e:  # 處理解開縮網址時的錯誤
            print(f"Worker {self.worker_id}: 無法解開縮網址: {url}，錯誤: {e}")  # 打印無法解開縮網址的錯誤 
            return url  # 如果解開失敗，返回原始 URL

    def _determine_post_type(self, url):
        """
        判斷是個人貼文還是社團貼文
        :param url: 解開後的完整 URL
        :return: "group" 或 "personal"
        """
        try:  # 嘗試判斷貼文類型
            path = urlparse(url).path  # 獲取 URL 的路徑
            if "/groups/" in path:  # 如果 URL 包含 /groups/
                return "group"  # 返回社團貼文
            else:  # 如果 URL 不包含 /groups/
                return "personal"  # 返回個人貼文
        except Exception as e:  # 處理判斷貼文類型時的錯誤
            print(f"Worker {self.worker_id}: 無法判斷貼文類型，錯誤: {e}")  # 打印無法判斷貼文類型的錯誤
            return "unknown"  # 返回未知貼文
    
    def _remove_unnecessary_subjects(self, subjects, unwanted_keywords=None):
        """
        移除不必要的關鍵字。
        :param subjects: 從滑鼠懸停提取的附加資訊 
        :param unwanted_keywords: 不必要的關鍵字列表
        :return: 清理後的資訊列表
        """
        if not subjects:  # 如果 subjects 為空
            return []  # 返回空列表 
        
        # 默認的關鍵字列表
        default_keywords = ["發送訊息", "加朋友", "追蹤", "訊息", "人", "共同朋友", "點", "位朋友", "成為朋友"]

        # 合併自定義關鍵字
        if unwanted_keywords:  # 如果 unwanted_keywords 不為空  
            unwanted_keywords = list(set(default_keywords + unwanted_keywords))  # 合併自定義關鍵字
        else:  # 如果 unwanted_keywords 為空
            unwanted_keywords = default_keywords  # 使用默認關鍵字列表

        # 確保輸入是列表，如果是字符串，按換行符拆分為列表
        if isinstance(subjects, str):  # 如果 subjects 是字符串
            subjects = subjects.split("\n")  # 按換行符拆分為列表   

        # 清理不必要的關鍵字
        cleaned_subjects = [
            s for s in subjects if not any(keyword in s for keyword in unwanted_keywords)
        ]

        return cleaned_subjects  # 返回清理後的資訊列表

    def _save_crawl_results(self, result_data, post_type, group_name=None):
        """
        儲存爬取結果到分類資料夾中，檔案名包含貼文類型、群組名稱及時間戳。
        
        :param result_data: 要儲存的結果數據
        :param post_type: 貼文類型 ("personal" 或 "group")
        :param group_name: 群組名稱 (若為群組貼文，提供群組名稱)
        """
        # 定義基礎資料夾
        base_folder = "./results"  # 定義基礎資料夾
        post_type_folder = os.path.join(base_folder, f"crawl_results_{post_type}")  # 定義貼文類型資料夾    
        os.makedirs(post_type_folder, exist_ok=True)  # 確保資料夾存在

        # 處理群組名稱
        if group_name:  # 如果群組名稱存在
            sanitized_group_name = group_name.replace(" ", "_").replace("/", "_").replace("\\", "_")  # 清理群組名稱
        else:  # 如果群組名稱不存在
            sanitized_group_name = "unknown"  # 設置群組名稱為 unknown

        # 生成時間戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 組合檔案名稱
        if post_type == "group":  # 如果貼文類型是社團貼文
            filename = f"{sanitized_group_name}_{timestamp}.json"  # 組合檔案名稱
        else:  # 如果貼文類型是個人貼文
            filename = f"{post_type}_{timestamp}.json"  # 組合檔案名稱

        # 完整檔案路徑
        output_file = os.path.join(post_type_folder, filename)  # 組合完整檔案路徑

        try:
            with open(output_file, "w", encoding="utf-8") as json_file:  # 以 UTF-8 編碼開啟檔案
                json.dump(result_data, json_file, ensure_ascii=False, indent=4)  # 將結果數據寫入 JSON 檔案
            print(f"Worker {self.worker_id}: 結果已保存到檔案 {output_file}")  # 打印結果已保存到檔案
        except Exception as e:  # 處理儲存爬取結果時的錯誤
            print(f"Worker {self.worker_id}: 儲存爬取結果時發生錯誤: {e}")  # 打印儲存爬取結果時的錯誤

