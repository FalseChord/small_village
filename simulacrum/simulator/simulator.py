from datetime import timedelta, date
from typing import Dict
from .event_generator import EventGenerator
from .dialogue_generator import DialogueGenerator
import json, os, hashlib
from datetime import datetime

class Simulator:
    def __init__(self, personas, gpt_interface, embedding_interface):
        self.personas = personas
        
        self.event_generator = EventGenerator(gpt_interface)
        self.dialogue_generator = DialogueGenerator(gpt_interface)
        self.gpt = gpt_interface
        self.embedding_interface = embedding_interface
        self.current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.daily_activities = []
        
        # Create a new folder for this execution
        self.base_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        self.execution_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.data_dir = os.path.join(self.base_data_dir, self.execution_timestamp)
        
        # Create the execution directory and its subdirectories
        os.makedirs(os.path.join(self.data_dir, "events"), exist_ok=True)
        
    def step_day(self):
        """生成事件和對話"""
        
        # 為每個人格生成事件
        daily_events = []
        for persona in self.personas.values():
            persona_events = self.event_generator.generate_daily_events(
                persona,
                self.current_date
            )
            daily_events.extend(persona_events)

        daily_dialogues = self.dialogue_generator.generate_daily_dialogues(
            all_personas=self.personas,
            current_date=self.current_date
        )

        # 記錄所有活動
        self.daily_activities = []
        
        for event in daily_events:
            self._process_event(event)
            
        for dialogue in daily_dialogues:
            self._process_dialogue(dialogue)

        self._save_daily_memories()
        self._save_daily_events()

        """推進一天"""
        self.current_date += timedelta(days=1)
        return self.daily_activities
        
    def _process_event(self, event: Dict):
        """處理單個事件"""
        persona_name = event.get('person', event.get('name'))
        if persona_name and persona_name in self.personas:
            persona = self.personas[persona_name]
            
            # 準備角色資料
            persona_data = {
                "name": persona.name,
                "innate_traits": persona.innate_traits
            }
            
            # 使用 GPT 進行記憶分割
            try:
                memory_breakdown = self.gpt.breakdown_event_to_memories(event, persona_data)
                self._store_memory_breakdown(memory_breakdown, persona)
            except Exception as e:
                print(f"事件記憶分割失敗 ({persona_name}): {e}")
                # 如果分割失敗，使用原始方式儲存
                persona.add_event_memory(
                    description=event['description'],
                    keywords=event['keywords'],
                    emotional_intensity=event.get('poignancy', 0.3),
                    created_time=self.current_date
                )
        
        self.daily_activities.append({
            'time': self.current_date,
            'type': 'event',
            'content': event
        })
        
    def _process_dialogue(self, dialogue: Dict):
        """處理單個對話"""
        # 為對話中的每個參與者都創建記憶
        for participant_name in dialogue.get('participants', []):
            if participant_name in self.personas:
                persona = self.personas[participant_name]
                
                # 準備角色資料
                persona_data = {
                    "name": persona.name,
                    "innate_traits": persona.innate_traits
                }
                
                # 使用 GPT 進行對話記憶分割
                try:
                    memory_breakdown = self.gpt.breakdown_dialogue_to_memories(dialogue, persona_data)
                    self._store_memory_breakdown(memory_breakdown, persona)
                except Exception as e:
                    print(f"對話記憶分割失敗 ({participant_name}): {e}")
                    # 如果分割失敗，使用原始方式儲存
                    summary = self.gpt.dialogue_handler.summarize_dialogue(
                        dialogue['content'],
                        dialogue['participants']
                    )
                    persona.add_event_memory(
                        description=summary['description'],
                        keywords=self.gpt.extract_keywords(summary['description']),
                        emotional_intensity=0.5,  # 預設值，因為移除了 calculate_poignancy
                        created_time=self.current_date
                    )
        
        self.daily_activities.append({
            'time': self.current_date,
            'type': 'dialogue',
            'content': dialogue
        })
    
    def _store_memory_breakdown(self, memory_breakdown: Dict, persona):
        """儲存記憶分割結果到角色記憶系統"""
        def _store_memory(memory_type: str, memory: Dict):
            persona.add_event_memory(
                description=memory['description'],
                keywords=memory['keywords'],
                emotional_intensity=memory['emotional_intensity'],
                created_time=self.current_date,
                memory_type=memory_type
            )

        if memory_breakdown.get('semantic') and isinstance(memory_breakdown['semantic'], list):
            for memory in memory_breakdown['semantic']:
                _store_memory(memory_type="semantic", memory=memory)
        
        if memory_breakdown.get('episodic') and isinstance(memory_breakdown['episodic'], list):
            for memory in memory_breakdown['episodic']:
                _store_memory(memory_type="episodic", memory=memory)
        
        if memory_breakdown.get('emotional') and isinstance(memory_breakdown['emotional'], list):
            for memory in memory_breakdown['emotional']:
                _store_memory(memory_type="emotional", memory=memory)
        

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

    def _save_daily_memories(self):
        """保存所有記憶"""
        
        # 為每個人格保存記憶
        for persona_name, persona in self.personas.items():
            if not persona.memory.memories:
                continue
            
            # 按日期分組所有記憶
            memories_by_date = {}
            
            for memory in persona.memory.memories:
                # 取得記憶的日期
                memory_date = memory['created_time'].date()
                date_str = memory_date.strftime("%Y-%m-%d")
                
                if date_str not in memories_by_date:
                    memories_by_date[date_str] = []
                memories_by_date[date_str].append(memory)
            
            # 為每個日期保存記憶檔案
            for date_str, memories in memories_by_date.items():
                memory_nodes = []
                embedding_nodes = {}
                
                for memory in memories:
                    memory_id = hashlib.md5(f"{memory['description']}{memory['keywords']}".encode()).hexdigest()

                    memory_node = {k: v for k, v in memory.items() if k != 'embedding'}
                    memory_node['id'] = memory_id
                    memory_nodes.append(memory_node)

                    if 'embedding' in memory:
                        embedding_nodes[memory_id] = memory['embedding']
                
                # 設定完整的檔案路徑（按人格名稱分目錄）
                persona_memory_dir = os.path.join(self.data_dir, persona_name, "memories")
                persona_embedding_dir = os.path.join(self.data_dir, persona_name, "embeddings")
                
                # 確保目錄存在
                os.makedirs(persona_memory_dir, exist_ok=True)
                os.makedirs(persona_embedding_dir, exist_ok=True)
                
                memory_file = os.path.join(persona_memory_dir, f"{date_str}.json")
                embedding_file = os.path.join(persona_embedding_dir, f"{date_str}.json")
                
                # 保存記憶和embedding
                with open(memory_file, 'w', encoding='utf-8') as f:
                    json.dump(memory_nodes, f, ensure_ascii=False, indent=4, default=str)
                
                with open(embedding_file, 'w', encoding='utf-8') as f:
                    json.dump(embedding_nodes, f, ensure_ascii=False, indent=4, default=str)
