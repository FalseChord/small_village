#!/usr/bin/env python3
"""
記憶模板轉換腳本

將記憶模板檔案轉換成 data/ 資料夾中的標準記憶格式，
包括 embeddings 與 memories 資料

使用方法:
    python scripts/convert_memory_template.py <template_file> <persona_name> [output_dir]

參數:
    template_file: 記憶模板檔案路徑
    persona_name: 角色名稱
    output_dir: 輸出目錄（可選，預設為 data/ 下的新目錄）
"""

import sys
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_template_file(template_file: str) -> dict:
    """載入記憶模板檔案"""
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            template_data = json.load(f)

        print(f"✅ 成功載入記憶模板: {template_file}")
        return template_data
    except FileNotFoundError:
        print(f"❌ 記憶模板檔案不存在: {template_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ 記憶模板檔案格式錯誤: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 載入記憶模板檔案時發生錯誤: {e}")
        sys.exit(1)

def validate_template_data(template_data: dict) -> bool:
    """驗證模板資料格式"""
    required_fields = ['persona_name', 'memories']

    for field in required_fields:
        if field not in template_data:
            print(f"❌ 模板缺少必要欄位: {field}")
            return False

    memories = template_data['memories']
    if not isinstance(memories, list):
        print(f"❌ memories 欄位必須是列表")
        return False

    if len(memories) == 0:
        print(f"❌ memories 列表不能為空")
        return False

    # 驗證每個記憶項目
    for i, memory in enumerate(memories):
        required_memory_fields = ['type', 'description', 'keywords', 'created_time']
        for field in required_memory_fields:
            if field not in memory:
                print(f"❌ 記憶項目 {i} 缺少必要欄位: {field}")
                return False

        # 驗證 emotional_intensity（可選）
        if 'emotional_intensity' in memory:
            intensity = memory['emotional_intensity']
            if not isinstance(intensity, (int, float)) or not (0.0 <= intensity <= 1.0):
                print(f"❌ 記憶項目 {i} 的 emotional_intensity 必須是 0.0-1.0 之間的數值")
                return False

    print(f"✅ 模板資料格式驗證通過")
    return True

def generate_embedding(description: str) -> list:
    """生成記憶描述的向量表示（模擬）"""
    # 這裡使用模擬的 embedding，實際使用時可以替換為真實的 embedding 模型
    # 生成一個基於描述的簡單向量
    seed = hash(description) % 10000
    import random
    random.seed(seed)

    # 生成 384 維的向量（常見的 embedding 維度）
    embedding = [random.uniform(-1.0, 1.0) for _ in range(384)]
    return embedding

def convert_memories_to_standard_format(template_data: dict, persona_name: str) -> tuple:
    """將模板記憶轉換成標準格式"""
    memories_by_date = {}
    embeddings_by_date = {}

    memories = template_data['memories']
    print(f"開始轉換 {len(memories)} 個記憶...")

    for i, memory_item in enumerate(memories):
        try:
            # 解析創建時間
            created_time = datetime.fromisoformat(memory_item['created_time'])
            date_str = created_time.strftime("%Y-%m-%d")

            # 生成 embedding
            embedding = generate_embedding(memory_item['description'])

            # 準備記憶數據（不包含 embedding）
            memory_data = {
                'created_time': memory_item['created_time'],
                'type': memory_item['type'],
                'description': memory_item['description'],
                'keywords': memory_item['keywords'],
                'emotional_intensity': memory_item.get('emotional_intensity', 0.3)
            }

            # 如果是對話記憶，添加對話全文和主題列表
            if memory_item['type'] == 'dialogue':
                if 'dialogue_content' in memory_item:
                    memory_data['dialogue_content'] = memory_item['dialogue_content']
                if 'topics' in memory_item:
                    memory_data['topics'] = memory_item['topics']

            # 生成記憶 ID
            memory_id = hashlib.md5(f"{memory_item['description']}{memory_item['keywords']}".encode()).hexdigest()
            memory_data['id'] = memory_id

            # 按日期分組
            if date_str not in memories_by_date:
                memories_by_date[date_str] = []
                embeddings_by_date[date_str] = {}

            memories_by_date[date_str].append(memory_data)
            embeddings_by_date[date_str][memory_id] = embedding

            print(f"  ✅ 轉換記憶 {i+1}: {memory_item['description'][:50]}...")

        except Exception as e:
            print(f"  ❌ 轉換記憶項目 {i+1} 時發生錯誤: {e}")
            continue

    print(f"✅ 成功轉換 {len(memories)} 個記憶")
    return memories_by_date, embeddings_by_date

def save_memories_to_directory(memories_by_date: dict, embeddings_by_date: dict,
                             output_dir: str, persona_name: str):
    """保存記憶到指定目錄"""
    # 創建目錄結構
    memories_dir = os.path.join(output_dir, persona_name, "memories")
    embeddings_dir = os.path.join(output_dir, persona_name, "embeddings")

    os.makedirs(memories_dir, exist_ok=True)
    os.makedirs(embeddings_dir, exist_ok=True)

    print(f"保存記憶到目錄: {output_dir}")

    # 保存每個日期的記憶
    for date_str, memories in memories_by_date.items():
        memory_file = os.path.join(memories_dir, f"{date_str}.json")
        embedding_file = os.path.join(embeddings_dir, f"{date_str}.json")

        try:
            # 保存記憶數據
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(memories, f, ensure_ascii=False, indent=4)

            # 保存 embedding 數據
            with open(embedding_file, 'w', encoding='utf-8') as f:
                json.dump(embeddings_by_date[date_str], f, ensure_ascii=False, indent=4)

            print(f"  ✅ 保存 {date_str}: {len(memories)} 個記憶")

        except Exception as e:
            print(f"  ❌ 保存 {date_str} 時發生錯誤: {e}")
            continue

def create_execution_timestamp() -> str:
    """創建執行時間戳"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def main():
    """主函數"""
    if len(sys.argv) < 3:
        print("使用方法: python scripts/convert_memory_template.py <template_file> <persona_name> [output_dir]")
        print("")
        print("參數:")
        print("  template_file: 記憶模板檔案路徑")
        print("  persona_name: 角色名稱")
        print("  output_dir: 輸出目錄（可選，預設為 data/ 下的新目錄）")
        print("")
        print("範例:")
        print("  python scripts/convert_memory_template.py templates/luo_yiqing.json 羅以青")
        print("  python scripts/convert_memory_template.py templates/luo_yiqing.json 羅以青 data/custom_output")
        sys.exit(1)

    template_file = sys.argv[1]
    persona_name = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else None

    print("=== 記憶模板轉換腳本 ===")
    print(f"模板檔案: {template_file}")
    print(f"角色名稱: {persona_name}")

    # 1. 載入模板檔案
    template_data = load_template_file(template_file)

    # 2. 驗證模板資料
    if not validate_template_data(template_data):
        sys.exit(1)

    # 3. 檢查角色名稱是否匹配
    template_persona_name = template_data.get('persona_name', '')
    if template_persona_name and template_persona_name != persona_name:
        print(f"⚠️  警告: 模板中的角色名稱 '{template_persona_name}' 與指定的角色名稱 '{persona_name}' 不符")
        response = input("是否繼續？(y/N): ")
        if response.lower() != 'y':
            print("轉換已取消")
            sys.exit(0)

    # 4. 設定輸出目錄
    if output_dir is None:
        # 預設輸出到 data/ 下的新目錄
        base_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        execution_timestamp = create_execution_timestamp()
        output_dir = os.path.join(base_data_dir, execution_timestamp)
        print(f"輸出目錄: {output_dir} (自動生成)")
    else:
        print(f"輸出目錄: {output_dir}")

    # 5. 轉換記憶格式
    memories_by_date, embeddings_by_date = convert_memories_to_standard_format(template_data, persona_name)

    # 6. 保存到目錄
    save_memories_to_directory(memories_by_date, embeddings_by_date, output_dir, persona_name)

    print("")
    print("=== 轉換完成 ===")
    print(f"✅ 成功將記憶模板轉換為標準格式")
    print(f"📁 輸出目錄: {output_dir}")
    print(f"👤 角色: {persona_name}")
    print(f"📅 記憶日期: {list(memories_by_date.keys())}")
    print(f"🔢 總記憶數: {sum(len(memories) for memories in memories_by_date.values())}")
    print("")
    print("現在您可以在模擬器中使用這個目錄來載入角色的記憶了！")

if __name__ == "__main__":
    main()
