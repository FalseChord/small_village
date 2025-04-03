import csv
import json
from collections import defaultdict

def read_csv(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [row.strip().split(', ') for row in f.readlines()]

def create_spatial_mapping():
    # 讀取所有CSV檔案
    game_object_maze = read_csv('environment/frontend_server/static_dirs/assets/小鎮/matrix/maze/game_object_maze.csv')
    arena_maze = read_csv('environment/frontend_server/static_dirs/assets/小鎮/matrix/maze/arena_maze.csv')
    sector_maze = read_csv('environment/frontend_server/static_dirs/assets/小鎮/matrix/maze/sector_maze.csv')
    
    # 讀取物件和場所定義
    game_objects = {}
    with open('environment/frontend_server/static_dirs/assets/小鎮/matrix/special_blocks/game_object_blocks.csv', 'r', encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) >= 4:
                game_objects[row[0].strip()] = row[3].strip()

    arenas = {}
    with open('environment/frontend_server/static_dirs/assets/小鎮/matrix/special_blocks/arena_blocks.csv', 'r', encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) >= 4:
                arenas[row[0].strip()] = {
                    'sector': row[2].strip(),
                    'name': row[3].strip()
                }

    # 建立映射關係
    spatial_mapping = defaultdict(lambda: defaultdict(set))
    
    # 遍歷矩陣
    for y in range(len(game_object_maze)):
        for x in range(len(game_object_maze[y])):
            obj_id = game_object_maze[y][x].strip()
            arena_id = arena_maze[y][x].strip()
            sector_id = sector_maze[y][x].strip()
            
            # 如果找到物件
            if obj_id != '0' and obj_id in game_objects:
                # 找到對應的arena
                if arena_id != '0' and arena_id in arenas:
                    sector_name = arenas[arena_id]['sector']
                    arena_name = arenas[arena_id]['name']
                    object_name = game_objects[obj_id]
                    
                    # 添加到映射中
                    spatial_mapping[sector_name][arena_name].add(object_name)

    # 轉換為一般dict並將set轉為list
    result = {}
    for sector, arenas_dict in spatial_mapping.items():
        result[sector] = {
            arena: list(objects) 
            for arena, objects in arenas_dict.items()
        }

    return result

# 執行並輸出結果
if __name__ == "__main__":
    mapping = create_spatial_mapping()
    
    # 漂亮地輸出JSON
    print(json.dumps(mapping, ensure_ascii=False, indent=2))