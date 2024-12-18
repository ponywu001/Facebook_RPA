from modules.multi_window_setup import MultiWindowSetup
from modules.facebook_bot import FacebookBot
from modules.data_loader import DataLoader
from modules.operations.post_manager import PostManager
from modules.operations.comment_manager import CommentManager
from modules.operations.crawl_manager import CrawlManager
from modules.operations.click_manager import ClickManager
from modules.operations.navigate_manager import NavigateManager
from modules.task_monitor import TaskMonitor
from concurrent.futures import ThreadPoolExecutor, as_completed
from config.settings import EXCEL_PATH, MAX_WORKERS
import threading
import random
import pandas as pd

# 初始化多窗口設置
multi_window_setup = MultiWindowSetup(columns=4, rows=2)
positions = multi_window_setup.positions

def process_post_account(account_info, position, task_status, worker_id):
    """
    專門處理發文帳號的操作。
    """
    process_account(account_info, position, task_status, worker_id, operation="post")


def process_comment_account(account_info, position, task_status, worker_id):
    """
    專門處理留言帳號的操作。
    """
    process_account(account_info, position, task_status, worker_id, operation="comment")

def process_crawl_account(account_info, position, task_status, worker_id):
    """
    專門處理爬蟲帳號的操作。
    """
    process_account(account_info, position, task_status, worker_id, operation="crawl")
    
def process_click_account(account_info, position, task_status, worker_id):
    """
    專門處理點擊帳號的操作。
    """
    process_account(account_info, position, task_status, worker_id, operation="click")   
    
def process_navigate_account(account_info, position, task_status, worker_id):
    """
    專門處理跳轉帳號的操作。
    """
    process_account(account_info, position, task_status, worker_id, operation="navigate")  

def process_account(account_info, position, task_status, worker_id, operation=None):
    """
    處理帳號的發文操作，並且監控狀態。
    :param account_info: 帳號資訊
    :param position: 窗口位置
    :param task_status: 用於跟蹤任務狀態
    :param worker_id: 每個 worker 的唯一標識
    :param operation: 操作類型 ("post"、"comment"、"crawl"、"click" 或 "navigate")
    """
    print(f"Worker {worker_id}: 開始處理帳號 {account_info['account']}")

    # Step 1: 啟動瀏覽器並配置代理
    try:  # 嘗試啟動瀏覽器
        driver = multi_window_setup.setup_driver(position)  # 啟動瀏覽器
        task_status["driver"] = driver  # 將瀏覽器實例存入任務狀態
        task_status["worker_id"] = worker_id  # 將 worker_id 存入任務狀態
    except Exception as e:  # 如果出現錯誤，print錯誤信息
        print(f"Worker {worker_id}: 初始化 driver 时出错: {e}")

    # 初始化代理配置
    proxy_config = {  # 代理配置
        "host": account_info["host"],  # 代理主機   
        "port": account_info["port"],  # 代理端口
        "proxy_username": account_info["proxy_username"],  # 代理用戶名
        "proxy_password": account_info["proxy_password"]  # 代理密碼
    }

    # 創建 FacebookBot 實例，並設置代理
    facebook_bot = FacebookBot(driver, proxy_config, worker_id)
    
    if facebook_bot.driver is None:  # 如果瀏覽器實例為空，print錯誤信息    
        print(f"Worker {worker_id}: 跳過帳號 {account_info['account']}，因為代理配置失敗")
        return  # 跳過該帳號

    try:  # 嘗試登錄 Facebook
        # Step 2: 登錄 Facebook
        login_success = facebook_bot.login(account_info)  # 登錄 Facebook

        # 如果登錄失敗，直接結束該帳號的操作
        if not login_success:  
            print(f"Worker {worker_id}: 登錄失敗，跳過發文操作")
            return  # 跳過該帳號    
        
        print(f"Worker {worker_id}: 登錄成功，開始處理帳號 {account_info['account']} 的操作...")

        # Step 3: 開始處理發文、留言或爬蟲操作
        if operation == "post" and "posts" in account_info and account_info["posts"]:  # 如果操作類型為發文，且有發文資料
            print(f"Worker {worker_id}: 開始發文操作...")
            try:  # 嘗試處理發文操作
                post_manager = PostManager(driver, worker_id)  # 創建 PostManager 實例  
                post_manager.process_posts(account_info["posts"], task_status)  # 處理發文操作
            except Exception as e:  # 如果出現錯誤，print錯誤信息
                print(f"Worker {worker_id}: 發文操作過程中出現錯誤: {e}")

        elif operation == "comment" and "comments" in account_info and account_info["comments"]:
            print(f"Worker {worker_id}: 開始留言互動操作...")
            try:  # 嘗試處理留言互動操作
                comment_manager = CommentManager(driver, worker_id)  # 創建 CommentManager 實例
                comment_manager.process_comments(account_info["comments"], task_status)  # 處理留言互動操作
            except Exception as e:  # 如果出現錯誤，print錯誤信息
                print(f"Worker {worker_id}: 留言互動過程中出現錯誤: {e}")
        
        elif operation == "crawl" and "crawls" in account_info and account_info["crawls"]:
            print(f"Worker {worker_id}: 開始爬蟲操作...")
            try:  # 嘗試處理爬蟲操作
                crawl_manager = CrawlManager(driver, worker_id)  # 創建 CrawlManager 實例
                crawl_manager.process_crawls(account_info["crawls"], task_status)  # 處理爬蟲操作
            except Exception as e:  # 如果出現錯誤，print錯誤信息   
                print(f"Worker {worker_id}: 爬蟲過程中出現錯誤: {e}")
                
        elif operation == "click" and "clicks" in account_info and account_info["clicks"]:
            print(f"Worker {worker_id}: 開始點擊操作...")
            try:  # 嘗試處理點擊操作
                click_manager = ClickManager(driver, worker_id)  # 創建 ClickManager 實例
                click_manager.process_clicks(account_info["clicks"], task_status)  # 處理點擊操作
            except Exception as e:  # 如果出現錯誤，print錯誤信息
                print(f"Worker {worker_id}: 點擊過程中出現錯誤: {e}")
                
        elif operation == "navigate" and "navigates" in account_info and account_info["navigates"]:
            print(f"Worker {worker_id}: 開始跳轉操作...")
            try:  # 嘗試處理跳轉操作
                navigate_manager = NavigateManager(driver, worker_id)  # 創建 NavigateManager 實例
                navigate_manager.process_navigates(account_info["navigates"], task_status)  # 處理跳轉操作
            except Exception as e:  # 如果出現錯誤，print錯誤信息
                print(f"Worker {worker_id}: 跳轉過程中出現錯誤: {e}")

    except Exception as e:  # 如果出現錯誤，print錯誤信息
        print(f"Worker {worker_id}: 帳號 {account_info['account']} 操作時發生錯誤: {e}")

    finally: 
        # Step 5: 關閉瀏覽器
        facebook_bot.quit()  # 關閉瀏覽器
        task_status["driver"] = None  # 將瀏覽器實例設為 None   
        task_status["completed"] = True  # 標記任務為已完成
        print(f"Worker {worker_id}: 帳號 {account_info['account']} 的任務已結束")

def process_accounts(accounts, positions, max_workers, operation):
    """
    通用的帳號處理函數，用於處理發文或留言。
    :param accounts: 帳號列表
    :param positions: 瀏覽器窗口位置
    :param max_workers: 最大並行數
    :param operation: 操作類型 ("post"、"comment"、"crawl"、"click" 或 "navigate")
    """
    tasks_status = {}  # 用於存儲任務狀態
    all_tasks_completed = threading.Event()  # 用於監控所有任務是否完成

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []  # 用於存儲任務
        for index, account_info in enumerate(accounts):
            position = positions[index % len(positions)]  # 計算視窗位置
            task_id = f"task_{index}"  # 計算task_id
            worker_id = f"{index + 1}"  # 計算worker_id

            # 初始化任務狀態
            task_status = {"account": account_info["account"], "driver": None, "stop": False, "completed": False}
            tasks_status[task_id] = task_status

            if operation == "post":
                future = executor.submit(process_post_account, account_info, position, task_status, worker_id)
            elif operation == "comment":
                future = executor.submit(process_comment_account, account_info, position, task_status, worker_id)
            elif operation == "crawl":
                future = executor.submit(process_crawl_account, account_info, position, task_status, worker_id)
            elif operation == "click":
                future = executor.submit(process_click_account, account_info, position, task_status, worker_id)
            elif operation == "navigate":
                future = executor.submit(process_navigate_account, account_info, position, task_status, worker_id)
            else:
                raise ValueError(f"未知的操作類型: {operation}")

            futures.append(future)

        # 啟動任務監控
        monitor = TaskMonitor(tasks_status, all_tasks_completed)
        monitor_thread = threading.Thread(target=monitor.run, name=f"TaskMonitor-{operation}", daemon=True)
        monitor_thread.start()

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"處理帳號時發生錯誤: {e}")

        all_tasks_completed.set()  # 設置所有任務完成事件
        monitor_thread.join(timeout=5)  # 等待監控線程完成

# 主流程函數
def facebook_controller():
    """
    Facebook Bot 主流程函數
    """    
    data_loader = DataLoader(EXCEL_PATH)  # 創建 DataLoader 實例
    post_accounts, comment_accounts, crawl_accounts, click_accounts, navigate_accounts = data_loader.load_account_data()  # 加載帳號資料
    max_workers = MAX_WORKERS  # 設置並行的最大線程數

    if post_accounts:  # 如果發文帳號存在
        print("開始處理發文帳號...")
        process_accounts(post_accounts, positions, max_workers, operation="post")  # 處理發文帳號

    if comment_accounts:  # 如果留言帳號存在
        print("開始處理留言帳號...")
        process_accounts(comment_accounts, positions, max_workers, operation="comment")  # 處理留言帳號
    
    if crawl_accounts:  # 如果爬蟲帳號存在
        print("開始處理爬蟲帳號...")
        process_accounts(crawl_accounts, positions, max_workers, operation="crawl")  # 處理爬蟲帳號
        
    if click_accounts:  # 如果點擊帳號存在
        print("開始處理點擊帳號...")
        process_accounts(click_accounts, positions, max_workers, operation="click")  # 處理點擊帳號
        
    if navigate_accounts:  # 如果點擊帳號存在
        print("開始處理跳轉帳號...")
        process_accounts(navigate_accounts, positions, max_workers, operation="navigate")  # 處理點擊帳號

# 確保直接運行 facebook_controller.py 時會執行主流程
if __name__ == "__main__":
    facebook_controller()