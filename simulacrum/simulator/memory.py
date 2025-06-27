import numpy as np
from datetime import datetime, date
from typing import List, Optional, Dict
from .embedding import EmbeddingInterface
from .memory_node import MemoryNode

class Memory:
    def __init__(self, embedding_interface: EmbeddingInterface, memory_duration: int = 30):
        self.embedding_interface = embedding_interface
        self.memories = []
        self.memory_duration = memory_duration  # 預設記憶保存30天
        
    def add_memory(
        self,
        created_time: datetime,
        expiration: datetime,
        memory_type: str,
        description: str,
        keywords: List[str],
        poignancy: float,
    ):
        """添加新記憶"""
        memory_node = {
            'created_time': created_time,
            'expiration': expiration,
            'type': memory_type,
            'description': description,
            'keywords': keywords,
            'poignancy': poignancy,
            'embedding': self.embedding_interface.get_embedding(description)
        }
        
        self.memories.append(memory_node)
        return memory_node

    def get_relevant_memories(self, query: str, limit: int = 5) -> List[MemoryNode]:
        """檢索相關記憶
        
        結合相關性和時間因素來檢索記憶：
        1. 計算查詢與所有記憶的相似度
        2. 根據時間衰減調整相似度分數
        3. 返回綜合分數最高的記憶
        """
        if not self.memories:
            return []
        
        # 獲取查詢的 embedding
        query_embedding = self.embedding_interface.get_embedding(query)
        current_time = datetime.now()
        
        # 計算所有記憶的綜合分數
        memory_scores = []
        for node in self.memories:
            # 計算相似度
            similarity = self.embedding_interface.compute_similarity(
                query_embedding, 
                node['embedding']
            )
            
            # 計算時間衰減因子 (越近的記憶分數越高)
            time_diff = (current_time.date() - node['created_time']).days
            time_factor = 1.0 / (1.0 + 0.1 * time_diff)  # 簡單的衰減函數
            
            # 計算重要性加權
            importance_factor = 1.0 + node['poignancy']  # 重要的記憶更容易被記住
            
            # 綜合分數
            final_score = similarity * time_factor * importance_factor
            
            memory_scores.append((node, final_score))
        
        # 按綜合分數排序
        memory_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 返回分數最高的記憶
        return [node for node, _ in memory_scores[:limit]]

    def cleanup_expired_memories(self, current_date: date):
        """清理過期記憶"""
        self.memories = [
            node for node in self.memories
            if (current_date - node['created_time']).days <= self.memory_duration
        ]

    def get_memories_by_keyword(self, keyword: str, limit: int = 10) -> List[MemoryNode]:
        """根據關鍵字檢索記憶"""
        keyword = keyword.lower()
        return [
            node for node in self.memories
            if keyword in node['keywords']
        ][:limit]

    def get_memories_by_timerange(self, start_time: datetime, end_time: datetime) -> List[MemoryNode]:
        return [
            node for node in self.memories
            if start_time <= node['created_time'] < end_time
        ]
    
    def get_all_memories(self) -> List[MemoryNode]:
        return self.memories
