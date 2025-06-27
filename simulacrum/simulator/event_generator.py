import random
from datetime import datetime
from typing import Dict, List, Optional

class EventGenerator:
    def __init__(self, gpt_interface):
        self.gpt = gpt_interface
        
        # 定義每日可能的時間段
        self.time_periods = [
            "早上",
            "下午",
            "晚上"
        ]

    def generate_daily_events(self, main_persona, current_time: datetime) -> List[Dict]:
        """生成每日事件"""
        events = []
        
        # 隨機選擇1-2個時間段生成事件
        event_count = random.randint(1, 1)
        selected_periods = random.sample(self.time_periods, event_count)
        
        # 為每個選定的時間段生成事件
        for period in selected_periods:
            event = self._generate_event(
                event_type="daily",
                context={
                    'time_period': period,
                    'current_time': current_time,
                    'date': current_time.strftime("%Y年%m月%d日")
                },
                persona=main_persona
            )
            
            if event:
                events.append(event)
        
        return events

    def _generate_event(self, event_type: str, context: Dict, persona) -> Optional[Dict]:
        """生成具體事件"""
        # 生成具體時間
        event_time = self._generate_time_for_period(
            current_time=context.get('current_time', datetime.now()),
            period=context.get('time_period', '某個時間')
        )
        
        # 準備人物資料
        persona_data = {
            "name": persona.name,
            "current_status": persona.current_status,
            "innate_traits": persona.innate_traits,
            "lifestyle": persona.lifestyle,
            "biography": persona.biography,
            "time_period": context.get('time_period', '某個時間'),
            "date": context.get('date', datetime.now().strftime("%Y年%m月%d日")),
            "time": event_time.strftime("%H:%M")
        }
        
        # 使用 EventHandler 生成事件
        event = self.gpt.event_handler.generate(persona_data)
        
        if event:
            # 添加時間資訊
            event['time'] = event_time
            event['poignancy'] = self.gpt.calculate_poignancy(event['description'])
            event['keywords'] = self.gpt.extract_keywords(
                event['description'],
                context={'type': 'event', 'persona_name': persona_data['name']}
            )
            return event
        
        return None

    def _generate_time_for_period(self, current_time: datetime, period: str) -> datetime:
        """根據時間段生成具體時間"""
        if period == "早上":
            hour = random.randint(6, 11)
        elif period == "下午":
            hour = random.randint(12, 17)
        else:  # 晚上
            hour = random.randint(18, 22)
            
        minute = random.randint(0, 59)
        
        return datetime(
            current_time.year,
            current_time.month,
            current_time.day,
            hour,
            minute
        ) 