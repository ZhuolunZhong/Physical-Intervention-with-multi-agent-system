import os
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from collections import defaultdict

# ==================== 路径与输入配置 ====================
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, "random.csv")

# 1. Pellet瓷砖坐标 (P)
pellet_tiles = np.array([[0, 1], [7, 0], [3, 1], [1, 4], [7, 4], [2, 0], [7, 7], [7, 3], [4, 0], [2, 7], [4, 1], [4, 3], [4, 7]])

# 2. 网格参数
GRID_SIZE = 8
N_TILES = GRID_SIZE ** 2

# 3. 读取干预数据
try:
    data = pd.read_csv(csv_path)
    if 'user_id' not in data.columns:
        raise KeyError("CSV文件必须包含user_id列")
except KeyError as e:
    raise KeyError(f"CSV文件必须包含列: {e}")

# ==================== 核心函数 ====================
def is_pellet(tile):
    """检查是否为Pellet瓷砖"""
    return any(np.all(tile == pellet_tiles, axis=1))

def get_neighborhood(center, size):
    """生成指定大小的邻域内所有有效瓷砖坐标"""
    x, y = center
    radius = size // 2
    neighbors = []
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            nx, ny = x + dx, y + dy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                neighbors.append((nx, ny))
    return neighbors

def has_adjacent_pellet(tile):
    """检查一个瓷砖的3x3邻域内是否有Pellet瓷砖"""
    neighborhood = get_neighborhood(tile, 3)
    return any(is_pellet(adj_tile) for adj_tile in neighborhood)

def compute_SH(hypothesis, start_pos):
    """动态计算假设对应的瓷砖集合（按新顺序H1-H4）"""
    
    if hypothesis == 'H1':  # Undoing: 仅起始位置
        return [tuple(start_pos)]
    
    elif hypothesis == 'H2':  # Correction: 5x5范围内的P瓷砖
        neighborhood = get_neighborhood(start_pos, 5)
        return [tuple(t) for t in neighborhood if is_pellet(t)]
    
    elif hypothesis == 'H3':  # Exploration-encouraging: 5x5范围内，3x3邻域有P的NP瓷砖
        neighborhood = get_neighborhood(start_pos, 5)
        return [tuple(t) for t in neighborhood 
                if not is_pellet(t) and has_adjacent_pellet(t)]
    
    elif hypothesis == 'H4':  # Restart: 5x5范围内，3x3邻域没有P的NP瓷砖
        neighborhood = get_neighborhood(start_pos, 5)
        return [tuple(t) for t in neighborhood 
                if not is_pellet(t) and not has_adjacent_pellet(t)]

def negative_log_likelihood(lambda_H, interventions, targets, hypothesis):
    """计算负对数似然（最小化目标）"""
    total = 0
    for (start_pos, target_pos) in zip(interventions, targets):
        S_H = compute_SH(hypothesis, start_pos)
        N_H = len(S_H)
        
        target_pos = tuple(target_pos)
        if N_H > 0:
            if target_pos in S_H:
                prob = lambda_H/N_H + (1-lambda_H)/N_TILES
            else:
                prob = (1-lambda_H)/N_TILES
        else:
            prob = 1.0/N_TILES
        
        total -= np.log(max(prob, 1e-10))
    return total

# ==================== 参数估计 ====================
def analyze_user_data(user_data):
    """分析单个用户的数据"""
    interventions = user_data[['agent_ini_pos_x', 'agent_ini_pos_y']].values
    targets = user_data[['agent_end_pos_x', 'agent_end_pos_y']].values
    
    results = {}
    for hypo in ['H1', 'H2', 'H3', 'H4']:  # 按新顺序H1-H4
        # 为不同假设提供不同的初始值
        initial_guess = 0.8 if hypo == 'H1' else 0.7 if hypo in ['H3', 'H4'] else 0.5
        
        res = minimize(negative_log_likelihood, x0=initial_guess, 
                      args=(interventions, targets, hypo),
                      bounds=[(0, 1)],
                      method='L-BFGS-B')
        results[hypo] = {
            'lambda': res.x[0],
            'likelihood': -res.fun,
            'success': res.success
        }
    
    best_hypo = max(results, key=lambda x: results[x]['likelihood'])
    return best_hypo, results

# ==================== 主分析流程 ====================
user_groups = data.groupby('user_id')
hypothesis_counts = defaultdict(int)
detailed_results = {}

for user_id, user_data in user_groups:
    best_hypo, results = analyze_user_data(user_data)
    hypothesis_counts[best_hypo] += 1
    detailed_results[user_id] = {
        'best_hypothesis': best_hypo,
        'results': results
    }

# ==================== 结果输出 ====================
print("\n=== 用户行为假设分析报告 ===")
print(f"总用户数: {len(user_groups)}")
print("假设顺序: H1(Undoing), H2(Correction), H3(Exploration-encouraging), H4(Restart)")
print("="*50)

print("\n=== 总体统计 ===")
for hypo in ['H1', 'H2', 'H3', 'H4']:
    count = hypothesis_counts.get(hypo, 0)
    print(f"{hypo}: {count} 用户 ({count/len(user_groups):.1%})")

print("\n=== 总结 ===")
most_common_hypo = max(hypothesis_counts, key=hypothesis_counts.get)
hypo_names = {'H1': 'Undoing', 'H2': 'Correction', 'H3': 'Exploration-encouraging', 'H4': 'Restart'}
print(f"最常见策略: {hypo_names[most_common_hypo]} ({most_common_hypo}), {hypothesis_counts[most_common_hypo]} 用户")