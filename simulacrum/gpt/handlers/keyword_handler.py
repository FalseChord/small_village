from typing import Dict, List, Optional
from .base_handler import BaseHandler

class KeywordHandler(BaseHandler):
    def extract(self, text: str, context: Dict = None) -> List[str]:
        """從文本中提取關鍵字"""
        prompt = self._create_prompt(text, context)
        response = self.interface._call_gpt(prompt, 'keyword_extractor', temperature=0.3)
        return response.get('keywords', []) if response else []
        
    def _create_prompt(self, text: str, context: Dict = None) -> str:
        prompt = (
            "請從以下文本中提取關鍵字：\n\n"
            f"{text}\n\n"
        )
        
        if context:
            prompt += (
                f"這是一段{context.get('type', '文本')}。\n"
                f"相關人物：{context.get('persona_name', '未知')}\n\n"
            )
        
        prompt += (
            "請提取：\n"
            "1. 重要的人物名稱\n"
            "2. 地點名稱\n"
            "3. 活動或事件類型\n"
            "4. 重要的物品\n"
            "5. 情緒或狀態詞\n\n"
            
            "請以 JSON 格式返回：\n"
            "{\n"
            '  "keywords": ["關鍵字1", "關鍵字2", ...]\n'
            "}\n"
        )
        
        return prompt 