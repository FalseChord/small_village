from simulator.simulator import Simulator
from gpt.interface import GPTInterface
from simulator.embedding import EmbeddingInterface
from simulator.persona import Persona
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime

def load_env_file():
    """載入 .env 檔案中的環境變數"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value.strip()
            print("✓ 已從 .env 檔案載入環境變數")
        except Exception as e:
            print(f"讀取 .env 檔案失敗: {e}")

def load_personas_data():
    """載入人格設定資料"""
    try:
        # 使用絕對路徑，確保從任何目錄都能正確執行
        current_dir = Path(__file__).parent
        file_path = current_dir / "data" / "personas" / "personas.json"
        with open(file_path, 'r', encoding='utf-8') as f:
            personas_data = json.load(f)
            
        return personas_data
    except Exception as e:
        print(f"載入人格資料失敗: {str(e)}")
        return {}


def initialize_personas(gpt_interface, embedding_interface):
    """初始化所有人格"""
    # 載入所有人格資料
    personas_data = load_personas_data()
    
    # 統一初始化所有人格
    personas = {}
    for name, persona_data in personas_data.items():
        personas[name] = Persona(
            persona_data=persona_data,
            embedding_interface=embedding_interface,
            gpt_interface=gpt_interface
        )
    
    return personas

def get_startup_option():
    """獲取啟動選項"""
    print("🚀 Simulacrum 啟動選項")
    print("1. 選擇 data 內的資料夾，載入記憶檔案")
    print("2. 載入初始化記憶檔案")
    print("3. 不載入任何記憶檔案")
    
    while True:
        try:
            choice = input("請選擇選項 (1-3): ").strip()
            if choice in ['1', '2', '3']:
                return int(choice)
            else:
                print("無效選項，請輸入 1、2 或 3")
        except KeyboardInterrupt:
            print("\n程式中斷")
            return None

def list_data_folders():
    """列出 data 目錄中的資料夾"""
    current_dir = Path(__file__).parent
    data_dir = current_dir / "data"
    
    if not data_dir.exists():
        print("❌ data 目錄不存在")
        return []
    
    valid_folders = []
    for folder in data_dir.iterdir():
        if folder.is_dir() and not folder.name.startswith('.') and folder.name != 'personas':
            # 檢查是否有記憶檔案（至少一個人格有 memories 目錄）
            has_memories = False
            for persona_dir in folder.iterdir():
                if persona_dir.is_dir() and (persona_dir / "memories").exists():
                    memories_dir = persona_dir / "memories"
                    if any(memories_dir.glob("*.json")):
                        has_memories = True
                        break
            
            if has_memories:
                valid_folders.append(folder)
    
    valid_folders.sort(key=lambda x: x.name, reverse=True)  # 最新的在前面
    return valid_folders

def select_data_folder():
    """選擇要載入的資料夾"""
    folders = list_data_folders()
    
    if not folders:
        print("❌ 找不到任何資料夾")
        return None
    
    print("\n可用的資料夾：")
    for folder in folders:
        print(f"  {folder.name}")
    
    while True:
        try:
            choice = input("\n請輸入資料夾名稱（或按 Enter 取消）: ").strip()
            if not choice:
                return None
            
            # 查找匹配的資料夾
            current_dir = Path(__file__).parent
            selected_folder = current_dir / "data" / choice
            
            if selected_folder.exists() and selected_folder.is_dir():
                return selected_folder
            else:
                print(f"❌ 資料夾 '{choice}' 不存在，請重新輸入")
        except KeyboardInterrupt:
            print("\n程式中斷")
            return None

def load_memories_from_folder(personas, folder_path):
    """從選定的資料夾載入記憶和embedding"""
    print(f"📂 載入資料夾: {folder_path.name}")
    
    for persona_name, persona in personas.items():
        persona_memory_dir = folder_path / persona_name / "memories"
        persona_embedding_dir = folder_path / persona_name / "embeddings"
        
        if persona_memory_dir.exists():
            print(f"  正在載入 {persona_name} 的記憶...")
            
            # 先載入所有 embedding
            embeddings_cache = {}
            if persona_embedding_dir.exists():
                for embedding_file in persona_embedding_dir.glob("*.json"):
                    try:
                        with open(embedding_file, 'r', encoding='utf-8') as f:
                            daily_embeddings = json.load(f)
                            embeddings_cache.update(daily_embeddings)
                    except Exception as e:
                        print(f"    ⚠️  載入 embedding {embedding_file.name} 失敗: {e}")
            
            # 載入記憶並配對 embedding
            for memory_file in persona_memory_dir.glob("*.json"):
                try:
                    with open(memory_file, 'r', encoding='utf-8') as f:
                        daily_memories = json.load(f)
                    
                    for memory_data in daily_memories:
                        # 獲取對應的 embedding
                        memory_id = memory_data.get('id')
                        embedding = embeddings_cache.get(memory_id) if memory_id else None
                        
                        # 直接加入到記憶列表（不重新計算 embedding）
                        memory_node = {
                            'created_time': datetime.fromisoformat(memory_data['created_time']),
                            'type': memory_data['type'],
                            'description': memory_data['description'],
                            'keywords': memory_data['keywords'],
                            'emotional_intensity': memory_data['emotional_intensity']
                        }
                        
                        if embedding:
                            memory_node['embedding'] = embedding
                        
                        persona.memory.memories.append(memory_node)
                        
                except Exception as e:
                    print(f"    ⚠️  載入 {memory_file.name} 失敗: {e}")
            
            print(f"  ✓ {persona_name} 記憶載入完成")

def load_initial_memories(personas, data_dir=None):
    """載入初始化記憶檔案"""
    current_dir = Path(__file__).parent
    
    memory_files = {
        "李承翰": current_dir / "data" / "李承翰_memories_line_by_line.json",
        "羅以青": current_dir / "data" / "羅以青_memories_line_by_line.json"
    }
    
    for persona_name, memory_file in memory_files.items():
        if persona_name in personas and memory_file.exists():
            print(f"📝 載入 {persona_name} 的初始記憶...")
            try:
                with open(memory_file, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
                
                for memory in memory_data['memories']:
                    personas[persona_name].memory.add_memory(
                        created_time=datetime.fromisoformat(memory['created_time']),
                        memory_type=memory['type'],
                        description=memory['description'],
                        keywords=memory['keywords'],
                        emotional_intensity=memory['emotional_intensity']
                    )
                
                print(f"  ✓ {persona_name} 初始記憶載入完成 ({len(memory_data['memories'])} 筆)")
            except Exception as e:
                print(f"  ❌ 載入 {persona_name} 記憶失敗: {e}")
    
    # 立即保存載入的記憶到輸出資料夾
    if data_dir:
        print(f"\n💾 將載入的記憶保存到 {data_dir}")
        save_loaded_memories(personas, data_dir)

def save_loaded_memories(personas, data_dir):
    """保存載入的記憶到輸出資料夾"""
    
    for persona_name, persona in personas.items():
        if not persona.memory.memories:
            continue
        
        print(f"  📝 保存 {persona_name} 的記憶...")
        print(f" data_dir: {data_dir}")
        
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
            persona_memory_dir = os.path.join(data_dir, persona_name, "memories")
            persona_embedding_dir = os.path.join(data_dir, persona_name, "embeddings")
            
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
            
            print(f"    ✅ {persona_name} {date_str} ({len(memory_nodes)} 筆記憶)")

def main():
    # 載入 .env 檔案
    load_env_file()
    
    # 獲取 API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 未找到 OpenAI API key")
        print("請運行 python set_api_key.py 來設置 API key")
        return

    print("✓ 成功載入 OpenAI API key")

    # 初始化 GPT 與 embedding 介面
    gpt_interface = GPTInterface(api_key)
    embedding_interface = EmbeddingInterface(api_key)
    
    # 初始化所有人格
    personas = initialize_personas(gpt_interface, embedding_interface)
    
    # 初始化模擬器
    simulator = Simulator(
        personas=personas,
        gpt_interface=gpt_interface,
        embedding_interface=embedding_interface
    )
    
    # 獲取啟動選項並載入記憶
    startup_option = get_startup_option()
    if startup_option is None:
        return
    
    if startup_option == 1:
        # 選擇資料夾載入記憶
        selected_folder = select_data_folder()
        if selected_folder:
            load_memories_from_folder(personas, selected_folder)
        else:
            print("❌ 未選擇資料夾，程式終止")
            return
    elif startup_option == 2:
        # 載入初始化記憶檔案
        load_initial_memories(personas, simulator.data_dir)
    else:
        # 選項 3：不載入任何記憶
        print("🆕 以空白記憶開始模擬")
    
    # 模擬一週的生活
    for day in range(2):
        print(f"\n=== Day {simulator.current_date.strftime('%Y-%m-%d')} ===")
        
        # 推進一天並獲取事件
        daily_events = simulator.step_day()

if __name__ == "__main__":
    main() 