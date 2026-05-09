import os
import pandas as pd

# 获取当前py文件所在路径
current_dir = os.path.dirname(os.path.abspath(__file__))

# 读取demographics.csv中的user_id列
demographics_path = os.path.join(current_dir, 'demographics.csv')
demographics_df = pd.read_csv(demographics_path)
user_ids = demographics_df['user_id'].unique()

# 读取user_data_action.csv
user_data_path = os.path.join(current_dir, 'user_data_action.csv')
user_data_df = pd.read_csv(user_data_path)

# 筛选出user_id在demographics.csv中存在的行
filtered_data = user_data_df[user_data_df['user_id'].isin(user_ids)]

# 将数据按round值分类保存
random_rounds = [2, 3, 6, 7]
smooth_rounds = [4, 5, 8, 9]

# 筛选并保存random.csv
random_data = filtered_data[filtered_data['round'].isin(random_rounds)]
random_output_path = os.path.join(current_dir, 'random.csv')
random_data.to_csv(random_output_path, index=False)

# 筛选并保存smooth.csv
smooth_data = filtered_data[filtered_data['round'].isin(smooth_rounds)]
smooth_output_path = os.path.join(current_dir, 'smooth.csv')
smooth_data.to_csv(smooth_output_path, index=False)

print("处理完成！已生成 random.csv 和 smooth.csv")