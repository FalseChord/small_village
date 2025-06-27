from datetime import datetime
from typing import List, Optional

class MemoryNode:
    def __init__(self, 
                 node_id: str,
                 created_time: datetime,
                 expiration: datetime,
                 memory_type: str,
                 description: str,
                 embedding: List[float],
                 poignancy: float,
                 keywords: List[str]):
        self.node_id = node_id
        self.created_time = created_time
        self.expiration = expiration
        self.memory_type = memory_type
        self.description = description
        self.embedding = embedding
        self.poignancy = poignancy
        self.keywords = keywords
        
    def __str__(self):
        return f"[{self.created_time.strftime('%Y-%m-%d %H:%M')}] {self.description}"
        
    def to_dict(self):
        return {
            'id': self.node_id,
            'created_time': self.created_time.isoformat(),
            'expiration': self.expiration.isoformat() if self.expiration else None,
            'type': self.memory_type,
            'description': self.description,
            'poignancy': self.poignancy,
            'keywords': self.keywords
        } 