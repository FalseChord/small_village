from typing import List, Dict, Optional
import openai
import json
import re
import numpy as np
import logging
import os
from datetime import datetime
from .prompts import SystemPrompts
from .handlers import (
    EventHandler,
    DialogueHandler,
    KeywordHandler,
    MemoryHandler
)

class GPTInterface:
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.system_roles = SystemPrompts()
        
        # 初始化各個處理器
        self.event_handler = EventHandler(self)
        self.dialogue_handler = DialogueHandler(self)
        self.keyword_handler = KeywordHandler(self)
        self.memory_handler = MemoryHandler(self)
        
        # 設置日誌系統
        self._setup_logging()

    def _setup_logging(self):
        """設置日誌系統"""
        # 創建 logs 目錄
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
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
        self.logger = logging.getLogger('GPTInterface')

    def _clean_json_response(self, content: str) -> str:
        """清理 GPT 回應，只保留 JSON 部分"""
        # 尋找第一個 { 和最後一個 } 之間的內容
        json_match = re.search(r'{.*}', content, re.DOTALL)
        if json_match:
            return json_match.group()
        return content

    def _log_gpt_request(self, prompt: str, response: Dict, role_type: str, temperature: float = 0.7):
        """記錄 GPT 請求"""
        self.logger.info(f"\n{'='*50}\n"
                        f"Role Type: {role_type}\n"
                        f"Temperature: {temperature}\n"
                        f"Prompt:\n{prompt}\n"
                        f"Response:\n{response}\n"
                        f"{'='*50}\n")

    def _call_gpt(self, prompt: str, role_type: str, temperature: float = 0.7) -> Optional[Dict]:
        """通用的 GPT 呼叫函數"""
        # 僅使用 gpt-5-mini
        model = "gpt-5-mini"
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": self.system_roles.get(role_type)},
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.choices[0].message.content
            
            # 清理回應，只保留 JSON 部分
            cleaned_content = self._clean_json_response(content)
            
            try:
                result = json.loads(cleaned_content)
                # 統一在這裡記錄 GPT 請求
                self._log_gpt_request(prompt, result, role_type, temperature)
                return result
            except json.JSONDecodeError:
                print(f"JSON 解析失敗: {content}")
                return None
                
        except Exception as e:
            print(f"GPT API 呼叫失敗: {str(e)}")
            return None

    # 代理方法，將請求轉發給對應的處理器
    def generate_event(self, persona_data: Dict) -> Dict:
        return self.event_handler.generate(persona_data)
        
    def generate_dialogue(self, prompt: str) -> Dict:
        return self.dialogue_handler.generate(prompt)
        
    def extract_keywords(self, text: str, context: Dict = None) -> List[str]:
        return self.keyword_handler.extract(text, context)
    
    def breakdown_event_to_memories(self, event: Dict, persona_data: Dict) -> Dict:
        return self.memory_handler.breakdown_event_to_memories(event, persona_data)
    
    def breakdown_dialogue_to_memories(self, dialogue: Dict, persona_data: Dict) -> Dict:
        return self.memory_handler.breakdown_dialogue_to_memories(dialogue, persona_data)
