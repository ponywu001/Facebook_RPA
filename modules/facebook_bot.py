import time
import pyotp
from selenium.webdriver.common.by import By
from modules.proxy_manager import ProxyManager
from modules.cookie_manager import CookieManager
from modules.utils import WebDriverUtils

COOKIES_FOLDER = "cookies"

class FacebookBot:
    def __init__(self, driver, proxy_config=None, worker_id=None):
        """
        初始化 FacebookBot 類別。
        :param driver: Selenium WebDriver 實例
        :param proxy_config: 代理配置（如果有）
        :param worker_id: 工作者 ID 用於打印日誌
        """
        self.driver = driver  # 初始化 WebDriver    
        self.worker_id = worker_id  # 設置工作者 ID
        self.proxy_config = proxy_config  # 設置代理配置
        
        # 如果提供了代理配置，設置代理
        if self.proxy_config:
            self.setup_proxy()  # 設置代理
        
        self.cookie_manager = CookieManager(COOKIES_FOLDER, worker_id)  # 初始化 CookieManager
        self.utils = WebDriverUtils(driver, worker_id)  # 初始化 WebDriverUtils 
        
    def setup_proxy(self):
        """
        設置代理
        """
        max_retries = 5  # 最大重試次數
        for attempt in range(max_retries):  # 遍歷嘗試設置代理
            try:
                proxy_manager = ProxyManager(self.driver, self.proxy_config, self.worker_id)  # 初始化 ProxyManager
                proxy_manager.close_blank_tab()  # 關閉空白標籤
                proxy_manager.configure_socks5_proxy()  # 配置 SOCKS5 代理
                proxy_manager.enable_proxy()  # 啟用代理
                print(f"Worker {self.worker_id}: 代理 {self.proxy_config['host']}:{self.proxy_config['port']} 設置成功")
                return  # 設置代理成功，返回
            except Exception as e:  # 設置代理失敗
                print(f"Worker {self.worker_id}: 設置代理時出錯: {e}，嘗試重新設置代理 ({attempt + 1}/{max_retries})")

        self.driver.quit()  # 設置代理失敗時，關閉瀏覽器
        self.driver = None  # 設置代理失敗時，將 driver 設置為 None 以避免後續操作
        
    def login(self, account_info):
        """
        登錄 Facebook，首先嘗試通過 Cookies 登錄，如果失敗則進行標準登錄
        """
        if not self.driver:
            print(f"Worker {self.worker_id}: 無法登錄，因為代理設置失敗或 driver 為 None")
            return False

        email = account_info["account"]  # 獲取帳號 
        password = account_info["password"]  # 獲取密碼
        secret_key = account_info["secret_key"]  # 獲取 2FA 密鑰
        
        # 使用 CookieManager 嘗試通過 Cookies 登錄
        if self.try_login_with_cookies(email):  # 如果使用 cookies 成功登入，直接返回 True
            return True  
        
        # Cookies 登錄失敗，執行標準登錄流程
        self.driver.get("https://www.facebook.com")  # 打開 Facebook 登入頁面

        time.sleep(5)  # 等待登錄完成後的頁面加載

        try:
            # 等待並輸入電子郵件帳號
            self.utils.retry_find_element(By.ID, "email", retries=5, delay=2, timeout=10).send_keys(email)
            # 等待並輸入密碼
            self.utils.retry_find_element(By.ID, "pass", retries=5, delay=2, timeout=10).send_keys(password)
            # 點擊登錄按鈕
            self.utils.retry_click(By.NAME, "login", retries=3, delay=2, timeout=10)
            print(f"Worker {self.worker_id}: 點擊登錄按鈕成功")

            # 檢查是否需要 2FA 驗證
            if self.utils.retry_find_element(By.XPATH, "//span[contains(text(), '嘗試其他方式') or contains(text(), '试试其他方式')]", retries=1, delay=2, timeout=10):
                print(f"Worker {self.worker_id}: 檢測到 2FA 驗證，開始 2FA 驗證流程")
                if self.perform_2fa_verification(secret_key):  # 如果 2FA 驗證成功  
                    print(f"Worker {self.worker_id}: 2FA 驗證成功")
                else:  # 如果 2FA 驗證失敗  
                    print(f"Worker {self.worker_id}: 2FA 驗證失敗")
                    return False  # 如果 2FA 驗證失敗，返回 False
                
            # 確認已成功登入
            login_success = self.utils.retry_find_element(
                By.XPATH, 
                "//span[contains(text(), '分享你的新鲜事吧') or contains(text(), '在想些什麼？')]", 
                retries=1, delay=2, timeout=10
            )

            if login_success:  # 如果登入成功
                # 成功登錄後保存 cookies
                self.cookie_manager.save_cookies(self.driver, email)  # 保存 cookies    
                print(f"Worker {self.worker_id}: 帳號 {email} 登錄成功並保存了新的 cookies")
                return True
            else:  # 如果登入失敗
                print(f"Worker {self.worker_id}: 登入失敗，無法找到登入後的確認元素")
                return False
        
        except Exception as e:  # 登入過程中出現錯誤
            print(f"Worker {self.worker_id}: 登錄過程中出現錯誤: {e}")
            return False
    
    def try_login_with_cookies(self, email):
        """
        嘗試使用 cookies 登錄，如果成功則返回 True，否則返回 False
        """
        self.driver.get("https://www.facebook.com")  # 打開 Facebook 登入頁面   
        
        if not self.cookie_manager.load_cookies(self.driver, email):  # 如果 cookies 加載失敗
            return False
        
        self.driver.refresh()  # 刷新頁面
        
        try:
            login_success = self.utils.retry_find_element(
                By.XPATH, 
                "//span[contains(text(), '分享你的新鲜事吧') or contains(text(), '在想些什麼？')]",
                retries=1
            )  # 檢查登入是否成功   
            
            if login_success:  # 如果登入成功
                print(f"Worker {self.worker_id}: 帳號 {email} 使用 cookies 成功登入")
                return True
        except Exception as e:  # 使用 cookies 登入過程中出現錯誤
            print(f"Worker {self.worker_id}: 使用 cookies 登入過程中出現錯誤: {e}")
        
        return False
    
    def perform_2fa_verification(self, secret_key):
        """
        執行 2FA 驗證過程
        :param secret_key: 用於生成 2FA 驗證碼的密鑰
        :return: 如果 2FA 驗證成功，返回 True；否則返回 False
        """
        try:
            # 點擊「嘗試其他方式」
            element = self.utils.retry_find_element(
                By.XPATH, 
                "//span[text()='嘗試其他方式'] | //span[text()='试试其他方式']", 
                retries=5, delay=2, timeout=10
            )
            self.driver.execute_script("arguments[0].click();", element)  # 點擊「嘗試其他方式」
            print(f"Worker {self.worker_id}: 點擊「嘗試其他方式」")
            self.utils.random_wait()  # 等待隨機時間

            # 點擊「驗證應用程式」
            element = self.utils.retry_find_element(
                By.XPATH, 
                "//div[text()='從驗證應用程式取得驗證碼。'] | //div[text()='从你的身份验证应用获取验证码。']",
                retries=5, delay=2, timeout=10
            )
            self.driver.execute_script("arguments[0].click();", element)  # 點擊「驗證應用程式」
            self.utils.random_wait()  # 等待隨機時間

            # 點擊「繼續」
            element = self.utils.retry_find_element(
                By.XPATH, 
                "//span[text()='繼續'] | //span[text()='继续']", 
                retries=5, delay=2, timeout=10
            )
            self.driver.execute_script("arguments[0].click();", element)
            print(f"Worker {self.worker_id}: 點擊「繼續」")
            self.utils.random_wait()

            # 獲取 2FA 驗證碼並輸入
            two_fa_code = self.get_2fa_code(secret_key)  # 獲取 2FA 驗證碼
            for char in two_fa_code:  # 遍歷 2FA 驗證碼
                self.utils.retry_find_element(
                    By.XPATH, "//input[@type='text']", retries=5, delay=2, timeout=10
                ).send_keys(char)  # 輸入 2FA 驗證碼    
                self.utils.random_wait(0.667, 0.1)  # 等待隨機時間

            # 最後一次點擊「繼續」以提交 2FA 驗證碼
            element = self.utils.retry_find_element(
                By.XPATH, 
                "//span[text()='繼續'] | //span[text()='继续']", 
                retries=5, delay=2, timeout=10
            )
            self.driver.execute_script("arguments[0].click();", element)
            print(f"Worker {self.worker_id}: 2FA 驗證碼已輸入並提交")
            self.utils.random_wait(10, 20)

            # 驗證成功後進入主頁
            self.driver.get("https://www.facebook.com")
            return True

        except Exception as e:  # 2FA 驗證過程中出現錯誤
            print(f"Worker {self.worker_id}: 2FA 驗證過程中出現錯誤: {e}")
            return False
    
    # 獲取 2FA 驗證碼的輔助函數
    def get_2fa_code(self, secret_key):
        totp = pyotp.TOTP(secret_key)  # 生成 TOTP 對象
        return totp.now()  # 返回當前時間的 TOTP 驗證碼

    def quit(self):
        """
        關閉瀏覽器
        """
        if self.driver:  # 如果 driver 存在
            self.driver.quit()  # 關閉瀏覽器