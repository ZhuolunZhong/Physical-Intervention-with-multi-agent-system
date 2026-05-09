import pandas as pd
import os

# 获取当前py文件所在路径
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建完整的文件路径
csv_file_path = os.path.join(current_dir, 'user_data_action.csv')

# 读取CSV文件
df = pd.read_csv(csv_file_path)

# 检查必要的列是否存在
if 'user_id' not in df.columns or 'round' not in df.columns:
    print("错误：CSV文件中缺少'user_id'或'round'列")
else:
    # 创建完整的user_id和round组合
    user_ids = df['user_id'].unique()
    rounds = list(range(2, 10))  # round 2到9
    
    # 创建所有可能的组合
    from itertools import product
    all_combinations = pd.DataFrame(list(product(user_ids, rounds)), columns=['user_id', 'round'])
    
    # 统计实际存在的组合数量
    actual_counts = df[df['round'].between(2, 9)].groupby(['user_id', 'round']).size().reset_index(name='count')
    
    # 合并所有组合和实际计数，缺失值填充为0
    result = pd.merge(all_combinations, actual_counts, on=['user_id', 'round'], how='left')
    result['count'] = result['count'].fillna(0).astype(int)
    
    # 重塑数据，使每个user_id一行，round作为列
    pivot_result = result.pivot(index='user_id', columns='round', values='count').reset_index()
    pivot_result.columns.name = None  # 移除列名
    
    # 重命名列，使其更清晰
    column_names = ['user_id'] + [f'round_{i}' for i in range(2, 10)]
    pivot_result.columns = column_names
    
    # 保存结果到新的CSV文件
    output_file_path = os.path.join(current_dir, 'user_round_counts_detailed.csv')
    pivot_result.to_csv(output_file_path, index=False)
    
    print(f"统计完成！结果已保存到: {output_file_path}")
    print("\n统计摘要:")
    print(f"- 共统计了 {len(user_ids)} 个不同的用户")
    print(f"- round范围: 2-9")
    print(f"- 总数据行数: {len(pivot_result)}")
    
    # 显示一些统计信息
    zero_counts = (pivot_result.iloc[:, 1:] == 0).sum().sum()
    total_cells = len(pivot_result) * 8  # 8个round列
    zero_percentage = (zero_counts / total_cells) * 100
    
    print(f"- 0值单元格数量: {zero_counts} ({zero_percentage:.1f}% of all cells)")