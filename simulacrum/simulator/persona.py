from datetime import datetime, timedelta
from .memory import Memory
from typing import List, Dict

class BasePersona:
    """基礎人格類別，包含共用的記憶相關功能"""
    def __init__(self, embedding_interface, gpt_interface):
        self.memory = Memory(embedding_interface)
        self.gpt = gpt_interface  # 添加 GPT 介面
        self.conversation_history = {}  # 依照對話對象分類

    def add_event_memory(self, description, keywords, emotional_intensity, created_time,
                         memory_type="event", extra_fields=None):
        """添加記憶

        Args:
            description: 記憶描述
            keywords: 關鍵字列表
            emotional_intensity: 情緒強度 (0.0-1.0)，整合了重要性和記憶強度
            created_time: 創建時間
            memory_type: 記憶類型 ("event", "episodic", "semantic", "emotional", "dialogue")
            extra_fields: 額外字段字典
        """
        # 如果 emotional_intensity 為 None，使用預設值 0.3
        if emotional_intensity is None:
            emotional_intensity = 0.3

        return self.memory.add_memory(
            created_time=created_time,
            memory_type=memory_type,
            description=description,
            keywords=keywords,
            emotional_intensity=emotional_intensity,
            extra_fields=extra_fields
        )

    def get_last_chat_with(self, target_name):
        """獲取與特定對象的最後一次對話"""
        return self.memory.get_last_chat(target_name)

class Persona(BasePersona):
    """統一的人格類別，所有角色都使用此類別"""
    def __init__(self, persona_data, embedding_interface, gpt_interface):
        super().__init__(embedding_interface, gpt_interface)
        self.name = persona_data["name"]
        self.first_name = persona_data.get("first_name", "")
        self.last_name = persona_data.get("last_name", "")
        self.age = persona_data["age"]
        self.innate = persona_data["innate"]  # 保持原始字串格式
        self.innate_traits = [trait.strip() for trait in persona_data["innate"].split("、")]
        self.learned = persona_data["learned"]
        self.lifestyle = persona_data["lifestyle"]
        self.biography = persona_data["biography"]
        self.relationships = persona_data.get("relationships", {})

    def get_relationship_with(self, person_name: str) -> Dict:
        """獲取與特定人物的關係資訊"""
        return self.relationships.get(person_name, {})

