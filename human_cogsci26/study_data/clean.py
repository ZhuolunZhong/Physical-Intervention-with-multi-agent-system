import os
import pandas as pd
import shutil

def clean_data_files():
    # 获取当前py文件所在路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 创建clean文件夹（如果不存在）
    clean_dir = os.path.join(current_dir, 'clean')
    if not os.path.exists(clean_dir):
        os.makedirs(clean_dir)
    
    # 读取user_round_statistics.csv文件中的user_id
    stats_file = os.path.join(current_dir, 'user_round_statistics.csv')
    try:
        stats_df = pd.read_csv(stats_file)
        valid_user_ids = set(stats_df['user_id'].astype(str).unique())
        print(f"找到 {len(valid_user_ids)} 个有效的user_id")
    except FileNotFoundError:
        print(f"错误：找不到文件 {stats_file}")
        return
    except KeyError:
        print(f"错误：{stats_file} 中没有找到 'user_id' 列")
        return
    
    # 需要处理的数据文件列表
    data_files = [
        'user_data_q.csv',
        'user_data.csv',
        'user_data_action.csv',
        'user_data_end_counts.csv',
        'user_data_try.csv'
    ]
    
    # 处理每个数据文件
    for file_name in data_files:
        file_path = os.path.join(current_dir, file_name)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"警告：文件 {file_name} 不存在，跳过处理")
            continue
        
        try:
            # 读取数据文件
            print(f"正在处理文件: {file_name}")
            df = pd.read_csv(file_path)
            
            # 检查是否有user_id列
            if 'user_id' not in df.columns:
                print(f"警告：{file_name} 中没有 'user_id' 列，跳过处理")
                continue
            
            # 筛选数据：只保留user_id在有效列表中的行
            # 将user_id转换为字符串进行比较，确保类型一致
            df['user_id_str'] = df['user_id'].astype(str)
            filtered_df = df[df['user_id_str'].isin(valid_user_ids)].copy()
            filtered_df.drop('user_id_str', axis=1, inplace=True)
            
            # 保存筛选后的数据到clean文件夹
            output_path = os.path.join(clean_dir, file_name)
            filtered_df.to_csv(output_path, index=False)
            
            print(f"已保存筛选后的数据: {file_name} (原始行数: {len(df)}, 筛选后行数: {len(filtered_df)})")
            
        except Exception as e:
            print(f"处理文件 {file_name} 时出错: {str(e)}")
    
    print("数据处理完成！")

if __name__ == "__main__":
    clean_data_files()