import csv

def replace_object(sector_name, arena_name, old_object_name, new_object_name):
    # 讀取所有必要的檔案和建立對照表
    def read_csv_to_matrix(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return [row.strip().split(', ') for row in f.readlines()]

    # 讀取矩陣檔案
    game_object_maze = read_csv_to_matrix('environment/frontend_server/static_dirs/assets/小鎮/matrix/maze/game_object_maze.csv')
    arena_maze = read_csv_to_matrix('environment/frontend_server/static_dirs/assets/小鎮/matrix/maze/arena_maze.csv')
    sector_maze = read_csv_to_matrix('environment/frontend_server/static_dirs/assets/小鎮/matrix/maze/sector_maze.csv')

    # 建立物件ID對照表
    object_id_map = {}
    object_name_to_id = {}
    with open('environment/frontend_server/static_dirs/assets/小鎮/matrix/special_blocks/game_object_blocks.csv', 'r', encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) >= 4:
                object_id = row[0].strip()
                object_name = row[3].strip()
                object_id_map[object_id] = object_name
                object_name_to_id[object_name] = object_id

    # 建立arena ID對照表
    arena_id_map = {}
    with open('environment/frontend_server/static_dirs/assets/小鎮/matrix/special_blocks/arena_blocks.csv', 'r', encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) >= 4:
                arena_id = row[0].strip()
                curr_sector = row[2].strip()
                curr_arena = row[3].strip()
                arena_id_map[arena_id] = (curr_sector, curr_arena)

    # 取得新物件的ID
    new_object_id = object_name_to_id.get(new_object_name)
    if not new_object_id:
        raise ValueError(f"找不到物件: {new_object_name}")

    # 取得舊物件的ID
    old_object_id = object_name_to_id.get(old_object_name)
    if not old_object_id:
        raise ValueError(f"找不到物件: {old_object_name}")

    # 替換物件
    changes_made = False
    for y in range(len(game_object_maze)):
        for x in range(len(game_object_maze[y])):
            # 檢查是否在指定的sector和arena中
            curr_arena_id = arena_maze[y][x].strip()
            if curr_arena_id in arena_id_map:
                curr_sector, curr_arena = arena_id_map[curr_arena_id]
                
                # 如果找到匹配的位置和物件
                if (curr_sector == sector_name and 
                    curr_arena == arena_name and 
                    game_object_maze[y][x].strip() == old_object_id):
                    
                    # 替換物件
                    game_object_maze[y][x] = new_object_id
                    changes_made = True

    # 如果有變更，寫回檔案
    if changes_made:
        with open('environment/frontend_server/static_dirs/assets/小鎮/matrix/maze/game_object_maze.csv', 'w', encoding='utf-8') as f:
            for row in game_object_maze:
                f.write(', '.join(row) + '\n')
        print(f"已將 {sector_name} 的 {arena_name} 中的 {old_object_name} 替換為 {new_object_name}")
    else:
        print(f"在 {sector_name} 的 {arena_name} 中找不到 {old_object_name}")

# 使用範例
if __name__ == "__main__":
    # 替換羅以青的單人套房起居室中的床為書桌
    replace_object(
        sector_name="心理諮商中心",
        arena_name="庭院",
        old_object_name="宿舍花園",
        new_object_name="公佈欄"
    )
