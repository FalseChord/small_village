from datetime import datetime, timedelta
from .memory import Memory
from typing import List, Dict

class BasePersona:
    """基礎人格類別，包含共用的記憶相關功能"""
    def __init__(self, embedding_interface, gpt_interface):
        self.memory = Memory(embedding_interface)
        self.gpt = gpt_interface  # 添加 GPT 介面
        self.conversation_history = {}  # 依照對話對象分類
        
    def add_event_memory(self, description, keywords, poignancy, created_time):
        """添加事件記憶"""
        expiration = created_time + timedelta(days=60)
        
        return self.memory.add_memory(
            created_time=created_time,
            expiration=expiration,
            memory_type="event",
            description=description,
            keywords=keywords,
            poignancy=poignancy
        )

    def get_last_chat_with(self, target_name):
        """獲取與特定對象的最後一次對話"""
        return self.memory.get_last_chat(target_name)

class MainPersona(BasePersona):
    def __init__(self, persona_data, embedding_interface, gpt_interface):
        super().__init__(embedding_interface, gpt_interface)
        self.name = persona_data["name"]
        self.age = persona_data["age"]
        self.innate_traits = persona_data["innate_traits"]
        self.learned_traits = persona_data["learned_traits"]
        self.current_status = persona_data["current_status"]
        self.lifestyle = persona_data["lifestyle"]
        self.biography = persona_data["biography"]
        self.relationships = persona_data.get("relationships", {})
        self.current_state = None
        
    def get_relationship_with(self, person_name: str) -> Dict:
        """獲取與特定人物的關係資訊"""
        return self.relationships.get(person_name, {})

    def update_current_state(self, new_state):
        """更新人物當前狀態"""
        self.current_state = new_state
        
    def get_current_state(self):
        """獲取人物當前狀態"""
        return self.current_state if self.current_state else "一般狀態"

class SecondaryPersona(BasePersona):
    def __init__(self, persona_data: Dict, embedding_interface, gpt_interface):  # 添加 gpt_interface 參數
        super().__init__(embedding_interface, gpt_interface)  # 傳遞給父類
        self.name = persona_data["name"]
        self.age = persona_data["age"]
        self.innate_traits = persona_data["innate_traits"]
        self.learned_traits = persona_data["learned_traits"]
        self.current_status = persona_data["current_status"]
        self.lifestyle = persona_data["lifestyle"]
        self.biography = persona_data["biography"]
        self.relationship_with_main = persona_data["relationship_with_main"]

        