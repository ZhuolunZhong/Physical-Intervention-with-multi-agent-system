import os
import pandas as pd

def calculate_intervention_categories():
    # 获取当前脚本所在路径
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # 定义文件夹名称
    folders = ['clean', 'pilot']
    
    # 初始化计数器
    total_random_denominator = 0
    total_random_acceleration = 0
    total_random_correction = 0
    total_random_restart = 0
    
    total_smooth_denominator = 0
    total_smooth_acceleration = 0
    total_smooth_correction = 0
    total_smooth_restart = 0
    
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
        
        # 对random组进行分类计数
        total_random_denominator += len(random_data)
        
        # 1. acceleration: is_optimal=1 且 expected_q_value=0
        random_acceleration = random_data[
            (random_data['is_optimal'] == 1) & 
            (random_data['expected_q_value'] == 0)
        ]
        total_random_acceleration += len(random_acceleration)
        
        # 2. correction: is_optimal=0
        random_correction = random_data[random_data['is_optimal'] == 0]
        total_random_correction += len(random_correction)
        
        # 3. restart: is_optimal=1 且 expected_q_value≠0
        random_restart = random_data[
            (random_data['is_optimal'] == 1) & 
            (random_data['expected_q_value'] != 0)
        ]
        total_random_restart += len(random_restart)
        
        # 对smooth组进行分类计数
        total_smooth_denominator += len(smooth_data)
        
        # 1. acceleration: is_optimal=1 且 expected_q_value=0
        smooth_acceleration = smooth_data[
            (smooth_data['is_optimal'] == 1) & 
            (smooth_data['expected_q_value'] == 0)
        ]
        total_smooth_acceleration += len(smooth_acceleration)
        
        # 2. correction: is_optimal=0
        smooth_correction = smooth_data[smooth_data['is_optimal'] == 0]
        total_smooth_correction += len(smooth_correction)
        
        # 3. restart: is_optimal=1 且 expected_q_value≠0
        smooth_restart = smooth_data[
            (smooth_data['is_optimal'] == 1) & 
            (smooth_data['expected_q_value'] != 0)
        ]
        total_smooth_restart += len(smooth_restart)
    
    # 计算combined组
    total_combined_denominator = total_random_denominator + total_smooth_denominator
    total_combined_acceleration = total_random_acceleration + total_smooth_acceleration
    total_combined_correction = total_random_correction + total_smooth_correction
    total_combined_restart = total_random_restart + total_smooth_restart
    
    # 计算各组的百分比
    def calculate_rates(numerator, denominator):
        if denominator > 0:
            return numerator / denominator * 100
        return 0
    
    # Random组
    random_acceleration_rate = calculate_rates(total_random_acceleration, total_random_denominator)
    random_correction_rate = calculate_rates(total_random_correction, total_random_denominator)
    random_restart_rate = calculate_rates(total_random_restart, total_random_denominator)
    
    # Smooth组
    smooth_acceleration_rate = calculate_rates(total_smooth_acceleration, total_smooth_denominator)
    smooth_correction_rate = calculate_rates(total_smooth_correction, total_smooth_denominator)
    smooth_restart_rate = calculate_rates(total_smooth_restart, total_smooth_denominator)
    
    # Combined组
    combined_acceleration_rate = calculate_rates(total_combined_acceleration, total_combined_denominator)
    combined_correction_rate = calculate_rates(total_combined_correction, total_combined_denominator)
    combined_restart_rate = calculate_rates(total_combined_restart, total_combined_denominator)
    
    # 输出结果
    print("干预行为分类统计结果 (按Random/Smooth/Combined分组):")
    print("\n=== RANDOM组 ===")
    print(f"总数据行数: {total_random_denominator}")
    print(f"Acceleration (加速): {random_acceleration_rate:.2f}% ({total_random_acceleration}/{total_random_denominator})")
    print(f"Correction (纠正): {random_correction_rate:.2f}% ({total_random_correction}/{total_random_denominator})")
    print(f"Restart (重启): {random_restart_rate:.2f}% ({total_random_restart}/{total_random_denominator})")
    
    print("\n=== SMOOTH组 ===")
    print(f"总数据行数: {total_smooth_denominator}")
    print(f"Acceleration (加速): {smooth_acceleration_rate:.2f}% ({total_smooth_acceleration}/{total_smooth_denominator})")
    print(f"Correction (纠正): {smooth_correction_rate:.2f}% ({total_smooth_correction}/{total_smooth_denominator})")
    print(f"Restart (重启): {smooth_restart_rate:.2f}% ({total_smooth_restart}/{total_smooth_denominator})")
    
    print("\n=== COMBINED组 ===")
    print(f"总数据行数: {total_combined_denominator}")
    print(f"Acceleration (加速): {combined_acceleration_rate:.2f}% ({total_combined_acceleration}/{total_combined_denominator})")
    print(f"Correction (纠正): {combined_correction_rate:.2f}% ({total_combined_correction}/{total_combined_denominator})")
    print(f"Restart (重启): {combined_restart_rate:.2f}% ({total_combined_restart}/{total_combined_denominator})")
    
    # 验证分类是否完整
    def validate_categories(acceleration, correction, restart, total):
        categorized = acceleration + correction + restart
        if categorized != total:
            print(f"注意: 分类数据({categorized})与总数据({total})不匹配，差值: {total - categorized}")
    
    validate_categories(total_random_acceleration, total_random_correction, total_random_restart, total_random_denominator)
    validate_categories(total_smooth_acceleration, total_smooth_correction, total_smooth_restart, total_smooth_denominator)
    validate_categories(total_combined_acceleration, total_combined_correction, total_combined_restart, total_combined_denominator)
    
    return {
        'random': {
            'total': total_random_denominator,
            'acceleration_rate': random_acceleration_rate,
            'correction_rate': random_correction_rate,
            'restart_rate': random_restart_rate
        },
        'smooth': {
            'total': total_smooth_denominator,
            'acceleration_rate': smooth_acceleration_rate,
            'correction_rate': smooth_correction_rate,
            'restart_rate': smooth_restart_rate
        },
        'combined': {
            'total': total_combined_denominator,
            'acceleration_rate': combined_acceleration_rate,
            'correction_rate': combined_correction_rate,
            'restart_rate': combined_restart_rate
        }
    }

if __name__ == "__main__":
    calculate_intervention_categories()