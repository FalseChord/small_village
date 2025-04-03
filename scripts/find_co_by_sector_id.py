import csv

def find_coordinates_by_sector_id(sector_id, maze_file_path, maze_width):
    coordinates = []
    
    # 讀取 sector_maze.csv
    with open(maze_file_path, 'r') as file:
        reader = csv.reader(file)
        raw_data = next(reader)  # 只讀取第一行
        
        # 將一維數據轉換為二維矩陣
        sector_maze = []
        for i in range(0, len(raw_data), maze_width):
            row = raw_data[i:i + maze_width]
            sector_maze.append(row)
            
        # 在二維矩陣中查找對應的 sector_id
        for row_idx, row in enumerate(sector_maze):
            for col_idx, value in enumerate(row):
                try:
                    value = int(value.strip())
                    if value == sector_id:
                        coordinates.append((col_idx, row_idx))
                except ValueError:
                    continue
                    
    return coordinates

# 使用示例
maze_path = "environment/frontend_server/static_dirs/assets/小鎮/matrix/maze/sector_maze.csv"
sector_id = 32165
maze_width = 140    # 從 maze_meta_info.json 中獲取

coords = find_coordinates_by_sector_id(sector_id, maze_path, maze_width)
print(f"Sector ID {sector_id} 的所有座標: {coords}")