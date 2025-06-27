import openai
import numpy as np
from typing import List, Tuple

class EmbeddingInterface:
    def __init__(self, api_key: str):
        openai.api_key = api_key
        
    def get_embedding(self, text: str) -> List[float]:
        """獲取文本的 embedding"""
        try:
            response = openai.Embedding.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response['data'][0]['embedding']
        except Exception as e:
            print(f"獲取 embedding 失敗: {str(e)}")
            # 返回零向量作為後備
            return [0.0] * 1536  # text-embedding-ada-002 的維度是 1536
            
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """計算兩個 embedding 的餘弦相似度"""
        if not embedding1 or not embedding2:
            return 0.0
            
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return np.dot(vec1, vec2) / (norm1 * norm2) 