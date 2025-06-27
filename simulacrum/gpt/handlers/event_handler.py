from typing import Dict
from .base_handler import BaseHandler

class EventHandler(BaseHandler):
    def generate(self, persona_data: Dict) -> Dict:
        """生成事件"""
        prompt = self._create_prompt(persona_data)
        event = self.interface._call_gpt(prompt, 'event_generator')
        
        return event
        
    def _create_prompt(self, persona_data: Dict) -> str:
        """創建事件生成提示"""
        return (
            f"請根據以下資訊，生成一個發生在"
            f"{persona_data['time_period']} {persona_data['time']} "
            f"的事件。\n\n"
            
            f"人物資料：\n"
            f"姓名：{persona_data['name']}\n"
            f"身份：{persona_data['current_status']}\n"
            f"個性特質：{', '.join(persona_data['innate_traits'])}\n"
            f"生活型態：{persona_data['lifestyle']}\n"
            f"背景：{persona_data['biography']}\n\n"
            
            "請生成一個合理且具體的事件，需要：\n"
            "1. 符合人物的身份和性格特徵\n"
            "2. 符合時間點的合理活動\n"
            "3. 包含具體的場景和互動細節\n"
            "4. 反映人物的生活重心和目標\n"
            "5. 考慮人物的背景和家庭關係\n\n"
            
            "請以 JSON 格式返回：\n"
            "{\n"
            '  "description": "詳細的事件描述",\n'
            '  "location": "事件發生的地點",\n'
            '  "involved_people": ["相關人物1", "相關人物2", ...]\n'
            "}\n"
        ) 