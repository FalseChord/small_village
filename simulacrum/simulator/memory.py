import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict
import json
import os
import hashlib
import math
from .embedding import EmbeddingInterface
from .memory_node import MemoryNode

class Memory:
    def __init__(self, embedding_interface: EmbeddingInterface):
        self.embedding_interface = embedding_interface
        self.memories = []

        # 艾賓浩斯遺忘曲線參數
        self.forgetting_curve_params = {
            'episodic': {'decay_rate': 0.1, 'retention_rate': 0.8},  # 情節記憶衰減較快
            'semantic': {'decay_rate': 0.05, 'retention_rate': 0.9},  # 語意記憶衰減較慢
            'emotional': {'decay_rate': 0.15, 'retention_rate': 0.7}  # 情緒記憶衰減最快但保留率較低
        }

    def add_memory(
        self,
        created_time: datetime,
        memory_type: str,
        description: str,
        keywords: List[str],
        emotional_intensity: float = 0.3,
        extra_fields: Dict = None
    ):
        """添加記憶

        Args:
            created_time: 記憶創建時間
            memory_type: 記憶類型
            description: 記憶描述
            keywords: 關鍵字列表
            emotional_intensity: 情緒強度 (0.0-1.0)，整合了重要性和記憶強度
            extra_fields: 額外字段字典
        """
        # 生成記憶 ID
        memory_id = hashlib.md5(f"{description}{keywords}".encode()).hexdigest()

        # 創建記憶節點
        memory_node = {
            'id': memory_id,
            'created_time': created_time,
            'type': memory_type,
            'description': description,
            'keywords': keywords,
            'emotional_intensity': emotional_intensity,
            'embedding': self.embedding_interface.get_embedding(description)
        }

        # 添加額外字段
        if extra_fields:
            memory_node.update(extra_fields)

        self.memories.append(memory_node)
        return memory_node

    def load_memories_from_json_file(self, json_file_path: str):
        """從 JSON 檔案載入記憶

        Args:
            json_file_path: JSON 檔案路徑，例如 'data/李承翰_memories_line_by_line.json'
        """
        if not os.path.exists(json_file_path):
            print(f"記憶檔案不存在: {json_file_path}")
            return

        try:
            print(f"📁 開始讀取檔案: {json_file_path}")
            # 載入記憶數據
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 檢查檔案格式
            if 'memories' not in data:
                print(f"檔案格式錯誤，缺少 'memories' 欄位: {json_file_path}")
                return

            memories_data = data['memories']
            persona_name = data.get('persona_name', 'unknown')

            print(f"📊 檔案資訊: {persona_name}, 共 {len(memories_data)} 筆記憶")
            print(f"🔄 開始處理記憶...")

            # 將記憶數據轉換為記憶節點
            processed_count = 0
            error_count = 0

            for i, memory_item in enumerate(memories_data):
                try:
                    # 每處理 10 筆記憶顯示進度
                    if (i + 1) % 10 == 0 or i == 0:
                        print(f"⏳ 處理進度: {i + 1}/{len(memories_data)} ({((i + 1) / len(memories_data) * 100):.1f}%)")

                    # 生成記憶 ID
                    memory_id = hashlib.md5(f"{memory_item['description']}{memory_item['keywords']}".encode()).hexdigest()

                    # 生成 embedding (這是最耗時的部分)
                    if (i + 1) % 5 == 0:  # 每 5 筆顯示一次 embedding 生成進度
                        print(f"🧠 正在生成第 {i + 1} 筆記憶的 embedding...")

                    embedding = self.embedding_interface.get_embedding(memory_item['description'])

                    memory_node = {
                        'id': memory_id,
                        'created_time': datetime.fromisoformat(memory_item['created_time']),
                        'type': memory_item['type'],
                        'description': memory_item['description'],
                        'keywords': memory_item['keywords'],
                        'emotional_intensity': memory_item.get('emotional_intensity', 0.3),
                        'embedding': embedding
                    }

                    # 添加額外字段
                    if 'original_type' in memory_item:
                        memory_node['original_type'] = memory_item['original_type']
                    if 'line_number' in memory_item:
                        memory_node['line_number'] = memory_item['line_number']

                    self.memories.append(memory_node)
                    processed_count += 1

                except Exception as e:
                    print(f"❌ 載入第 {i + 1} 筆記憶時發生錯誤: {e}")
                    error_count += 1
                    continue

            print(f"✅ 記憶載入完成!")
            print(f"📈 成功載入: {processed_count} 筆")
            if error_count > 0:
                print(f"⚠️  載入失敗: {error_count} 筆")

        except Exception as e:
            print(f"❌ 載入記憶檔案失敗: {e}")


    def save_memories_to_directory(self, data_dir: str, persona_name: str = "human"):
        """保存記憶到指定目錄

        Args:
            data_dir: 資料目錄路徑
            persona_name: 角色名稱，預設為 'human'
        """
        # 新的文件結構：data_dir/persona_name/memories/
        memories_dir = os.path.join(data_dir, persona_name, "memories")
        embeddings_dir = os.path.join(data_dir, persona_name, "embeddings")

        # 確保目錄存在
        os.makedirs(memories_dir, exist_ok=True)
        os.makedirs(embeddings_dir, exist_ok=True)

        # 按日期分組記憶
        memories_by_date = {}
        embeddings_by_date = {}

        for memory in self.memories:
            date_str = memory['created_time'].strftime("%Y-%m-%d")

            if date_str not in memories_by_date:
                memories_by_date[date_str] = []
                embeddings_by_date[date_str] = {}

            # 準備記憶數據（不包含 embedding）
            memory_data = {
                'created_time': memory['created_time'].isoformat(),
                'type': memory['type'],
                'description': memory['description'],
                'keywords': memory['keywords'],
                'emotional_intensity': memory['emotional_intensity']
            }

            # 如果是對話記憶，添加對話全文和主題列表
            if memory['type'] == 'dialogue':
                if 'dialogue_content' in memory:
                    memory_data['dialogue_content'] = memory['dialogue_content']
                if 'topics' in memory:
                    memory_data['topics'] = memory['topics']

            # 生成記憶 ID
            memory_id = hashlib.md5(f"{memory['description']}{memory['keywords']}".encode()).hexdigest()
            memory_data['id'] = memory_id

            memories_by_date[date_str].append(memory_data)
            embeddings_by_date[date_str][memory_id] = memory['embedding']

        # 保存每個日期的記憶
        for date_str, memories in memories_by_date.items():
            memory_file = os.path.join(memories_dir, f"{date_str}.json")
            embedding_file = os.path.join(embeddings_dir, f"{date_str}.json")

            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(memories, f, ensure_ascii=False, indent=4)

            with open(embedding_file, 'w', encoding='utf-8') as f:
                json.dump(embeddings_by_date[date_str], f, ensure_ascii=False, indent=4)

    def get_relevant_memories(self, query: str, limit: int = 5, current_date: datetime = None) -> List[MemoryNode]:
        """檢索相關記憶（基於語義搜尋）

        Args:
            query: 查詢字符串
            limit: 返回的記憶數量限制
            current_date: 當前日期，如果為 None 則使用真實當前日期
        """
        if not self.memories:
            return []

        # 使用指定的當前日期或真實當前日期
        if current_date is None:
            current_time = datetime.now()
        else:
            current_time = current_date

        # 計算所有記憶的綜合分數
        memory_scores = []
        for node in self.memories:
            score = self._calculate_semantic_score(query, node, current_time)

            if score > 0:
                memory_scores.append((node, score))

        # 按綜合分數排序
        memory_scores.sort(key=lambda x: x[1], reverse=True)

        # 返回分數最高的記憶
        return [node for node, _ in memory_scores[:limit]]

    def _calculate_semantic_score(self, query: str, node: dict, current_time: datetime) -> float:
        """計算語義搜尋分數（基於艾賓浩斯遺忘曲線）"""
        # 獲取查詢的 embedding
        query_embedding = self.embedding_interface.get_embedding(query)

        # 計算相似度
        similarity = self.embedding_interface.compute_similarity(
            query_embedding,
            node['embedding']
        )

        # 基於艾賓浩斯遺忘曲線的時間衰減
        days_ago = (current_time.date() - node['created_time'].date()).days
        time_factor = self._calculate_ebbinghaus_decay(days_ago, node['type'])

        # 記憶強度計算（整合情緒強度）
        strength_factor = 1.0 + node['emotional_intensity']

        # 計算記憶強度加權 (越強的記憶分數越高)
        strength_factor = 1.0 + node['emotional_intensity']  # 記憶強度影響因子

        # 綜合分數：相似度 × 時間因子 × 記憶強度因子 × 類型權重
        final_score = similarity * time_factor * strength_factor

        return final_score

    def _calculate_ebbinghaus_decay(self, days_ago: int, memory_type: str) -> float:
        """基於艾賓浩斯遺忘曲線計算時間衰減因子

        Args:
            days_ago: 記憶創建距今天數
            memory_type: 記憶類型 ('episodic', 'semantic', 'emotional')
        """
        if days_ago <= 0:
            return 1.0  # 當天

        params = self.forgetting_curve_params.get(memory_type, self.forgetting_curve_params['episodic'])
        decay_rate = params['decay_rate']
        retention_rate = params['retention_rate']

        # 艾賓浩斯公式：R = retention_rate * e^(-decay_rate * days_ago)
        decay_factor = retention_rate * math.exp(-decay_rate * days_ago)

        # 確保最小值，避免完全遺忘
        return max(decay_factor, 0.01)

    def get_memories_by_timerange(self, start_time: datetime, end_time: datetime) -> List[MemoryNode]:
        """根據時間範圍檢索記憶"""
        return [
            node for node in self.memories
            if start_time <= node['created_time'] < end_time
        ]

    def get_all_memories(self) -> List[MemoryNode]:
        return self.memories

    def load_memories_from_directory(self, data_dir: str, persona_name: str = "human"):
        """從指定目錄載入記憶

        Args:
            data_dir: 資料目錄路徑，例如 'data/Case01'
            persona_name: 角色名稱，預設為 'human'
        """
        # 新的文件結構：data_dir/persona_name/memories/
        memories_dir = os.path.join(data_dir, persona_name, "memories")
        embeddings_dir = os.path.join(data_dir, persona_name, "embeddings")

        if not os.path.exists(memories_dir):
            print(f"記憶目錄不存在: {memories_dir}")
            return

        # 載入所有記憶文件
        for filename in os.listdir(memories_dir):
            if filename.endswith('.json'):
                memory_file = os.path.join(memories_dir, filename)
                embedding_file = os.path.join(embeddings_dir, filename)

                try:
                    # 載入記憶數據
                    with open(memory_file, 'r', encoding='utf-8') as f:
                        memory_data = json.load(f)

                    # 載入對應的 embedding 數據
                    embeddings_data = {}
                    if os.path.exists(embedding_file):
                        with open(embedding_file, 'r', encoding='utf-8') as f:
                            embeddings_data = json.load(f)

                    # 將記憶數據轉換為記憶節點
                    for memory_item in memory_data:
                        memory_id = memory_item.get('id', '')
                        embedding = embeddings_data.get(memory_id, [])

                        # 如果沒有 embedding，重新生成
                        if not embedding:
                            embedding = self.embedding_interface.get_embedding(memory_item['description'])

                        memory_node = {
                            'id': memory_id,
                            'created_time': datetime.fromisoformat(memory_item['created_time']),
                            'type': memory_item['type'],
                            'description': memory_item['description'],
                            'keywords': memory_item['keywords'],
                            'emotional_intensity': memory_item.get('emotional_intensity', 0.3),
                            'embedding': embedding
                        }

                        # 添加額外字段
                        if 'extra_fields' in memory_item:
                            memory_node.update(memory_item['extra_fields'])

                        self.memories.append(memory_node)

                    print(f"✅ 載入記憶檔案: {filename} ({len(memory_data)} 筆)")

                except Exception as e:
                    print(f"❌ 載入記憶檔案失敗 {filename}: {e}")

        print(f"✅ 從目錄載入記憶完成: {memories_dir}")

    def load_memories_with_cached_embeddings(self, data_dir: str, persona_name: str = "human"):
        """從指定目錄載入記憶，優先使用預先計算好的 embedding，如果沒有則回退到標準模式

        Args:
            data_dir: 資料目錄路徑，例如 'data/Case01'
            persona_name: 角色名稱，預設為 'human'
        """
        # 新的文件結構：data_dir/persona_name/memories/
        memories_dir = os.path.join(data_dir, persona_name, "memories")
        embeddings_dir = os.path.join(data_dir, persona_name, "embeddings")

        if not os.path.exists(memories_dir):
            print(f"❌ 記憶目錄不存在: {memories_dir}")
            return

        # 檢查是否有預計算的 embedding
        if not os.path.exists(embeddings_dir):
            print(f"⚠️ 沒有預計算的 embedding 目錄: {embeddings_dir}")
            print("📝 回退到標準載入模式")
            # 回退到標準載入模式
            self.load_memories_from_directory(data_dir, persona_name)
            return

        print(f"📂 從目錄載入記憶: {data_dir}/{persona_name}")

        # 載入所有記憶文件
        memory_files = [f for f in os.listdir(memories_dir) if f.endswith('.json')]
        memory_files.sort()

        total_memories = 0
        processed_memories = 0
        skipped_embeddings = 0

        for filename in memory_files:
            memory_file = os.path.join(memories_dir, filename)
            embedding_file = os.path.join(embeddings_dir, filename)

            print(f"📖 載入記憶檔案: {filename}")

            try:
                # 載入記憶數據
                with open(memory_file, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)

                # 載入對應的 embedding 數據
                with open(embedding_file, 'r', encoding='utf-8') as f:
                    embeddings_data = json.load(f)

                print(f"📊 記憶檔案包含 {len(memory_data)} 筆記憶")

                # 將記憶數據轉換為記憶節點
                for memory_item in memory_data:
                    memory_id = memory_item.get('id', '')
                    embedding = embeddings_data.get(memory_id, [])

                    # 如果沒有預計算的 embedding，跳過（避免 API 調用）
                    if not embedding:
                        print(f"⚠️ 記憶 ID {memory_id} 沒有預計算的 embedding，跳過")
                        skipped_embeddings += 1
                        continue

                    memory_node = {
                        'id': memory_id,
                        'created_time': datetime.fromisoformat(memory_item['created_time']),
                        'type': memory_item['type'],
                        'description': memory_item['description'],
                        'keywords': memory_item['keywords'],
                        'emotional_intensity': memory_item.get('emotional_intensity', 0.3),
                        'embedding': embedding  # 直接使用預計算的 embedding
                    }

                    # 添加額外字段
                    if 'original_type' in memory_item:
                        memory_node['original_type'] = memory_item['original_type']
                    if 'line_number' in memory_item:
                        memory_node['line_number'] = memory_item['line_number']

                    self.memories.append(memory_node)
                    processed_memories += 1

                total_memories += len(memory_data)

            except Exception as e:
                print(f"❌ 載入檔案 {filename} 失敗: {e}")
                continue

        print(f"✅ 成功載入 {processed_memories}/{total_memories} 筆記憶")
        print(f"📈 總記憶數量: {len(self.memories)}")
