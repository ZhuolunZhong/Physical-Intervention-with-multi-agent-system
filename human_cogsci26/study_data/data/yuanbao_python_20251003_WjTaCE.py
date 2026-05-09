# expected_q_delta.py
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.nonparametric.smoothers_lowess import lowess
from tqdm import tqdm  # 添加进度条

plt.rcParams['axes.unicode_minus'] = False
plt.ioff()

setting_titles = {
    'setting1': 'One agent Random env',
    'setting2': 'One agent Smooth env', 
    'setting3': 'Two agents Random env',
    'setting4': 'Two agents Smooth env'
}

FRAC = 0.3
BASE = os.path.dirname(os.path.abspath(__file__))
BOOTSTRAP_ITERATIONS = 1000  # bootstrap迭代次数
CI_ALPHA = 0.05  # 置信水平 (95%置信区间)

# -------------- 工具 --------------
def get_interpret_type(user_id: int) -> int:
    return (user_id - 1) % 6

def get_type_name(itype: int) -> str:
    names = {0: "SUGGESTION", 1: "RESET", 2: "INTERRUPT",
             3: "TRANSITION", 4: "DISRUPT", 5: "IMPEDE"}
    return names.get(itype, f"TYPE_{itype}")

def lowess_line(x: np.ndarray, y: np.ndarray):
    mask = ~np.isnan(x) & ~np.isnan(y)
    if not mask.any():
        return np.array([]), np.array([])
    x_clean, y_clean = x[mask], y[mask]
    order = np.argsort(x_clean)
    smoothed = lowess(y_clean[order], x_clean[order], frac=FRAC, it=3)
    return smoothed[:, 0], smoothed[:, 1]

# -------------- 新增bootstrap函数 --------------
def bootstrap_ci(x: np.ndarray, y: np.ndarray, n_iterations: int = BOOTSTRAP_ITERATIONS, 
                 alpha: float = CI_ALPHA, random_state: int = 42):
    """
    计算LOWESS平滑曲线的bootstrap置信区间
    
    参数:
    x, y: 原始数据
    n_iterations: bootstrap迭代次数
    alpha: 置信水平
    random_state: 随机种子
    
    返回:
    x_grid: 统一的x网格点
    lower_ci: 置信区间下界
    upper_ci: 置信区间上界
    """
    if len(x) == 0 or len(y) == 0:
        return np.array([]), np.array([]), np.array([])
    
    # 创建统一的x网格
    x_min, x_max = np.min(x), np.max(x)
    x_grid = np.linspace(x_min, x_max, 100)
    
    # 存储所有bootstrap样本的拟合结果
    bootstrap_fits = np.zeros((n_iterations, len(x_grid)))
    
    # 设置随机种子
    np.random.seed(random_state)
    
    # 原始数据索引
    indices = np.arange(len(x))
    
    for i in tqdm(range(n_iterations), desc="Bootstrap Progress", leave=False):
        # 有放回抽样
        sample_indices = np.random.choice(indices, size=len(indices), replace=True)
        x_sample = x[sample_indices]
        y_sample = y[sample_indices]
        
        # 去除NaN值
        mask = ~np.isnan(x_sample) & ~np.isnan(y_sample)
        x_clean, y_clean = x_sample[mask], y_sample[mask]
        
        if len(x_clean) > 10:  # 确保有足够的数据点
            # 对样本进行LOWESS拟合
            order = np.argsort(x_clean)
            smoothed = lowess(y_clean[order], x_clean[order], frac=FRAC, it=3)
            
            if len(smoothed) > 0:
                # 插值到统一的x网格
                y_interp = np.interp(x_grid, smoothed[:, 0], smoothed[:, 1], 
                                    left=np.nan, right=np.nan)
                bootstrap_fits[i, :] = y_interp
    
    # 计算置信区间
    lower_ci = np.nanpercentile(bootstrap_fits, 100 * alpha/2, axis=0)
    upper_ci = np.nanpercentile(bootstrap_fits, 100 * (1 - alpha/2), axis=0)
    
    return x_grid, lower_ci, upper_ci

def lowess_with_ci(x: np.ndarray, y: np.ndarray):
    """
    计算LOWESS平滑线及其置信区间
    
    返回:
    x_sm: 平滑后的x值
    y_sm: 平滑后的y值
    x_ci: 置信区间的x网格
    lower_ci: 置信区间下界
    upper_ci: 置信区间上界
    """
    x_sm, y_sm = lowess_line(x, y)
    x_ci, lower_ci, upper_ci = bootstrap_ci(x, y)
    return x_sm, y_sm, x_ci, lower_ci, upper_ci

# -------------- 数据构建 --------------
def build_black_df(rounds: list[int]) -> pd.DataFrame:
    detailed = pd.read_csv(os.path.join(BASE, 'black', 'user_round_counts_detailed.csv'))
    round_cols = [f'round_{r}' for r in rounds]
    detailed = detailed[['user_id'] + round_cols].melt(
        id_vars='user_id', var_name='round_col', value_name='val')
    detailed = detailed[detailed['val'] <= 0]          # 原 black 定义
    detailed['round'] = detailed['round_col'].str.extract(r'round_(\d+)').astype(int)

    black_keys = detailed[['user_id', 'round']].drop_duplicates()
    black_keys['user_id'] = pd.to_numeric(black_keys['user_id'], errors='coerce')
    black_keys = black_keys.dropna().astype({'user_id': 'int64', 'round': 'int64'})

    data_path = os.path.join(BASE, 'black', 'user_data_q.csv')
    if not os.path.exists(data_path):
        return pd.DataFrame()
    df = pd.read_csv(data_path)
    df['user_id'] = pd.to_numeric(df['user_id'], errors='coerce')
    df = df.dropna(subset=['user_id']).astype({'user_id': 'int64', 'round': 'int64'})
    df = df.merge(black_keys, on=['user_id', 'round'], how='inner')
    return df

def build_colored_df(rounds: list[int], itype: int, lower: int, upper: int | None):
    stats_paths = [os.path.join(BASE, fld, 'user_round_statistics.csv')
                   for fld in ('clean', 'pilot')]
    stats_paths = [p for p in stats_paths if os.path.exists(p)]
    if not stats_paths:
        return pd.DataFrame()
    stats = pd.concat([pd.read_csv(p) for p in stats_paths], ignore_index=True)

    round_cols = [f'round_{r}' for r in rounds]
    if not set(round_cols).issubset(stats.columns):
        return pd.DataFrame()
    stats = stats[['user_id'] + round_cols]
    stats['avg_inter'] = stats[round_cols].mean(axis=1)
    if upper is None:
        ok_users = stats[stats['avg_inter'] > lower]['user_id']
    else:
        ok_users = stats[(stats['avg_inter'] > lower) & (stats['avg_inter'] <= upper)]['user_id']
    if ok_users.empty:
        return pd.DataFrame()

    ok_users = ok_users.astype('int64').drop_duplicates()
    ok_users = ok_users[ok_users.apply(lambda uid: get_interpret_type(uid) == itype)]
    if ok_users.empty:
        return pd.DataFrame()

    data_paths = [os.path.join(BASE, fld, 'user_data_q.csv') for fld in ('clean', 'pilot')]
    data_paths = [p for p in data_paths if os.path.exists(p)]
    if not data_paths:
        return pd.DataFrame()
    df = pd.concat([pd.read_csv(p) for p in data_paths], ignore_index=True)
    df['user_id'] = pd.to_numeric(df['user_id'], errors='coerce')
    df = df.dropna(subset=['user_id']).astype({'user_id': 'int64', 'round': 'int64'})
    df = df[df['round'].isin(rounds)]
    df = df.merge(ok_users.to_frame('user_id'), on='user_id', how='inner')
    return df

def build_top_low(df: pd.DataFrame, rounds: list[int]) -> pd.DataFrame:
    sub = df[df['round'].isin(rounds) & df['agent_id'].isin([0, 1])].copy()
    score = (sub.groupby(['user_id', 'round', 'agent_id'])
               .apply(lambda g: np.interp(100,
                       *lowess_line(g['time'].values, g['ExpectedQvalue'].values),
                       left=np.nan, right=np.nan))
               .reset_index(name='score'))
    best = (score.sort_values('score')
                  .drop_duplicates(['user_id', 'round'], keep='last')
                  .assign(group='top'))
    best['agent_id_best'] = best['agent_id']
    sub = sub.merge(best[['user_id', 'round', 'agent_id_best', 'group']],
                    on=['user_id', 'round'], how='left')
    sub['group'] = np.where(sub['agent_id'] == sub['agent_id_best'], 'top', 'low')
    return sub[['user_id', 'round', 'agent_id', 'time', 'ExpectedQvalue', 'group']]

# -------------- 单类型绘图（核心改动） --------------
def plot_one_type(itype: int):
    settings = [([2, 3], "setting1", 1),
                ([4, 5], "setting2", 2),
                ([6, 7], "setting3", 3),
                ([8, 9], "setting4", 4)]
    fig, axes = plt.subplots(1, 4, figsize=(24, 6))

    def delta_line(xs, ys, base_x, base_y):
        if base_x.size == 0:
            return xs, ys
        return xs, ys - np.interp(xs, base_x, base_y, left=np.nan, right=np.nan)

    for ax, (rnds, title, st) in zip(axes, settings):
        # ---- 基准黑线（只计算不画）----
        black_df = build_black_df(rnds)
        base_lines = {}
        if not black_df.empty:
            if st <= 2:
                b = black_df[black_df['agent_id'] == 0]
                base_x, base_y = lowess_line(b['time'].values, b['ExpectedQvalue'].values)
                base_lines['all'] = (base_x, base_y)
            else:
                bsub = build_top_low(black_df, rnds)
                for grp in ['top', 'low']:
                    b = bsub[bsub['group'] == grp]
                    base_x, base_y = lowess_line(b['time'].values, b['ExpectedQvalue'].values)
                    base_lines[grp] = (base_x, base_y)

        # ---- 红线（相对黑线） ----
        red_df = build_colored_df(rnds, itype, 0, 15)
        if not red_df.empty:
            if st <= 2:
                r = red_df[red_df['agent_id'] == 0]
                # 使用带置信区间的LOWESS
                x_sm, y_sm, x_ci, lower_ci, upper_ci = lowess_with_ci(
                    r['time'].values, r['ExpectedQvalue'].values)
                
                if x_sm.size:
                    # 计算相对黑线的差值
                    x_sm, y_sm = delta_line(x_sm, y_sm, *base_lines.get('all', (np.array([]), np.array([]))))
                    # 计算置信区间相对于黑线的差值
                    x_ci, lower_ci = delta_line(x_ci, lower_ci, *base_lines.get('all', (np.array([]), np.array([]))))
                    x_ci, upper_ci = delta_line(x_ci, upper_ci, *base_lines.get('all', (np.array([]), np.array([]))))
                    
                    # 绘制置信区间
                    ax.fill_between(x_ci, lower_ci, upper_ci, color='red', alpha=0.2, label='RED 95% CI')
                    # 绘制主曲线
                    ax.plot(x_sm, y_sm, color='red', linewidth=2.5, label='RED')
            else:
                rsub = build_top_low(red_df, rnds)
                for grp, lst in [('top', '-'), ('low', '--')]:
                    r = rsub[rsub['group'] == grp]
                    # 使用带置信区间的LOWESS
                    x_sm, y_sm, x_ci, lower_ci, upper_ci = lowess_with_ci(
                        r['time'].values, r['ExpectedQvalue'].values)
                    
                    if x_sm.size:
                        # 计算相对黑线的差值
                        x_sm, y_sm = delta_line(x_sm, y_sm, *base_lines.get(grp, (np.array([]), np.array([]))))
                        # 计算置信区间相对于黑线的差值
                        x_ci, lower_ci = delta_line(x_ci, lower_ci, *base_lines.get(grp, (np.array([]), np.array([]))))
                        x_ci, upper_ci = delta_line(x_ci, upper_ci, *base_lines.get(grp, (np.array([]), np.array([]))))
                        
                        # 绘制置信区间
                        ax.fill_between(x_ci, lower_ci, upper_ci, color='red', alpha=0.2, 
                                       label=f'RED-{grp} 95% CI')
                        # 绘制主曲线
                        ax.plot(x_sm, y_sm, color='red', linewidth=2.5, linestyle=lst, label=f'RED-{grp}')

        # ---- 蓝线（相对黑线） ----
        blue_df = build_colored_df(rnds, itype, 15, None)
        if not blue_df.empty:
            if st <= 2:
                b = blue_df[blue_df['agent_id'] == 0]
                # 使用带置信区间的LOWESS
                x_sm, y_sm, x_ci, lower_ci, upper_ci = lowess_with_ci(
                    b['time'].values, b['ExpectedQvalue'].values)
                
                if x_sm.size:
                    # 计算相对黑线的差值
                    x_sm, y_sm = delta_line(x_sm, y_sm, *base_lines.get('all', (np.array([]), np.array([]))))
                    # 计算置信区间相对于黑线的差值
                    x_ci, lower_ci = delta_line(x_ci, lower_ci, *base_lines.get('all', (np.array([]), np.array([]))))
                    x_ci, upper_ci = delta_line(x_ci, upper_ci, *base_lines.get('all', (np.array([]), np.array([]))))
                    
                    # 绘制置信区间
                    ax.fill_between(x_ci, lower_ci, upper_ci, color='blue', alpha=0.2, label='BLUE 95% CI')
                    # 绘制主曲线
                    ax.plot(x_sm, y_sm, color='blue', linewidth=2.5, label='BLUE')
            else:
                bsub = build_top_low(blue_df, rnds)
                for grp, lst in [('top', '-'), ('low', '--')]:
                    b = bsub[bsub['group'] == grp]
                    # 使用带置信区间的LOWESS
                    x_sm, y_sm, x_ci, lower_ci, upper_ci = lowess_with_ci(
                        b['time'].values, b['ExpectedQvalue'].values)
                    
                    if x_sm.size:
                        # 计算相对黑线的差值
                        x_sm, y_sm = delta_line(x_sm, y_sm, *base_lines.get(grp, (np.array([]), np.array([]))))
                        # 计算置信区间相对于黑线的差值
                        x_ci, lower_ci = delta_line(x_ci, lower_ci, *base_lines.get(grp, (np.array([]), np.array([]))))
                        x_ci, upper_ci = delta_line(x_ci, upper_ci, *base_lines.get(grp, (np.array([]), np.array([]))))
                        
                        # 绘制置信区间
                        ax.fill_between(x_ci, lower_ci, upper_ci, color='blue', alpha=0.2, 
                                       label=f'BLUE-{grp} 95% CI')
                        # 绘制主曲线
                        ax.plot(x_sm, y_sm, color='blue', linewidth=2.5, linestyle=lst, label=f'BLUE-{grp}')

        # ===== 明显标出 0 基准 =====
        ax.axhline(0, color='black', linewidth=1.5, linestyle='-')
        if st != 1:
            ax.set_yticklabels([])
        ax.set_title(setting_titles[title], fontsize=24, fontweight='bold')
        ax.set_xlabel('Time', fontsize=24, fontweight='bold')
        if ax == axes[0]:
            ax.set_ylabel('Expected Reward Difference', fontsize=24, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', which='major', labelsize=24)

        # ===== 统一 4 个子图 Y 轴范围（自适应）=====
    y_all = []
    for axi in axes:
        y_low, y_high = axi.get_ylim()
        y_all += [y_low, y_high]
    y_min, y_max = min(y_all), max(y_all)
    margin = (y_max - y_min) * 0.05
    for axi in axes:
        axi.set_ylim(y_min - margin, y_max + margin)
    
    plt.tight_layout()
    fname = f"{get_type_name(itype)}_{itype}_with_ci.png"
    out_path = os.path.join(BASE, fname)
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"图片已保存至: {os.path.abspath(out_path)}")

# -------------- 主入口 --------------
def main():
    try:
        for itype in tqdm(range(6), desc="Processing interpretation types"):
            plot_one_type(itype)
    except Exception as e:
        print("处理失败:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()