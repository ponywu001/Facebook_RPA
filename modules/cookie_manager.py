import json
import os

class CookieManager:
    def __init__(self, cookies_folder, worker_id=None):
        """
        初始化 CookieManager 類別。
        :param cookies_folder: 存放 cookies 的資料夾路徑
        :param worker_id: 工作者 ID，用於日誌打印
        """
        self.cookies_folder = cookies_folder  # 設置 cookies 資料夾路徑
        self.worker_id = worker_id  # 設置工作者 ID
        if not os.path.exists(self.cookies_folder):  # 如果 cookies 資料夾不存在
            os.makedirs(self.cookies_folder)  # 創建 cookies 資料夾

    def get_cookie_file_path(self, email):
        """返回指定帳號的 Cookies 文件路徑"""
        return os.path.join(self.cookies_folder, f"{email}_cookies.json")  # 返回指定帳號的 Cookies 文件路徑

    def load_cookies(self, driver, email):
        """從文件加載指定帳號的 Cookies 到 WebDriver"""
        cookie_file = self.get_cookie_file_path(email)  # 獲取指定帳號的 Cookies 文件路徑
        if os.path.exists(cookie_file):  # 如果 Cookies 文件存在
            try:
                with open(cookie_file, 'r') as file:  # 以 UTF-8 編碼開啟 Cookies 文件
                    cookies = json.load(file)  # 加載 Cookies 數據
                    for cookie in cookies:
                        driver.add_cookie(cookie)  # 將 Cookies 添加到 WebDriver
                print(f"Worker {self.worker_id}: Cookies 已加載成功: {cookie_file}")  # 打印 Cookies 已加載成功
                return True
            except Exception as e:
                print(f"Worker {self.worker_id}: 加載 Cookies 時發生錯誤: {e}")  # 打印加載 Cookies 時發生錯誤
                os.remove(cookie_file)  # 刪除 Cookies 文件
                return False
        else:
            print(f"Worker {self.worker_id}: Cookies 文件 {cookie_file} 不存在。")  # 打印 Cookies 文件不存在
            return False

    def save_cookies(self, driver, email):
        """將當前 WebDriver 的 Cookies 保存到指定帳號的文件中"""
        cookie_file = self.get_cookie_file_path(email)  # 獲取指定帳號的 Cookies 文件路徑
        try:
            with open(cookie_file, 'w') as file:  # 以 UTF-8 編碼開啟 Cookies 文件
                json.dump(driver.get_cookies(), file)  # 將 Cookies 數據保存到文件中
                print(f"Worker {self.worker_id}: Cookies 已保存到 {cookie_file}")  # 打印 Cookies 已保存到文件
        except Exception as e:
            print(f"Worker {self.worker_id}: 保存 Cookies 時發生錯誤: {e}")  # 打印保存 Cookies 時發生錯誤