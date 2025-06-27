from typing import List, Dict, Optional
import openai
import json
import re
import numpy as np
from .prompts import SystemPrompts
from .handlers import (
    EventHandler,
    DialogueHandler,
    ReflectionHandler,
    KeywordHandler,
    PoignancyHandler
)

class GPTInterface:
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.system_roles = SystemPrompts()
        
        # 初始化各個處理器
        self.event_handler = EventHandler(self)
        self.dialogue_handler = DialogueHandler(self)
        self.reflection_handler = ReflectionHandler(self)
        self.keyword_handler = KeywordHandler(self)
        self.poignancy_handler = PoignancyHandler(self)

    def _clean_json_response(self, content: str) -> str:
        """清理 GPT 回應，只保留 JSON 部分"""
        # 尋找第一個 { 和最後一個 } 之間的內容
        json_match = re.search(r'{.*}', content, re.DOTALL)
        if json_match:
            return json_match.group()
        return content

    def _call_gpt(self, prompt: str, role_type: str, temperature: float = 0.7) -> Optional[Dict]:
        """通用的 GPT 呼叫函數"""
        #model="gpt-4.1",
        model="gpt-4.5-preview",
        # model="o4-mini",
        if model == "o4-mini":
            temperature=1
        try:
            response = openai.ChatCompletion.create(
                #model="gpt-4.1",
                model="gpt-4.5-preview",
                #model="o4-mini",
                messages=[
                    {"role": "system", "content": self.system_roles.get(role_type)},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature
            )
            
            content = response.choices[0].message.content
            
            # 清理回應，只保留 JSON 部分
            cleaned_content = self._clean_json_response(content)
            
            try:
                return json.loads(cleaned_content)
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
        
    def generate_reflection(self, persona_data: Dict, dialogue_content: str, recent_memories: List) -> Dict:
        return self.reflection_handler.generate(persona_data, dialogue_content, recent_memories)
        
    def extract_keywords(self, text: str, context: Dict = None) -> List[str]:
        return self.keyword_handler.extract(text, context)
        
    def calculate_poignancy(self, description: str) -> float:
        return self.poignancy_handler.calculate(description)
