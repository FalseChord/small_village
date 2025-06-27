from typing import Dict, Optional
import logging
import os
from datetime import datetime

class BaseHandler:
    def __init__(self, interface):
        self.interface = interface
        self._setup_logging()
        
    def _setup_logging(self):
        """設置日誌系統"""
        # 創建 logs 目錄
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # 設置日誌格式
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(os.path.join(log_dir, f'gpt_requests_{datetime.now().strftime("%Y%m%d")}.log')),
                logging.StreamHandler()
            ]
        )
        
        # 創建處理器特定的日誌記錄器
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def _log_gpt_request(self, prompt: str, response: Dict, handler_name: str, temperature: float = 0.7):
        """記錄 GPT 請求"""
        self.logger.info(f"\n{'='*50}\n"
                        f"Handler: {handler_name}\n"
                        f"Temperature: {temperature}\n"
                        # f"Prompt:\n{prompt}\n"
                        f"Response:\n{response}\n"
                        f"{'='*50}\n") 