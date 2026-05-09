import os
import numpy as np
import pandas as pd
from scipy.optimize import minimize

# ==================== 路径与输入配置 ====================
# 自动获取脚本所在目录，并读取同目录下的random.csv
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, "smooth.csv")

# 1. Pellet瓷砖坐标 (P)
pellet_tiles = np.array([[2, 2], [1, 2], [2, 1], [2, 3], [3, 2], [1, 1], [1, 3], [3, 1], [3, 3], [5, 5], [4, 5], [5, 4], [5, 6], [6, 5], [4, 4], [4, 6], [6, 4], [6, 6]])

# 2. 网格参数
GRID_SIZE = 8  # 假设8x8网格
N_TILES = GRID_SIZE ** 2

# 3. 读取干预数据（确保列名匹配）
try:
    data = pd.read_csv(csv_path)
    interventions = data[['agent_ini_pos_x', 'agent_ini_pos_y']].values  # s_start坐标
    targets = data[['agent_end_pos_x', 'agent_end_pos_y']].values        # 干预目标位置
except KeyError as e:
    raise KeyError(f"CSV文件必须包含列: {e}. 请检查列名是否为agent_ini_pos_x/y和agent_end_pos_x/y")

# ==================== 核心函数 ====================
def is_pellet(tile):
    """检查是否为Pellet瓷砖"""
    return any(np.all(tile == pellet_tiles, axis=1))

def get_5x5_neighborhood(center):
    """生成5x5邻域内所有有效瓷砖坐标"""
    x, y = center
    neighbors = []
    for dx in [-2, -1, 0, 1, 2]:
        for dy in [-2, -1, 0, 1, 2]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                neighbors.append((nx, ny))
    return neighbors

def compute_SH(hypothesis, start_pos):
    """动态计算假设对应的瓷砖集合"""
    neighborhood = get_5x5_neighborhood(start_pos)
    
    if hypothesis == 'H1':  # Restart: 邻域内NP瓷砖
        return [tuple(t) for t in neighborhood if not is_pellet(t)]
    elif hypothesis == 'H2':  # Retry: 仅起始位置
        return [tuple(start_pos)]
    elif hypothesis == 'H3':  # Demonstration: 邻域内P瓷砖
        return [tuple(t) for t in neighborhood if is_pellet(t)]

def negative_log_likelihood(lambda_H, interventions, targets, hypothesis):
    """计算负对数似然（最小化目标）"""
    total = 0
    for (start_pos, target_pos) in zip(interventions, targets):
        S_H = compute_SH(hypothesis, start_pos)
        N_H = len(S_H)
        
        target_pos = tuple(target_pos)  # 转换为可哈希类型
        if target_pos in S_H:
            prob = lambda_H/N_H + (1-lambda_H)/N_TILES
        else:
            prob = (1-lambda_H)/N_TILES
        
        total -= np.log(max(prob, 1e-10))  # 避免log(0)
    return total

# ==================== 参数估计 ====================
results = {}
for hypo in ['H1', 'H2', 'H3']:
    res = minimize(negative_log_likelihood, x0=0.5, 
                   args=(interventions, targets, hypo),
                   bounds=[(0, 1)],
                   method='L-BFGS-B')
    results[hypo] = {
        'lambda': res.x[0],
        'likelihood': -res.fun,
        'n_interventions': len(interventions)
    }

# ==================== 结果输出 ====================
print("\n=== 全局假设拟合结果 ===")
print(f"数据路径: {csv_path}")
print(f"网格大小: {GRID_SIZE}x{GRID_SIZE}, Pellet瓷砖数: {len(pellet_tiles)}")
print(f"总干预次数: {len(interventions)}")
print("="*40)
for hypo in results:
    print(f"{hypo}: λ = {results[hypo]['lambda']:.3f} | 对数似然 = {results[hypo]['likelihood']:.1f}")

best_hypo = max(results, key=lambda x: results[x]['likelihood'])
print(f"\n最佳拟合假设: {best_hypo} (最高似然)")