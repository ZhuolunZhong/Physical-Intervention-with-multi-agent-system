import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from statsmodels.nonparametric.smoothers_lowess import lowess
import os
from scipy import stats

# 设置英文样式
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

setting_titles = {
    'setting1': 'One agent Random env',
    'setting2': 'One agent Smooth env',
    'setting3': 'Two agents Random env',
    'setting4': 'Two agents Smooth env'
}

def load_and_process_data(base_path):
    """
    加载和处理所有实验数据
    """
    settings_mapping = {
        'agents_1_world2_size_8': 'setting1',
        'agents_1_world3_size_8': 'setting2', 
        'agents_2_world2_size_8': 'setting3',
        'agents_2_world3_size_8': 'setting4'
    }
    
    all_data = {}
    
    for folder_name, setting_name in settings_mapping.items():
        setting_path = base_path / folder_name
        if not setting_path.exists():
            print(f"Warning: Cannot find folder {setting_path}")
            continue
            
        print(f"Processing {setting_name} ({folder_name})...")
        setting_data = {}
        
        # 加载无干预数据
        no_int_path = setting_path / 'no_intervention'
        if no_int_path.exists():
            no_int_dfs = []
            for run_file in no_int_path.glob('run_*.csv'):
                df = pd.read_csv(run_file)
                df['run'] = int(run_file.stem.split('_')[1])
                no_int_dfs.append(df)
            
            if no_int_dfs:
                no_int_data = pd.concat(no_int_dfs, ignore_index=True)
                setting_data['no_intervention'] = no_int_data
                print(f"  Loaded no intervention data: {len(no_int_dfs)} runs")
        
        # 只加载干预率为0.25的数据
        intervention_dfs = []
        for intervention_dir in setting_path.glob('type_*_rate_0.25_mode_2'):
            for run_file in intervention_dir.glob('run_*.csv'):
                df = pd.read_csv(run_file)
                df['run'] = int(run_file.stem.split('_')[1])
                intervention_dfs.append(df)
        
        # 合并干预率为0.25的数据
        if intervention_dfs:
            intervention_data = pd.concat(intervention_dfs, ignore_index=True)
            setting_data['intervention'] = intervention_data
            print(f"  Loaded intervention rate 0.25: {len(intervention_dfs)} runs")
        
        all_data[setting_name] = setting_data
    
    return all_data

def calculate_lowess_smooth(df, x_col='step', y_col='CumulativeReward', frac=0.3):
    """计算LOWESS平滑曲线"""
    if df.empty:
        return pd.Series([], dtype=float), []
    
    # 按步数分组求均值
    grouped = df.groupby(x_col)[y_col].mean().reset_index()
    if len(grouped) < 2:
        return pd.Series([], dtype=float), []
    
    # 计算LOWESS平滑
    try:
        lowess_result = lowess(grouped[y_col], grouped[x_col], frac=frac, it=0)
        smoothed = pd.Series(lowess_result[:, 1], index=grouped[x_col])
        return smoothed, grouped[x_col].values
    except Exception as e:
        print(f"LOWESS calculation error: {e}")
        return pd.Series([], dtype=float), []

def calculate_difference_with_ci(intervention_data, baseline_data, x_col='step', y_col='CumulativeReward', confidence=0.95, n_bootstrap=1000):
    """计算干预数据与基线数据的差值及其置信区间（使用bootstrap方法）"""
    if intervention_data.empty or baseline_data.empty:
        return pd.Series([], dtype=float), pd.Series([], dtype=float), pd.Series([], dtype=float), []
    
    # 计算平滑曲线
    smoothed_int, int_steps = calculate_lowess_smooth(intervention_data, x_col, y_col)
    smoothed_base, base_steps = calculate_lowess_smooth(baseline_data, x_col, y_col)
    
    if smoothed_int.empty or smoothed_base.empty:
        return pd.Series([], dtype=float), pd.Series([], dtype=float), pd.Series([], dtype=float), []
    
    # 找到共同的步数
    common_steps = smoothed_int.index.intersection(smoothed_base.index)
    if len(common_steps) == 0:
        return pd.Series([], dtype=float), pd.Series([], dtype=float), pd.Series([], dtype=float), []
    
    # 计算差值
    difference = smoothed_int.loc[common_steps] - smoothed_base.loc[common_steps]
    
    # 使用bootstrap计算置信区间
    ci_lower_values = []
    ci_upper_values = []
    
    for step in common_steps:
        # 获取该步数的干预数据和基线数据
        int_vals = intervention_data[intervention_data[x_col] == step][y_col].values
        base_vals = baseline_data[baseline_data[x_col] == step][y_col].values
        
        if len(int_vals) > 1 and len(base_vals) > 1:  # 需要至少2个数据点才能计算方差
            bootstrap_diffs = []
            
            # 进行bootstrap采样
            for _ in range(n_bootstrap):
                # 有放回抽样
                sample_int = np.random.choice(int_vals, size=len(int_vals), replace=True)
                sample_base = np.random.choice(base_vals, size=len(base_vals), replace=True)
                
                # 计算均值差异
                mean_diff = np.mean(sample_int) - np.mean(sample_base)
                bootstrap_diffs.append(mean_diff)
            
            # 计算置信区间
            alpha = (1 - confidence) / 2
            ci_lower = np.percentile(bootstrap_diffs, alpha * 100)
            ci_upper = np.percentile(bootstrap_diffs, (1 - alpha) * 100)
        else:
            # 数据不足，使用NaN
            ci_lower = np.nan
            ci_upper = np.nan
        
        ci_lower_values.append(ci_lower)
        ci_upper_values.append(ci_upper)
    
    ci_lower = pd.Series(ci_lower_values, index=common_steps)
    ci_upper = pd.Series(ci_upper_values, index=common_steps)
    
    return difference, ci_lower, ci_upper, common_steps

def process_agent_groups(setting_data, setting_name):
    """处理智能体分组（针对多智能体设置）"""
    is_multi_agent = setting_name in ['setting3', 'setting4']
    
    if not is_multi_agent:
        return {}, {}
    
    # 获取无干预数据并计算第50步的值
    no_int_data = setting_data.get('no_intervention', pd.DataFrame())
    if no_int_data.empty:
        return {}, {}
    
    # 计算每个智能体在第50步的LOWESS值
    step_50_values = {}
    for agent_id in no_int_data['agentid'].unique():
        agent_data = no_int_data[no_int_data['agentid'] == agent_id]
        smoothed, _ = calculate_lowess_smooth(agent_data)
        if 50 in smoothed.index:
            step_50_values[agent_id] = smoothed[50]
    
    # 添加调试信息
    print(f"Setting {setting_name}: Found {len(step_50_values)} agents with step 50 data")
    if step_50_values:
        for agent_id, value in step_50_values.items():
            print(f"  Agent {agent_id}: value = {value:.4f}")
    
    if len(step_50_values) < 2:
        print(f"  Warning: Not enough agents with step 50 data for grouping")
        return {}, {}
    
    # 确定top和low组
    sorted_agents = sorted(step_50_values.items(), key=lambda x: x[1], reverse=True)
    top_agent = sorted_agents[0][0]
    low_agent = sorted_agents[1][0]
    
    print(f"  Grouping: Agent {top_agent} -> 'top', Agent {low_agent} -> 'low'")
    
    return {top_agent: 'top', low_agent: 'low'}, step_50_values

def create_setting_plots(all_data, output_dir):
    """为每个设置创建图表（1行4列）"""
    # 定义列名常量
    x_col = 'step'
    y_col = 'CumulativeReward'

    plt.rcParams['xtick.labelsize'] = 24
    plt.rcParams['ytick.labelsize'] = 24
    
    # 创建1行4列的大图
    fig, axes = plt.subplots(1, 4, figsize=(20, 5))
    
    # 首先收集所有数据来确定全局Y轴范围
    all_differences_global = []
    
    for setting_name, setting_data in all_data.items():
        # 处理智能体分组
        agent_groups, step_50_values = process_agent_groups(setting_data, setting_name)
        is_multi_agent = bool(agent_groups)
        
        # 计算无干预基线
        no_int_data = setting_data.get('no_intervention', pd.DataFrame())
        if no_int_data.empty:
            continue
        
        # 检查是否有干预数据
        if 'intervention' not in setting_data:
            continue
        
        int_data = setting_data['intervention']
        
        if is_multi_agent:
            # 多智能体：分别收集top和low组
            for agent_id, group_type in agent_groups.items():
                agent_int_data = int_data[int_data['agentid'] == agent_id]
                agent_base_data = no_int_data[no_int_data['agentid'] == agent_id]
                
                # 计算差值
                difference, ci_lower, ci_upper, steps = calculate_difference_with_ci(
                    agent_int_data, agent_base_data, x_col, y_col
                )
                
                if not difference.empty:
                    all_differences_global.extend(difference.values)
        else:
            # 单智能体
            difference, ci_lower, ci_upper, steps = calculate_difference_with_ci(
                int_data, no_int_data, x_col, y_col
            )
            
            if not difference.empty:
                all_differences_global.extend(difference.values)
    
    # 确定全局Y轴范围
    if all_differences_global:
        y_min_global = np.min(all_differences_global) * 1.1 if np.min(all_differences_global) < 0 else np.min(all_differences_global) * 0.9
        y_max_global = np.max(all_differences_global) * 1.1 if np.max(all_differences_global) > 0 else np.max(all_differences_global) * 0.9
        # 确保范围不为0
        if y_min_global == y_max_global:
            y_min_global, y_max_global = y_min_global - 0.1, y_max_global + 0.1
    else:
        y_min_global, y_max_global = -1, 1
    
    # 处理每个设置并绘制图表
    for idx, (setting_name, setting_data) in enumerate(all_data.items()):
        ax = axes[idx]
        print(f"\nCreating plot for {setting_name}...")
        
        # 处理智能体分组
        agent_groups, step_50_values = process_agent_groups(setting_data, setting_name)
        is_multi_agent = bool(agent_groups)
        
        # 计算无干预基线
        no_int_data = setting_data.get('no_intervention', pd.DataFrame())
        if no_int_data.empty:
            print(f"  Warning: Missing no intervention data for {setting_name}")
            ax.text(0.5, 0.5, 'No Baseline Data', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12)
            ax.set_title(setting_titles[setting_name], fontsize=24, fontweight='bold')
            ax.set_ylim(y_min_global, y_max_global)
            continue
        
        # 检查是否有干预数据
        if 'intervention' not in setting_data:
            print(f"  Warning: No intervention data for {setting_name}")
            ax.text(0.5, 0.5, 'No Intervention Data', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12)
            ax.set_title(setting_titles[setting_name], fontsize=24, fontweight='bold')
            ax.set_ylim(y_min_global, y_max_global)
            continue
        
        int_data = setting_data['intervention']
        
        # 绘制干预率为0.25的曲线
        has_data = False
        
        if is_multi_agent:
            # 多智能体：分别绘制top和low组
            for agent_id, group_type in agent_groups.items():
                agent_int_data = int_data[int_data['agentid'] == agent_id]
                agent_base_data = no_int_data[no_int_data['agentid'] == agent_id]
                
                # 计算差值和置信区间
                difference, ci_lower, ci_upper, steps = calculate_difference_with_ci(
                    agent_int_data, agent_base_data, x_col, y_col
                )
                
                if not difference.empty and not ci_lower.empty and not ci_upper.empty:
                    if group_type == 'top':
                        # top组：蓝色实线 + 蓝色置信区间
                        color = '#0000FF'  # 蓝色
                        linestyle = '-'
                        ax.plot(steps, difference, color=color, 
                               linestyle=linestyle, linewidth=2)
                        # 绘制置信区间
                        ax.fill_between(steps, ci_lower, ci_upper, color=color, alpha=0.2)
                    else:
                        # low组：红色实线 + 红色置信区间
                        color = '#FF0000'  # 红色
                        linestyle = '-'
                        ax.plot(steps, difference, color=color, 
                               linestyle=linestyle, linewidth=2)
                        # 绘制置信区间
                        ax.fill_between(steps, ci_lower, ci_upper, color=color, alpha=0.2)
                    
                    has_data = True
        else:
            # 单智能体：蓝色实线 + 蓝色置信区间
            difference, ci_lower, ci_upper, steps = calculate_difference_with_ci(
                int_data, no_int_data, x_col, y_col
            )
            
            if not difference.empty and not ci_lower.empty and not ci_upper.empty:
                color = '#0000FF'  # 蓝色
                ax.plot(steps, difference, color=color, 
                       linewidth=2)
                # 绘制置信区间
                ax.fill_between(steps, ci_lower, ci_upper, color=color, alpha=0.2)
                has_data = True
        
        # 绘制黑色零线
        ax.axhline(y=0, color='black', linestyle='-', linewidth=2, alpha=0.7)
        
        ax.set_title(setting_titles[setting_name], fontsize=24, fontweight='bold')
        ax.set_xlabel('Steps', fontsize=24, fontweight='bold')
        if idx == 0:
            ax.set_ylabel('Reward Difference', fontsize=24, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # 设置统一的Y轴范围
        ax.set_ylim(y_min_global, y_max_global)
    
    for i, ax in enumerate(axes):
        if i > 0:  # 不是第一个子图
            ax.set_ylabel('')  # 移除Y轴标签
            ax.tick_params(axis='y', which='both', left=False, labelleft=False)  # 隐藏Y轴刻度和标签
        else:  # 第一个子图
            ax.tick_params(axis='y', labelsize=24)  # 加大Y轴刻度字体

    # 调整布局并保存
    plt.tight_layout()
    
    output_file = output_dir / 'all_settings_intervention_analysis_rate_0.25.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\nPlot saved: {output_file}")

def main():
    # 获取当前脚本所在目录
    script_dir = Path(__file__).parent
    
    # 设置结果文件夹路径
    results_dir = script_dir / "干预results2"
    output_dir = script_dir / "analysis_results"
    output_dir.mkdir(exist_ok=True)
    
    if not results_dir.exists():
        print(f"Error: Cannot find results folder {results_dir}")
        return
    
    print("Loading and processing data...")
    
    # 加载数据
    all_data = load_and_process_data(results_dir)
    
    if not all_data:
        print("No valid data found, please check folder structure")
        return
    
    print("\nCreating plots...")
    
    # 创建图表
    create_setting_plots(all_data, output_dir)
    
    print(f"\nAnalysis completed! Results saved in: {output_dir}")

if __name__ == "__main__":
    main()