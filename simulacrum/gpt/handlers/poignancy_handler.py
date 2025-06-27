from typing import Dict, Optional
from .base_handler import BaseHandler

class PoignancyHandler(BaseHandler):
    def calculate(self, description: str) -> float:
        """計算事件的重要性分數"""
        prompt = self._create_prompt(description)
        response = self.interface._call_gpt(prompt, 'poignancy_analyzer', temperature=0.3)
        
        if response:
            return self._calculate_weighted_score(response)
        return 0.5  # 預設值
        
    def _create_prompt(self, description: str) -> str:
        return (
            "請分析以下事件的重要性：\n\n"
            f"{description}\n\n"
            "請從以下幾個面向進行評分(0.0-1.0)：\n"
            "1. 情感強度：事件引發的情感反應強度\n"
            "2. 社交影響：涉及的人物關係和互動程度\n"
            "3. 持續影響：對未來行為和決策的影響程度\n"
            "4. 獨特程度：事件的特殊性和記憶點\n\n"
            
            "請以 JSON 格式返回：\n"
            "{\n"
            '  "emotional_intensity": 0.0-1.0,\n'
            '  "social_impact": 0.0-1.0,\n'
            '  "lasting_effect": 0.0-1.0,\n'
            '  "uniqueness": 0.0-1.0\n'
            "}"
        )
        
    def _calculate_weighted_score(self, scores: Dict) -> float:
        """計算加權分數"""
        weights = {
            'emotional_intensity': 0.3,
            'social_impact': 0.25,
            'lasting_effect': 0.3,
            'uniqueness': 0.15
        }
        
        total_score = sum(
            scores[key] * weight 
            for key, weight in weights.items()
        )
        
        return max(0.0, min(1.0, total_score)) 