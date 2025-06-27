from datetime import timedelta, date
from typing import Dict
from .event_generator import EventGenerator
from .dialogue_generator import DialogueGenerator
import json, os, hashlib
from datetime import datetime

class Simulator:
    def __init__(self, main_persona, gpt_interface, embedding_interface, secondary_personas):
        self.main_persona = main_persona
        self.secondary_personas = secondary_personas
        
        self.event_generator = EventGenerator(gpt_interface)
        self.dialogue_generator = DialogueGenerator(gpt_interface)
        self.gpt = gpt_interface
        self.embedding_interface = embedding_interface
        self.current_date = date.today()
        self.daily_activities = []
        
        # Create a new folder for this execution
        self.base_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        self.execution_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.data_dir = os.path.join(self.base_data_dir, self.execution_timestamp)
        
        # Create the execution directory and its subdirectories
        os.makedirs(os.path.join(self.data_dir, "events"), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "memories", "human"), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "memories", "embeddings"), exist_ok=True)
        
    def step_day(self):
        """生成事件和對話"""
        
        # 清理過期記憶
        self.main_persona.memory.cleanup_expired_memories(self.current_date)

        daily_events = self.event_generator.generate_daily_events(
            self.main_persona,
            self.current_date
        )

        daily_dialogues = self.dialogue_generator.generate_daily_dialogues(
            main_persona=self.main_persona,
            secondary_personas=self.secondary_personas,
            current_date=self.current_date
        )

        # 記錄所有活動
        self.daily_activities = []
        for event in daily_events:
            self._process_event(event)
            
        for dialogue in daily_dialogues:
            self._process_dialogue(dialogue)

        # 生成每日反思和更新狀態
        self._generate_daily_reflection()

        self._save_daily_memories()
        self._save_daily_events()

        """推進一天"""
        self.current_date += timedelta(days=1)
        return self.daily_activities
        
    def _process_event(self, event: Dict):
        """處理單個事件"""
        self.main_persona.add_event_memory(
            description=event['description'],
            keywords=event['keywords'],
            poignancy=event['poignancy'],
            created_time=self.current_date
        )
        
        self.daily_activities.append({
            'time': self.current_date,
            'type': 'event',
            'content': event
        })
        
    def _process_dialogue(self, dialogue: Dict):
        """處理單個對話"""
        # 生成對話摘要
        summary = self.gpt.dialogue_handler.summarize_dialogue(
            dialogue['content'],
            dialogue['participants']
        )
        
        # 儲存對話記憶
        self.main_persona.add_event_memory(
            description=summary['description'],
            keywords=self.gpt.extract_keywords(summary['description']),
            poignancy=self.gpt.calculate_poignancy(summary['description']),
            created_time=self.current_date
        )
        
        self.daily_activities.append({
            'time': self.current_date,
            'type': 'dialogue',
            'content': dialogue
        })
        
    def _generate_daily_reflection(self):
        """生成每日反思和更新狀態"""
        # 獲取當日所有活動的記憶
        daily_memories = self.main_persona.memory.get_memories_by_timerange(
            start_time=self.current_date,
            end_time=self.current_date + timedelta(days=1)
        )
        
        # 生成反思
        reflection = self.gpt.reflection_handler.generate_daily_reflection(
            persona_data={
                "name": self.main_persona.name,
                "current_status": self.main_persona.current_status,
                "innate_traits": self.main_persona.innate_traits,
                "current_state": self.main_persona.current_state
            },
            daily_memories=daily_memories
        )
        
        # 更新主角色狀態
        self.main_persona.update_current_state(reflection['state'])

    def _save_json(self, relative_path: str, data: Dict):
        """保存JSON資料
        
        Args:
            relative_path: 相對於專案根目錄的路徑，例如 'data/events/2024-01-01.json'
            data: 要保存的資料
        """
        # 獲取基礎目錄路徑
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        full_path = os.path.join(base_dir, relative_path)
        
        # 確保目錄存在
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # 寫入檔案
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4, default=str)

    def _save_daily_events(self):
        date_str = self.current_date.strftime("%Y-%m-%d")
        """保存每日事件"""
        events_file = os.path.join(self.data_dir, "events", f"{date_str}.json")
        self._save_json(
            events_file,
            self.daily_activities
        )

    def _save_daily_memories(self, ):
        """保存每日記憶"""
        date_str = self.current_date.strftime("%Y-%m-%d")
        # 準備記憶資料
        memories = []
        memory_nodes = []
        embedding_nodes = {}
        
        memories = self.main_persona.memory.get_memories_by_timerange(
            start_time=self.current_date,
            end_time=self.current_date + timedelta(days=1)
        )

        for memory in memories:
            memory_id = hashlib.md5(f"{memory['description']}{memory['keywords']}".encode()).hexdigest()

            memory_node = {k: v for k, v in memory.items() if k != 'embedding'}
            memory_node['id'] = memory_id
            memory_nodes.append(memory_node)

            embedding_nodes[memory_id] = self.embedding_interface.get_embedding(memory['description'])
        
        # 設定完整的檔案路徑
        memory_file = os.path.join(self.data_dir, "memories", "human", f"{date_str}.json")
        embedding_file = os.path.join(self.data_dir, "memories", "embeddings", f"{date_str}.json")
        
        # 保存記憶和embedding
        self._save_json(
            memory_file,
            memory_nodes
        )
        
        self._save_json(
            embedding_file,
            embedding_nodes
        )
