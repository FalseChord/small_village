from typing import Dict, List
from .base_handler import BaseHandler

class ReflectionHandler(BaseHandler):
    # def generate(self, persona_data: Dict, dialogue_content: str, recent_memories: List) -> Dict:
    #     """生成對話反思"""
    #     prompt = self._create_prompt(persona_data, dialogue_content, recent_memories)
    #     return self.interface._call_gpt(prompt, 'reflection_generator')
        
    # def _create_prompt(self, persona_data: Dict, dialogue_content: str, recent_memories: List) -> str:
    #     prompt = (
    #         f"請根據以下對話內容，生成{persona_data['name']}的內心反思：\n\n"
            
    #         f"人物資料：\n"
    #         f"姓名：{persona_data['name']}\n"
    #         f"身份：{persona_data['current_status']}\n"
    #         f"個性特質：{', '.join(persona_data['innate_traits'])}\n"
    #         f"當前狀態：{persona_data['current_state']}\n\n"
            
    #         f"對話內容：\n{dialogue_content}\n\n"
            
    #         f"相關記憶：\n"
    #     )
        
    #     for memory in recent_memories[:2]:
    #         prompt += f"- {memory['description']}\n"
            
    #     prompt += (
    #         "\n請生成一段內心反思，需要：\n"
    #         "1. 反映人物的性格和心理狀態\n"
    #         "2. 包含對對話內容的情感反應\n"
    #         "3. 連結到個人經歷和記憶\n"
    #         "4. 可能影響未來的決定或行為\n\n"
            
    #         "請以 JSON 格式返回：\n"
    #         "{\n"
    #         '  "reflection": "詳細的反思內容",\n'
    #         '  "keywords": ["關鍵字1", "關鍵字2", ...],\n'
    #         '  "poignancy": 反思的重要性(0.0-1.0)\n'
    #         "}\n"
    #     )
        
    #     return prompt 

    def generate_daily_reflection(self, persona_data: Dict, daily_memories: List) -> Dict:
        """生成每日反思與狀態"""
        prompt = self._create_daily_reflection_prompt(persona_data, daily_memories)
        response = self.interface._call_gpt(prompt, 'reflection_generator')
        return response


    def _create_daily_reflection_prompt(self, persona_data: Dict, daily_memories: List) -> str:
        prompt = (
            f"請根據今天的經歷，描述{persona_data['name']}的心理活動與狀態變化：\n\n"
            
            f"人物資料：\n"
            f"姓名：{persona_data['name']}\n"
            f"身份：{persona_data['current_status']}\n"
            f"個性特質：{', '.join(persona_data['innate_traits'])}\n"
            f"昨天的狀態：{persona_data['current_state']}\n\n"
            
            f"今日經歷：\n"
        )
        
        for memory in daily_memories:
            prompt += f"- {memory['description']}\n"
            
        prompt += (
            "\n請描述：\n"
            "- 人物對這些經歷的內心感受與想法\n"
            "- 經歷這些事情後，人物的整體狀態\n\n"
            
            "注意事項：\n"
            "- 請保持描述的具體性和真實感\n"
            "- 確保反應符合人物的性格特質\n"
            "- 聚焦於當下的感受和狀態\n\n"
            
            "請以 JSON 格式返回：\n"
            "{\n"
            '  "reflection": "對今日經歷的內心感受與想法",\n'
            '  "state": "經歷這些事情後的整體狀態，可以是情緒、感受、想法、身體狀態等描述"\n'
            "}\n"
        )
        
        return prompt 