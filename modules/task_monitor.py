from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.common.exceptions import InvalidSessionIdException
import time

class TaskMonitor:
    def __init__(self, tasks_status, all_tasks_completed, check_interval=1):
        self.tasks_status = tasks_status  # 任務狀態字典    
        self.all_tasks_completed = all_tasks_completed  # 所有任務完成事件
        self.check_interval = check_interval  # 檢查間隔時間

    def run(self):
        """
        持續檢查任務狀態，直到所有任務都完成。
        """
        print("開始監控任務狀態...")
        while not self.all_tasks_completed.is_set():  # 如果所有任務都未完成，則持續檢查
            all_tasks_completed = True  # 假設所有任務都完成

            for task_id, status in self.tasks_status.items():  # 遍歷所有任務
                # 如果任務尚未完成，設定 all_tasks_completed 為 False
                if not status.get("completed"):     
                    all_tasks_completed = False

                if status.get("driver"):  # 如果 driver 存在，繼續檢查
                    try:  # 檢查是否有非預期行為或簡體中文
                        self.check_for_unexpected_behavior(task_id, status)  # 檢查是否有非預期行為
                        self.check_for_simplified_chinese(task_id, status)  # 檢查是否出現簡體中文
                    except InvalidSessionIdException:  # 如果瀏覽器已關閉，停止該任務
                        print(f"Worker {status.get('worker_id', 'Unknown')}: 瀏覽器已關閉，任務已完成")
                        self.stop_task(status)  # 停止該任務
                    except WebDriverException:  # 如果瀏覽器崩潰，停止該任務
                        print(f"Worker {status.get('worker_id', 'Unknown')}: 瀏覽器崩潰，已停止該任務")
                        self.stop_task(status)  # 停止該任務
                    except ConnectionRefusedError:  # 如果連線被拒絕，停止該任務
                        if status.get("completed"):  # 如果任務已完成，則不停止
                            print(f"Worker {status.get('worker_id', 'Unknown')}: 瀏覽器已關閉，任務已完成")
                        else:  # 如果任務未完成，則停止
                            print(f"Worker {status.get('worker_id', 'Unknown')}: 連線被拒絕，已停止該任務")
                            self.stop_task(status)  # 停止該任務

            if all_tasks_completed:  # 如果所有任務都已完成，則停止監控
                print("所有任務已完成，停止監控")
                self.all_tasks_completed.set()  # 設定所有任務完成事件

            time.sleep(self.check_interval)  # 等待一段時間後再檢查
    
    def check_for_unexpected_behavior(self, task_id, status):
        """
        檢查是否有非預期行為發生。
        :param task_id: 任務的 ID
        :param status: 任務的狀態字典
        """
        driver = status["driver"]  # 獲取 driver
        if driver is None:  # 驗證 driver 是否為 None
            return
        
        account = status.get("account", "Unknown")  # 獲取帳號資訊
        worker_id = status.get("worker_id", "Unknown")  # 獲取 worker_id
        unexpected_texts = [  # 非預期文字列表
            "我們已移除你的貼文",
            "我们移除了你的帖子",
            "私密",
            "非公开",
            "協助我們確認你的身分",
            "輸入畫面所顯示的驗證碼",
            "我們已將你的帳號停權",
            "目前無法查看此內容",
            "我们已暂时停用你的账户",
            "你的帳號已被鎖住",
            "请帮助我们验证你的身份",
            "我們已移除部分內容或訊息",
        ]

        for text in unexpected_texts:  # 遍歷非預期文字列表
            try:
                # 檢查是否出現非預期文字
                WebDriverWait(driver, 0.01).until(
                    EC.presence_of_element_located((By.XPATH, f"//span[contains(text(), '{text}')]"))
                )
                # 如果找到非預期文字，終止任務
                reason = f"偵測到非預期行為：{text}"  # 終止原因    
                self.terminate_task(worker_id, status, reason)  # 終止任務
                print(f"Worker {worker_id}: 終止帳號 {account} 的任務，原因：{reason}")  # print終止原因
                return  # 任務終止後不再檢查其他文字
            except TimeoutException:  # 如果沒有找到該文字，檢查下一個
                continue  
    
    def check_for_simplified_chinese(self, task_id, status):
        """
        檢查是否出現簡體中文內容，如果出現則強制結束任務。
        :param task_id: 任務的 ID
        :param status: 任務的狀態字典
        """
        driver = status["driver"]  # 獲取 driver
        if driver is None:  # 驗證 driver 是否為 None
            return
        account = status.get("account", "Unknown")  # 獲取帳號資訊
        worker_id = status.get("worker_id", "Unknown")  # 獲取 worker_id
        simplified_texts = [  # 簡體中文文字列表    
            "视频",
            "创建帖子",
            "在另一台设备上查看通知",
            "选择身份验证方式",
            "公开",
        ]

        for text in simplified_texts:  # 遍歷簡體中文文字列表
            try:  # 檢查是否出現簡體中文文字
                WebDriverWait(driver, 0.01).until(
                    EC.presence_of_element_located((By.XPATH, f"//span[contains(text(), '{text}')]"))
                )
                # 如果找到該文字，終止任務
                reason = f"偵測到簡體中文內容：{text}"  # 終止原因
                self.terminate_task(worker_id, status, reason)  # 終止任務
                print(f"Worker {worker_id}: 終止帳號 {account} 的任務，原因：{reason}，請切換至繁體中文")  # print終止原因
                return  # 任務終止後不再檢查其他文字
            except TimeoutException:  # 如果沒有找到該文字，檢查下一個
                continue  
    
    def stop_task(self, status):
        """
        停止任務並釋放資源。
        """
        status["stop"] = True  # 設定停止標誌
        if status["driver"]:  # 如果 driver 存在
            try:
                status["driver"].quit()  # 關閉瀏覽器
            except Exception:
                pass  # 如果關閉瀏覽器失敗，則忽略
            finally:
                status["driver"] = None  # 釋放 driver 資源

    def terminate_task(self, worker_id, status, reason):
        """
        終止任務，並標註終止的原因。
        :param task_id: 任務的 ID
        :param status: 任務的狀態字典
        :param reason: 終止任務的原因
        """
        status["stop"] = True  # 設定停止標誌
        status["completed"] = True  # 設定任務完成標誌
        if status["driver"]:  # 如果 driver 存在
            try:  # 關閉瀏覽器
                status["driver"].quit()
            except Exception as e:  # 如果關閉瀏覽器失敗，則忽略
                print(f"Worker {worker_id}: 關閉瀏覽器時發生錯誤: {e}")
            finally:  # 釋放 driver 資源
                status["driver"] = None
