from datetime import datetime
from typing import List, Optional

class MemoryNode:
    def __init__(self, 
                 node_id: str,
                 created_time: datetime,
                 memory_type: str,
                 description: str,
                 embedding: List[float],
                 emotional_intensity: float = 0.3,
                 keywords: List[str] = None,
                 expiration: datetime = None):
        self.node_id = node_id
        self.created_time = created_time
        self.expiration = expiration
        self.memory_type = memory_type
        self.description = description
        self.embedding = embedding
        self.emotional_intensity = emotional_intensity if emotional_intensity is not None else 0.3
        self.keywords = keywords if keywords is not None else []
        
    def __str__(self):
        return f"[{self.created_time.strftime('%Y-%m-%d %H:%M')}] {self.description}"
        
    def to_dict(self):
        return {
            'id': self.node_id,
            'created_time': self.created_time.isoformat(),
            'expiration': self.expiration.isoformat() if self.expiration else None,
            'type': self.memory_type,
            'description': self.description,
            'emotional_intensity': self.emotional_intensity,
            'keywords': self.keywords
        } 