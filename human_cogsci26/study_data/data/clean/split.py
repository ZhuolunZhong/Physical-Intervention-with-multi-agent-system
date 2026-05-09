import pandas as pd
import os

# 获取当前py文件所在路径
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建完整的文件路径
csv_file_path = os.path.join(current_dir, 'user_data_action.csv')

# 读取CSV文件
try:
    df = pd.read_csv(csv_file_path)
    print("文件读取成功！")
except FileNotFoundError:
    print(f"错误：在路径 {current_dir} 下找不到 user_data_action.csv 文件")
    exit()

# 检查round列是否存在
if 'round' not in df.columns:
    print("错误：CSV文件中没有找到 'round' 列")
    print(f"可用的列有：{list(df.columns)}")
    exit()

# 分离数据
random_rounds = [2, 3, 6, 7]
smooth_rounds = [4, 5, 8, 9]

random_data = df[df['round'].isin(random_rounds)]
smooth_data = df[df['round'].isin(smooth_rounds)]

# 保存到新文件
random_file_path = os.path.join(current_dir, 'random.csv')
smooth_file_path = os.path.join(current_dir, 'smooth.csv')

random_data.to_csv(random_file_path, index=False)
smooth_data.to_csv(smooth_file_path, index=False)

print(f"数据分离完成！")
print(f"random.csv 已保存，包含 {len(random_data)} 行数据")
print(f"smooth.csv 已保存，包含 {len(smooth_data)} 行数据")

# 显示统计信息
print(f"\n原始数据总行数：{len(df)}")
print(f"random数据行数：{len(random_data)} (round值: {random_rounds})")
print(f"smooth数据行数：{len(smooth_data)} (round值: {smooth_rounds})")

# 检查是否有未处理的数据
other_data = df[~df['round'].isin(random_rounds + smooth_rounds)]
if len(other_data) > 0:
    print(f"\n注意：有 {len(other_data)} 行数据的round值不在2-9范围内")
    print(f"这些round值：{sorted(other_data['round'].unique())}")