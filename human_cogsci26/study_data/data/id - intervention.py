#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计 clean 与 pilot 两组 user_round_statistics.csv 中
每个setting里两个round的平均值分布
"""

import os
import pandas as pd
from pathlib import Path

# ---------- 1. 定位脚本所在目录 ----------
BASE_DIR = Path(__file__).resolve().parent   # 脚本所在文件夹
CLEAN_DIR  = BASE_DIR / "clean"
PILOT_DIR  = BASE_DIR / "pilot"

CSV_NAME = "user_round_statistics.csv"

# ---------- 2. 定义setting与round的对应关系 ----------
SETTINGS = {
    1: ['round_2', 'round_3'],
    2: ['round_4', 'round_5'], 
    3: ['round_6', 'round_7'],
    4: ['round_8', 'round_9']
}

# ---------- 3. 单组统计函数 ----------
def analyze_settings(df, group_name):
    """
    分析指定数据框中每个setting的分布
    返回每个setting的统计结果字典
    """
    results = {}
    
    for setting_num, round_cols in SETTINGS.items():
        # 检查必要的列是否存在
        missing_cols = [col for col in round_cols if col not in df.columns]
        if missing_cols:
            print(f"警告: {group_name} 组 Setting {setting_num} 缺少列: {missing_cols}")
            results[setting_num] = {'le_15': 0, 'gt_15': 0, 'total': 0}
            continue
            
        # 计算两个round的平均值
        avg_values = df[round_cols].mean(axis=1)
        
        # 统计符合条件的用户数量
        count_le_15 = ((avg_values > 0) & (avg_values <= 15)).sum()
        count_gt_15 = (avg_values > 15).sum()
        total_users = len(avg_values)
        
        results[setting_num] = {
            'le_15': count_le_15,
            'gt_15': count_gt_15,
            'total': total_users
        }
    
    return results

def process_group(folder, group_name):
    """
    处理单个组的数据
    """
    csv_path = folder / CSV_NAME
    if not csv_path.exists():
        raise FileNotFoundError(f"找不到文件：{csv_path}")

    df = pd.read_csv(csv_path)
    print(f"\n{group_name} 组数据: 共 {len(df)} 行")
    print(f"列名: {list(df.columns)}")
    
    return analyze_settings(df, group_name)

# ---------- 4. 主执行逻辑 ----------
def main():
    try:
        # 检查目录是否存在
        if not CLEAN_DIR.exists():
            print(f"警告: clean 目录不存在: {CLEAN_DIR}")
            clean_results = None
        else:
            clean_results = process_group(CLEAN_DIR, "Clean")
            
        if not PILOT_DIR.exists():
            print(f"警告: pilot 目录不存在: {PILOT_DIR}")
            pilot_results = None
        else:
            pilot_results = process_group(PILOT_DIR, "Pilot")
        
        # ---------- 5. 打印结果 ----------
        print("\n" + "="*50)
        
        # 打印clean组结果
        if clean_results:
            print("\nClean 组统计：")
            for setting_num in sorted(clean_results.keys()):
                counts = clean_results[setting_num]
                print(f"Setting {setting_num}:")
                print(f"  平均值 ≤ 15 且 > 0 的用户数: {counts['le_15']}")
                print(f"  平均值 > 15 的用户数: {counts['gt_15']}")
                print(f"  总用户数: {counts['total']}")
        
        # 打印pilot组结果
        if pilot_results:
            print("\nPilot 组统计：")
            for setting_num in sorted(pilot_results.keys()):
                counts = pilot_results[setting_num]
                print(f"Setting {setting_num}:")
                print(f"  平均值 ≤ 15 且 > 0 的用户数: {counts['le_15']}")
                print(f"  平均值 > 15 的用户数: {counts['gt_15']}")
                print(f"  总用户数: {counts['total']}")
        
        # 打印合并统计结果
        if clean_results and pilot_results:
            print("\n合并统计：")
            for setting_num in sorted(clean_results.keys()):
                clean_counts = clean_results[setting_num]
                pilot_counts = pilot_results[setting_num]
                
                total_le_15 = clean_counts['le_15'] + pilot_counts['le_15']
                total_gt_15 = clean_counts['gt_15'] + pilot_counts['gt_15']
                total_users = clean_counts['total'] + pilot_counts['total']
                
                print(f"Setting {setting_num} 总计:")
                print(f"  平均值 ≤ 15 且 > 0 的用户数: {total_le_15}")
                print(f"  平均值 > 15 的用户数: {total_gt_15}")
                print(f"  总用户数: {total_users}")
        
    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()