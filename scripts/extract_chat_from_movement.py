import json
import glob
import os

def extract_chats_from_movements():
    # 找出所有 @movement 目錄下的 json 檔案
    movement_files = glob.glob("environment/frontend_server/storage/3/movement/**/*.json", recursive=True)
    chat_records = []
    
    for file_path in movement_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 如果存在 "persona" 欄位就記錄下來
                if "persona" in data:
                    for persona_name, persona_data in data["persona"].items():
                        if "chat" in persona_data and persona_data["chat"] is not None:
                            chat_records.append({
                                "file": file_path,
                                "persona": persona_name,
                                "chat": [f"{x[0]}：{x[1]}" for x in persona_data["chat"]]
                            })
                
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")
    
    return chat_records

# 執行並印出結果
chats = extract_chats_from_movements()
for record in chats:
    print(f"\nFile: {record['file']}")
    print(f"Persona: {record['persona']}")
    print("Chat content:")
    for chat in record['chat']:
        print(f"  {chat}")