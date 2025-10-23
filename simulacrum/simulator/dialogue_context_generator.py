import random
from datetime import datetime
from typing import Dict, List, Optional

class DialogueContextGenerator:
    def __init__(self, gpt_interface):
        self.gpt = gpt_interface
        
        # 定義對話可能發生的時間段
        self.time_periods = [
            "早上",
            "下午", 
            "晚上"
        ]
        
        # 情境類別追蹤，用於平衡情境多樣性
        self.recent_context_categories = []  # 追蹤最近的情境類別

    def generate_dialogue_context(self, persona1, persona2, current_time: datetime) -> Optional[Dict]:
        """生成對話情境"""
        
        # 隨機選擇時間段
        time_period = random.choice(self.time_periods)
        
        # 生成具體時間
        context_time = self._generate_time_for_period(
            current_time=current_time,
            period=time_period
        )
        
        # 準備角色資料
        personas_data = {
            "persona1": {
                "name": persona1.name,
                "innate_traits": persona1.innate_traits,
                "lifestyle": persona1.lifestyle,
                "biography": persona1.biography
            },
            "persona2": {
                "name": persona2.name,
                "innate_traits": persona2.innate_traits,
                "lifestyle": persona2.lifestyle,
                "biography": persona2.biography
            },
            "time_period": time_period,
            "date": current_time.strftime("%Y年%m月%d日"),
            "time": context_time.strftime("%H:%M"),
            "recent_categories": self.recent_context_categories[-3:]  # 提供最近3個情境類別
        }
        
        # 使用 DialogueContextHandler 生成情境
        context = self.gpt.dialogue_context_handler.generate(personas_data)
        
        if context:
            # 添加時間資訊
            context['time'] = context_time
            context['time_period'] = time_period
            
            # 追蹤情境類別
            if 'context_category' in context:
                self.recent_context_categories.append(context['context_category'])
                # 保持最近10個情境的追蹤
                if len(self.recent_context_categories) > 10:
                    self.recent_context_categories.pop(0)
            
            return context
        
        return None

    def _generate_time_for_period(self, current_time: datetime, period: str) -> datetime:
        """根據時間段生成具體時間"""
        if period == "早上":
            hour = random.randint(7, 11)
        elif period == "下午":
            hour = random.randint(13, 17)
        else:  # 晚上
            hour = random.randint(18, 21)
            
        minute = random.randint(0, 59)
        
        return datetime(
            current_time.year,
            current_time.month,
            current_time.day,
            hour,
            minute
        )
