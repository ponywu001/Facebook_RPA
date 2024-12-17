from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
import re

class ProxyManager:
    def __init__(self, driver: WebDriver, proxy_config, worker_id=None):
        """初始化 ProxyManager 並設置代理參數。"""
        self.driver = driver  # 設置驅動器  
        self.proxy_host = proxy_config['host']  # 設置代理主機
        self.proxy_port = proxy_config['port']  # 設置代理埠
        self.proxy_username = proxy_config['proxy_username']  # 設置代理用戶名
        self.proxy_password = proxy_config['proxy_password']  # 設置代理密碼
        self.worker_id = worker_id  # 設置工作ID

    def close_blank_tab(self):
        """關閉所有空白標籤頁。"""
        try:
            for handle in self.driver.window_handles:  # 遍歷所有視窗句柄   
                self.driver.switch_to.window(handle)  # 切換到當前視窗
                if self.driver.current_url == "about:blank":  # 如果當前URL是空白頁
                    self.driver.close()  # 關閉當前視窗
        except Exception as e:  # 如果出現錯誤
            print(f"Worker {self.worker_id}: 關閉空白標籤頁時出錯: {e}")  # print錯誤信息
            raise  # 拋出錯誤

    def get_extension_id(self) -> str:
        """從當前的 URL 中取得擴展 ID。"""
        try:
            current_url = self.driver.current_url  # 獲取當前URL
            match = re.search(r'moz-extension://([a-f0-9-]+)/', current_url)  # 使用正則表達式匹配擴展ID
            if match:  # 如果匹配成功
                return match.group(1)  # 返回擴展ID
            else:  # 如果匹配失敗
                raise ValueError(f"Worker {self.worker_id}: 無法找到擴展 ID")  # 拋出錯誤
        except Exception as e:  # 如果出現錯誤
            print(f"Worker {self.worker_id}: 取得擴展 ID 時出錯: {e}")  # print錯誤信息
            raise  # 拋出錯誤

    def configure_socks5_proxy(self):
        """在擴展中配置 SOCKS5 代理設置。"""
        try:
            extension_id = self.get_extension_id()  # 獲取擴展ID
            options_url = f"moz-extension://{extension_id}/options.html"  # 構建選項頁面URL
            self.driver.get(options_url)  # 訪問選項頁面

            # 等待 options 頁面加載
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Add')]")))  # 等待 "Add" 按鈕出現

            # 等待加載指示器消失
            WebDriverWait(self.driver, 10).until(EC.invisibility_of_element_located((By.CLASS_NAME, "spinner")))  # 等待加載指示器消失

            # 點擊 "Add" 按鈕
            add_link = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Add')]")  # 找到 "Add" 按鈕
            self.driver.execute_script("arguments[0].click();", add_link)  # 執行 JavaScript 點擊 "Add" 按鈕

            # 等待新頁面加載
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "proxyType")))  # 等待 "proxyType" 元素出現

            # 選擇 SOCKS5 選項
            proxy_type_select = Select(self.driver.find_element(By.ID, "proxyType"))  # 找到 "proxyType" 下拉選單
            proxy_type_select.select_by_visible_text("SOCKS5")  # 選擇 SOCKS5 選項

            # 輸入代理資訊
            self.driver.find_element(By.ID, "proxyAddress").send_keys(self.proxy_host)  # 輸入代理主機
            self.driver.find_element(By.ID, "proxyPort").send_keys(str(self.proxy_port))  # 輸入代理埠
            self.driver.find_element(By.ID, "proxyUsername").send_keys(self.proxy_username)  # 輸入代理用戶名
            self.driver.find_element(By.ID, "proxyPassword").send_keys(self.proxy_password)  # 輸入代理密碼

            self.driver.find_element(By.XPATH, "//button[contains(text(), 'Save')]").click()  # 點擊 "Save" 按鈕
            self.driver.back()  # 返回上一頁
        except Exception as e:  # 如果出現錯誤
            print(f"Worker {self.worker_id}: 配置 SOCKS5 代理時出錯: {e}")  # print錯誤信息
            raise

    def enable_proxy(self):
        """啟用已配置的代理模式。"""
        try:
            # 使用 JavaScript 刪除 `spinner` 元素
            self.driver.execute_script("var spinner = document.querySelector('.spinner'); if (spinner) spinner.remove();")

            # 等待 `select` 元素可點擊
            select_element = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "mode")))

            # JavaScript 點擊 `select` 元素
            self.driver.execute_script("arguments[0].click();", select_element)

            # 啟用 Proxy
            select = Select(select_element)  # 找到 "mode" 下拉選單
            select.select_by_value("patterns")  # 選擇 "patterns" 選項
            
        except Exception as e:  # 如果出現錯誤
            print(f"Worker {self.worker_id}: 啟用代理模式時出錯: {e}")  # print錯誤信息
            raise  # 拋出錯誤