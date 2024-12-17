import sys
import logging
import os
from datetime import datetime

class LogManager:
    """
    將標準輸出覆寫，讓 print 的內容同時寫入日誌檔案和顯示在控制台。
    """
    def __init__(self, log_dir="logs/", log_prefix="facebook_rpa"):
        """
        初始化 LogManager。
        :param log_dir: 日誌檔案存放目錄。
        :param log_prefix: 日誌檔案名前綴。
        """
        # 確保日誌目錄存在
        os.makedirs(log_dir, exist_ok=True)

        # 動態設置日誌檔案名稱（包含日期和時間）
        log_file_name = os.path.join(
            log_dir, f"{log_prefix}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        )

        # 配置 logging
        self.logger = logging.getLogger(log_prefix)  # 設置日誌記錄器
        self.logger.setLevel(logging.INFO)  # 設置日誌級別

        # 文件處理器，設置編碼為 UTF-8
        file_handler = logging.FileHandler(log_file_name, encoding="utf-8")  # 設置文件處理器
        file_handler.setLevel(logging.INFO)  # 設置文件處理器級別

        # 控制台處理器
        stream_handler = logging.StreamHandler()  # 設置控制台處理器
        stream_handler.setLevel(logging.INFO)  # 設置控制台處理器級別

        # 日誌格式
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)  # 設置文件處理器格式
        stream_handler.setFormatter(formatter)  # 設置控制台處理器格式  

        # 添加處理器到記錄器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(stream_handler)

        # 替換標準輸出
        sys.stdout = self._StreamLogger(sys.stdout, self.logger.info)  # 設置標準輸出
        sys.stderr = self._StreamLogger(sys.stderr, self.logger.error)  # 設置標準錯誤輸出

    class _StreamLogger:
        """
        一個內部類，用於覆寫標準輸出流，將輸出同時記錄到日誌檔案。
        """
        def __init__(self, stream, log_func):
            self.stream = stream  # 設置輸出流
            self.log_func = log_func  # 設置日誌函數

        def write(self, message):
            if message.strip():  # 忽略空行
                self.log_func(message.strip())  # 寫入日誌

        def flush(self):
            self.stream.flush()  # 刷新輸出流       

    def get_logger(self):
        """
        獲取日誌記錄器實例。
        :return: logging.Logger
        """
        return self.logger
