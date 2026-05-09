#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按用户干预次数均值分组统计干预行为分类
分组标准: ≤15且>0的用户组 和 >15的用户组
"""

import os
import pandas as pd
from pathlib import Path

# ---------- 1. 定位脚本所在目录 ----------
BASE_DIR = Path(__file__).resolve().parent   # 脚本所在文件夹
CLEAN_DIR  = BASE_DIR / "clean"
PILOT_DIR  = BASE_DIR / "pilot"

# ---------- 2. 定义setting与round的对应关系 ----------
SETTINGS = {
    1: [2, 3],   # setting 1: round 2,3
    2: [4, 5],   # setting 2: round 4,5
    3: [6, 7],   # setting 3: round 6,7
    4: [8, 9]    # setting 4: round 8,9
}

# ---------- 3. 获取用户分组 ----------
def get_user_groups(folder):
    """
    根据用户干预次数均值将用户分为两组
    """
    stats_file = folder / "user_round_statistics.csv"
    if not stats_file.exists():
        raise FileNotFoundError(f"找不到文件：{stats_file}")
    
    user_stats = pd.read_csv(stats_file)
    
    # 计算每个setting的平均干预次数
    user_groups = {}
    
    for setting_num, round_cols in [(1, ['round_2', 'round_3']), 
                                  (2, ['round_4', 'round_5']),
                                  (3, ['round_6', 'round_7']), 
                                  (4, ['round_8', 'round_9'])]:
        
        # 检查必要的列是否存在
        missing_cols = [col for col in round_cols if col not in user_stats.columns]
        if missing_cols:
            print(f"警告: Setting {setting_num} 缺少列: {missing_cols}")
            user_groups[setting_num] = {'le_15': [], 'gt_15': []}
            continue
            
        # 计算两个round的平均值
        avg_values = user_stats[round_cols].mean(axis=1)
        
        # 分组用户ID
        le_15_users = user_stats.loc[(avg_values > 0) & (avg_values <= 15), 'user_id'].tolist()
        gt_15_users = user_stats.loc[avg_values > 15, 'user_id'].tolist()
        
        user_groups[setting_num] = {
            'le_15': le_15_users,
            'gt_15': gt_15_users
        }
    
    return user_groups

# ---------- 4. 按用户组统计干预行为分类 ----------
def analyze_group_intervention_categories(df_action, user_ids, group_name, setting_num, rounds):
    """
    分析指定用户组的干预行为分类
    """
    if not user_ids:
        return {
            'total_actions': 0,
            'acceleration': {'count': 0, 'rate': 0},
            'correction': {'count': 0, 'rate': 0},
            'restart': {'count': 0, 'rate': 0},
            'user_count': 0
        }
    
    # 筛选指定用户和round的数据
    filtered_data = df_action[
        (df_action['user_id'].isin(user_ids)) & 
        (df_action['round'].isin(rounds))
    ]
    
    total_actions = len(filtered_data)
    
    # 1. Acceleration (加速): is_optimal=1 且 expected_q_value=0
    acceleration = filtered_data[
        (filtered_data['is_optimal'] == 1) & 
        (filtered_data['expected_q_value'] == 0)
    ]
    acceleration_count = len(acceleration)
    acceleration_rate = (acceleration_count / total_actions * 100) if total_actions > 0 else 0
    
    # 2. Correction (纠正): is_optimal=0
    correction = filtered_data[filtered_data['is_optimal'] == 0]
    correction_count = len(correction)
    correction_rate = (correction_count / total_actions * 100) if total_actions > 0 else 0
    
    # 3. Restart (重启): is_optimal=1 且 expected_q_value≠0
    restart = filtered_data[
        (filtered_data['is_optimal'] == 1) & 
        (filtered_data['expected_q_value'] != 0)
    ]
    restart_count = len(restart)
    restart_rate = (restart_count / total_actions * 100) if total_actions > 0 else 0
    
    return {
        'total_actions': total_actions,
        'acceleration': {'count': acceleration_count, 'rate': acceleration_rate},
        'correction': {'count': correction_count, 'rate': correction_rate},
        'restart': {'count': restart_count, 'rate': restart_rate},
        'user_count': len(user_ids)
    }

def process_all_groups_categories():
    """
    处理所有组的干预行为分类数据
    """
    results = {}
    
    # 获取clean组用户分组
    clean_user_groups = get_user_groups(CLEAN_DIR)
    
    # 获取pilot组用户分组
    pilot_user_groups = get_user_groups(PILOT_DIR)
    
    # 读取clean组数据
    clean_action_file = CLEAN_DIR / "user_data_action.csv"
    clean_action_data = pd.read_csv(clean_action_file)
    
    # 读取pilot组数据
    pilot_action_file = PILOT_DIR / "user_data_action.csv"
    pilot_action_data = pd.read_csv(pilot_action_file)
    
    for setting_num, rounds in SETTINGS.items():
        setting_results = {}
        
        # 统计≤15且>0用户组
        le_15_users = (clean_user_groups[setting_num]['le_15'] + 
                       pilot_user_groups[setting_num]['le_15'])
        
        le_15_result = analyze_group_intervention_categories(
            pd.concat([clean_action_data, pilot_action_data]),
            le_15_users, "≤15", setting_num, rounds
        )
        
        # 统计>15用户组
        gt_15_users = (clean_user_groups[setting_num]['gt_15'] + 
                       pilot_user_groups[setting_num]['gt_15'])
        
        gt_15_result = analyze_group_intervention_categories(
            pd.concat([clean_action_data, pilot_action_data]),
            gt_15_users, ">15", setting_num, rounds
        )
        
        setting_results['le_15'] = le_15_result
        setting_results['gt_15'] = gt_15_result
        results[setting_num] = setting_results
    
    return results

# ---------- 5. 主执行逻辑 ----------
def main_intervention_categories():
    try:
        # 检查目录是否存在
        if not CLEAN_DIR.exists():
            raise FileNotFoundError(f"clean 目录不存在: {CLEAN_DIR}")
        if not PILOT_DIR.exists():
            raise FileNotFoundError(f"pilot 目录不存在: {PILOT_DIR}")
        
        results = process_all_groups_categories()
        
        # ---------- 打印结果 ----------
        print("\n" + "="*80)
        print("按用户干预次数均值分组的干预行为分类统计结果")
        print("="*80)
        
        for setting_num in sorted(results.keys()):
            setting_result = results[setting_num]
            rounds = SETTINGS[setting_num]
            
            print(f"\nSetting {setting_num} (rounds {rounds}):")
            print("-" * 60)
            
            # ≤15且>0用户组
            le_15 = setting_result['le_15']
            print(f"干预次数均值 ≤15 且 >0 的用户组 (用户数: {le_15['user_count']}):")
            print(f"  总行为数: {le_15['total_actions']}")
            print(f"  Acceleration (加速): {le_15['acceleration']['rate']:.2f}% ({le_15['acceleration']['count']})")
            print(f"  Correction (纠正): {le_15['correction']['rate']:.2f}% ({le_15['correction']['count']})")
            print(f"  Restart (重启): {le_15['restart']['rate']:.2f}% ({le_15['restart']['count']})")
            
            # >15用户组
            gt_15 = setting_result['gt_15']
            print(f"\n干预次数均值 >15 的用户组 (用户数: {gt_15['user_count']}):")
            print(f"  总行为数: {gt_15['total_actions']}")
            print(f"  Acceleration (加速): {gt_15['acceleration']['rate']:.2f}% ({gt_15['acceleration']['count']})")
            print(f"  Correction (纠正): {gt_15['correction']['rate']:.2f}% ({gt_15['correction']['count']})")
            print(f"  Restart (重启): {gt_15['restart']['rate']:.2f}% ({gt_15['restart']['count']})")
            
            # 总计
            total_actions = le_15['total_actions'] + gt_15['total_actions']
            total_acceleration = le_15['acceleration']['count'] + gt_15['acceleration']['count']
            total_correction = le_15['correction']['count'] + gt_15['correction']['count']
            total_restart = le_15['restart']['count'] + gt_15['restart']['count']
            
            acceleration_rate = (total_acceleration / total_actions * 100) if total_actions > 0 else 0
            correction_rate = (total_correction / total_actions * 100) if total_actions > 0 else 0
            restart_rate = (total_restart / total_actions * 100) if total_actions > 0 else 0
            
            print(f"\n总计 (总用户数: {le_15['user_count'] + gt_15['user_count']}):")
            print(f"  总行为数: {total_actions}")
            print(f"  Acceleration (加速): {acceleration_rate:.2f}% ({total_acceleration})")
            print(f"  Correction (纠正): {correction_rate:.2f}% ({total_correction})")
            print(f"  Restart (重启): {restart_rate:.2f}% ({total_restart})")
            print("=" * 60)
        
    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main_intervention_categories()