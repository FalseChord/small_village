from simulator.simulator import Simulator
from gpt.interface import GPTInterface
from simulator.embedding import EmbeddingInterface
from simulator.persona import MainPersona, SecondaryPersona
import os
import json
from pathlib import Path

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

def load_persona_data():
    """載入主要人格設定資料"""
    try:
        # 使用絕對路徑，確保從任何目錄都能正確執行
        current_dir = Path(__file__).parent
        file_path = current_dir / "data" / "personas" / "main_persona.json"
        with open(file_path, 'r', encoding='utf-8') as f:
            persona_data = json.load(f)
            
        # 轉換資料格式以符合系統需求
        return {
            "name": persona_data["name"],
            "age": persona_data["age"],
            "innate_traits": [trait.strip() for trait in persona_data["innate"].split("、")],
            "learned_traits": persona_data["learned"],
            "current_status": persona_data["currently"],
            "lifestyle": persona_data["lifestyle"],
            "biography": persona_data["biography"],
            "relationships": persona_data.get("relationships", {})
        }
    except Exception as e:
        print(f"載入主要人格資料失敗: {str(e)}")
        return {}

def load_secondary_personas():
    """載入次要人格設定資料"""
    try:
        # 使用絕對路徑，確保從任何目錄都能正確執行
        current_dir = Path(__file__).parent
        file_path = current_dir / "data" / "personas" / "secondary_personas.json"
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            
        # 轉換資料格式
        converted_data = {}
        for name, persona in raw_data.items():
            converted_data[name] = {
                "name": persona["name"],
                "age": persona["age"],
                "innate_traits": [trait.strip() for trait in persona["innate"].split("、")],
                "learned_traits": persona["learned"],
                "current_status": persona["currently"],
                "lifestyle": persona["lifestyle"],
                "biography": persona["biography"],
                "relationship_with_main": {
                    "role": persona["relationship_with_main"]["role"],
                    "expectations": persona["relationship_with_main"]["expectations"],
                    "concerns": persona["relationship_with_main"]["concerns"],
                    "communication_style": persona["relationship_with_main"]["communication_style"]
                }
            }
        return converted_data
            
    except Exception as e:
        print(f"載入次要人格資料失敗: {str(e)}")
        return {}

def initialize_personas(gpt_interface, embedding_interface):
    """初始化所有人格"""
    # 載入主要人格
    main_persona_data = load_persona_data()
    main_persona = MainPersona(
        persona_data=main_persona_data,
        embedding_interface=embedding_interface,
        gpt_interface=gpt_interface  # 添加 GPT 介面
    )
    
    # 載入次要人格
    secondary_personas_data = load_secondary_personas()
    secondary_personas = {}
    for name, persona_data in secondary_personas_data.items():
        secondary_personas[name] = SecondaryPersona(
            persona_data=persona_data,
            embedding_interface=embedding_interface,
            gpt_interface=gpt_interface  # 添加 GPT 介面
        )
    
    return main_persona, secondary_personas

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
    main_persona, secondary_personas = initialize_personas(gpt_interface, embedding_interface)
    
    # 初始化模擬器
    simulator = Simulator(
        main_persona=main_persona,
        gpt_interface=gpt_interface,
        embedding_interface=embedding_interface,
        secondary_personas=secondary_personas
    )
    
    # 模擬一週的生活
    for day in range(60):
        print(f"\n=== Day {simulator.current_date.strftime('%Y-%m-%d')} ===")
        
        # 推進一天並獲取事件
        daily_events = simulator.step_day()

if __name__ == "__main__":
    main() 