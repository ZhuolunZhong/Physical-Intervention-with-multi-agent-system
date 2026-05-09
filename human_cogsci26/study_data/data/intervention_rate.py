import os
import pandas as pd

def calculate_intervention_rate_corrected():
    # 获取当前脚本所在路径
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # 定义文件夹名称
    folders = ['clean', 'pilot']
    
    # 初始化计数器
    total_random_numerator = 0
    total_random_denominator = 0
    total_smooth_numerator = 0
    total_smooth_denominator = 0
    
    for folder in folders:
        folder_path = os.path.join(base_path, folder)
        
        # 读取user_round_statistics.csv获取有效用户ID
        stats_file = os.path.join(folder_path, 'user_round_statistics.csv')
        if not os.path.exists(stats_file):
            print(f"警告: 在{folder}文件夹中未找到user_round_statistics.csv")
            continue
            
        user_stats = pd.read_csv(stats_file)
        valid_user_ids = user_stats['user_id'].tolist()
        
        # 读取user_data_action.csv
        action_file = os.path.join(folder_path, 'user_data_action.csv')
        if not os.path.exists(action_file):
            print(f"警告: 在{folder}文件夹中未找到user_data_action.csv")
            continue
            
        action_data = pd.read_csv(action_file)
        
        # 筛选有效用户的数据
        action_data = action_data[action_data['user_id'].isin(valid_user_ids)]
        
        # 按round分组
        random_rounds = [2, 3, 6, 7]
        smooth_rounds = [4, 5, 8, 9]
        
        random_data = action_data[action_data['round'].isin(random_rounds)]
        smooth_data = action_data[action_data['round'].isin(smooth_rounds)]
        
        # 计算分子：is_optimal == 0 的行数 (correction类型)
        random_numerator = len(random_data[random_data['is_optimal'] == 0])
        smooth_numerator = len(smooth_data[smooth_data['is_optimal'] == 0])
        
        # 计算分母：所有需要干预的行数 (is_optimal == 0)
        # 这里使用user_data_try.csv来获取需要干预的行
        try_file = os.path.join(folder_path, 'user_data_try.csv')
        if not os.path.exists(try_file):
            print(f"警告: 在{folder}文件夹中未找到user_data_try.csv")
            continue
            
        try_data = pd.read_csv(try_file)
        
        # 筛选有效用户的数据
        try_data = try_data[try_data['user_id'].isin(valid_user_ids)]
        
        # 筛选需要干预的行 (is_optimal == 0)
        random_intervention_needed = try_data[
            (try_data['round'].isin(random_rounds)) & 
            (try_data['is_optimal'] == 0)
        ]
        smooth_intervention_needed = try_data[
            (try_data['round'].isin(smooth_rounds)) & 
            (try_data['is_optimal'] == 0)
        ]
        
        # 累加计数
        total_random_numerator += random_numerator
        total_random_denominator += len(random_intervention_needed)
        total_smooth_numerator += smooth_numerator
        total_smooth_denominator += len(smooth_intervention_needed)
    
    # 计算combined组
    total_combined_numerator = total_random_numerator + total_smooth_numerator
    total_combined_denominator = total_random_denominator + total_smooth_denominator
    
    # 计算比例并转换为百分比
    random_rate = (total_random_numerator / total_random_denominator * 100) if total_random_denominator > 0 else 0
    smooth_rate = (total_smooth_numerator / total_smooth_denominator * 100) if total_smooth_denominator > 0 else 0
    combined_rate = (total_combined_numerator / total_combined_denominator * 100) if total_combined_denominator > 0 else 0
    
    # 输出结果
    print("修正后的干预率统计结果:")
    print(f"Random组: {random_rate:.2f}% ({total_random_numerator}/{total_random_denominator})")
    print(f"Smooth组: {smooth_rate:.2f}% ({total_smooth_numerator}/{total_smooth_denominator})")
    print(f"Combined组: {combined_rate:.2f}% ({total_combined_numerator}/{total_combined_denominator})")
    
    return {
        'random_rate': random_rate,
        'smooth_rate': smooth_rate,
        'combined_rate': combined_rate,
        'random_counts': (total_random_numerator, total_random_denominator),
        'smooth_counts': (total_smooth_numerator, total_smooth_denominator),
        'combined_counts': (total_combined_numerator, total_combined_denominator)
    }

if __name__ == "__main__":
    calculate_intervention_rate_corrected()