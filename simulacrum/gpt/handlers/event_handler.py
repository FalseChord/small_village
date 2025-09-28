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
        recent_categories = persona_data.get('recent_categories', [])
        recent_categories_text = ""
        if recent_categories:
            recent_categories_text = f"\n最近的事件類別：{', '.join(recent_categories)}\n"
        
        return (
            f"請根據以下資訊，生成一個發生在"
            f"{persona_data['time_period']} {persona_data['time']} "
            f"的事件。{recent_categories_text}\n"
            
            f"人物資料：\n"
            f"姓名：{persona_data['name']}\n"
            f"個性特質：{', '.join(persona_data['innate_traits'])}\n"
            f"生活型態：{persona_data['lifestyle']}\n"
            f"背景：{persona_data['biography']}\n\n"
            
            "【事件多樣性要求】請從以下類別中選擇不同類型的事件：\n"
            "1. 工作/學習活動：會議、課程、研究、專案進行\n"
            "2. 個人興趣：閱讀、運動、烹飪、創作、學習新技能\n"
            "3. 社交活動：朋友聚會、社團活動、志工服務、興趣小組\n"
            "4. 生活管理：購物、整理、規劃、健康檢查\n"
            "5. 休閒娛樂：看電影、聽音樂、遊戲、戶外活動\n"
            "6. 意外/特殊：突發狀況、驚喜、新發現、靈感\n"
            "7. 自我提升：冥想、寫作、反思、目標設定\n"
            "8. 環境互動：天氣變化、鄰居互動、社區活動\n\n"
            
            "【避免重複】請避免以下常見模式：\n"
            "• 不要總是選擇打電話或傳訊息\n"
            "• 不要總是選擇家庭聯繫\n"
            "• 要考慮人物的具體生活環境和興趣\n"
            "• 要包含具體的活動和互動細節\n"
            f"• 如果最近有{recent_categories_text}，請選擇不同的類別\n\n"
            
            "【事件品質要求】：\n"
            "1. 具體明確：包含具體的活動、地點、互動對象\n"
            "2. 符合時間：考慮該時間段的合理活動\n"
            "3. 符合個性：反映人物的性格特質和興趣\n"
            "4. 有變化性：每天的事件應該有不同的重點\n"
            "5. 真實感：符合真實生活的可能性\n\n"
            
            "請以 JSON 格式返回：\n"
            "{\n"
            '  "description": "詳細的事件描述，包含具體活動和互動",\n'
            '  "location": "事件發生的具體地點",\n'
            '  "involved_people": ["相關人物1", "相關人物2", ...],\n'
            '  "event_category": "事件類別（工作/學習/個人興趣/社交活動/生活管理/休閒娛樂/意外/特殊/自我提升/環境互動）"\n'
            "}\n"
        ) 