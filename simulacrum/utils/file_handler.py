import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class FileHandler:
    def __init__(self, base_path: str = "simulacrum/data"):
        self.base_path = base_path
        self.ensure_directories()
        
    def ensure_directories(self):
        """確保所需的目錄結構存在"""
        directories = [
            "personas",
            "events",
            "memories"
        ]
        
        for dir_name in directories:
            dir_path = os.path.join(self.base_path, dir_name)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                
    def load_main_persona(self) -> Dict:
        """載入主要人格資料"""
        file_path = os.path.join(self.base_path, "personas/main_persona.json")
        return self._load_json(file_path)
        
    def load_secondary_personas(self) -> Dict:
        """載入次要人格資料"""
        file_path = os.path.join(self.base_path, "personas/secondary_personas.json")
        return self._load_json(file_path)
        
    def save_daily_events(self, date: datetime, events: List[Dict]):
        """儲存每日事件"""
        file_name = f"{date.strftime('%Y-%m-%d')}.json"
        file_path = os.path.join(self.base_path, "events", file_name)
        
        data = {
            "date": date.strftime("%Y-%m-%d"),
            "events": events
        }
        
        self._save_json(file_path, data)
        
    def save_memories(self, date: datetime, memories: List[Dict], embeddings: List[Dict]):
        """儲存記憶和對應的 embedding"""
        # 儲存人類可讀的記憶
        human_file = os.path.join(
            self.base_path,
            "memories",
            f"{date.strftime('%Y-%m-%d')}_human.json"
        )
        
        memory_data = {
            "date": date.strftime("%Y-%m-%d"),
            "memories": memories
        }
        
        self._save_json(human_file, memory_data)
        
        # 儲存 embedding
        embedding_file = os.path.join(
            self.base_path,
            "memories",
            f"{date.strftime('%Y-%m-%d')}_embedding.json"
        )
        
        embedding_data = {
            "date": date.strftime("%Y-%m-%d"),
            "embeddings": embeddings
        }
        
        self._save_json(embedding_file, embedding_data)
        
    def load_memories(self, date: datetime) -> tuple[List[Dict], List[Dict]]:
        """載入指定日期的記憶和 embedding"""
        # 載入人類可讀的記憶
        human_file = os.path.join(
            self.base_path,
            "memories",
            f"{date.strftime('%Y-%m-%d')}_human.json"
        )
        
        memories = self._load_json(human_file).get("memories", [])
        
        # 載入 embedding
        embedding_file = os.path.join(
            self.base_path,
            "memories",
            f"{date.strftime('%Y-%m-%d')}_embedding.json"
        )
        
        embeddings = self._load_json(embedding_file).get("embeddings", [])
        
        return memories, embeddings
        
    def _load_json(self, file_path: str) -> Dict:
        """載入 JSON 檔案"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"檔案不存在: {file_path}")
            return {}
        except json.JSONDecodeError:
            print(f"JSON 解析錯誤: {file_path}")
            return {}
            
    def _save_json(self, file_path: str, data: Dict):
        """儲存 JSON 檔案"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存檔案失敗 {file_path}: {str(e)}") 