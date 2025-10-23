from typing import Dict
from .base_handler import BaseHandler

class DialogueContextHandler(BaseHandler):
    def generate(self, personas_data: Dict) -> Dict:
        """生成對話情境"""
        prompt = self._create_prompt(personas_data)
        context = self.interface._call_gpt(prompt, 'dialogue_context_generator')
        
        return context
        
    def _create_prompt(self, personas_data: Dict) -> str:
        """創建對話情境生成提示"""
        persona1_info = personas_data["persona1"]
        persona2_info = personas_data["persona2"]
        
        # 準備最近情境類別
        recent_categories = personas_data.get('recent_categories', [])
        recent_categories_text = ""
        if recent_categories:
            recent_categories_text = f"\n最近的情境類別：{', '.join(recent_categories)}\n"
        
        # 過濾掉最近使用過的情境類別，避免重複
        context_categories = [
            "日常偶遇", "約定見面", "工作場合", "休閒時光",
            "家庭聚會", "學習環境", "購物場所", "交通途中",
            "語音通話", "訊息聊天", "視訊通話", "線上互動"
        ]
        available_categories = [cat for cat in context_categories if cat not in recent_categories]
        if not available_categories:  # 如果所有類別都用過了，就重新使用所有類別
            available_categories = context_categories
        
        return (
            f"請根據以下角色資訊和時間，生成一個自然的對話情境：\n\n"
            f"時間：{personas_data['date']} {personas_data['time_period']} {personas_data['time']}{recent_categories_text}\n"
            
            f"角色1：{persona1_info['name']}\n"
            f"個性：{', '.join(persona1_info['innate_traits'])}\n"
            f"生活方式：{persona1_info['lifestyle']}\n"
            f"背景：{persona1_info['biography']}\n\n"
            
            f"角色2：{persona2_info['name']}\n"
            f"個性：{', '.join(persona2_info['innate_traits'])}\n"
            f"生活方式：{persona2_info['lifestyle']}\n"
            f"背景：{persona2_info['biography']}\n\n"
            
            "【情境多樣性要求】請從以下類別中選擇不同類型的情境：\n"
            "1. 日常偶遇：街上、商店、電梯等隨機相遇\n"
            "2. 約定見面：咖啡廳、餐廳、公園等預定地點\n"
            "3. 工作場合：辦公室、會議室、工作場所\n"
            "4. 休閒時光：電影院、健身房、書店等休閒場所\n"
            "5. 家庭聚會：家中、親戚家、節慶場合\n"
            "6. 學習環境：學校、圖書館、補習班\n"
            "7. 購物場所：商場、超市、市場\n"
            "8. 交通途中：公車、捷運、計程車等移動中\n"
            "9. 語音通話：電話、語音訊息等語音交流\n"
            "10. 訊息聊天：文字訊息、即時通訊等文字交流\n"
            "11. 視訊通話：視訊會議、視訊聊天等視覺交流\n"
            "12. 線上互動：社群媒體、遊戲、線上活動等\n\n"
            
            "【避免重複】請避免以下常見模式：\n"
            "• 不要總是選擇相同的場所\n"
            "• 不要總是使用相同的觸發方式\n"
            "• 要考慮角色的具體生活環境和關係\n"
            "• 要包含具體的地點和互動細節\n"
            f"• 如果最近有{recent_categories_text}，請選擇不同的類別\n\n"
            
            "【情境品質要求】：\n"
            "1. 具體明確：包含具體的地點、觸發方式和氛圍\n"
            "2. 符合時間：考慮該時間段的合理活動\n"
            "3. 符合關係：反映角色間的關係和互動模式\n"
            "4. 有變化性：每次的情境應該有不同的重點\n"
            "5. 真實感：符合真實生活的可能性\n\n"
            
            f"情境類別（請從中選擇一個）：{', '.join(available_categories)}\n\n"
            
            "請以 JSON 格式返回：\n"
            "{\n"
            '  "description": "詳細的對話情境描述，包含具體的地點、觸發方式和氛圍",\n'
            '  "context_category": "情境類別（從上述類別中選擇一個）"\n'
            "}\n"
        )
