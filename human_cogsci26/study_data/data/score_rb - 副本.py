# expected_score_by_type.py
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.nonparametric.smoothers_lowess import lowess
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['axes.unicode_minus'] = False
plt.ioff()

setting_titles = {
    'setting1': 'One agent Random env',
    'setting2': 'One agent Smooth env', 
    'setting3': 'Two agents Random env',
    'setting4': 'Two agents Smooth env'
}


FRAC = 0.3
N_BOOTSTRAP = 100  # 新增：bootstrap次数
ALPHA = 0.05       # 新增：置信水平
BASE = os.path.dirname(os.path.abspath(__file__))

# -------------- 工具 --------------
def lowess_line(x: np.ndarray, y: np.ndarray):
    mask = ~np.isnan(x) & ~np.isnan(y)
    if not mask.any():
        return np.array([]), np.array([])
    x_clean, y_clean = x[mask], y[mask]
    order = np.argsort(x_clean)
    smoothed = lowess(y_clean[order], x_clean[order], frac=FRAC, it=3)
    return smoothed[:, 0], smoothed[:, 1]

# 新增：计算置信区间
def bootstrap_ci(x: np.ndarray, y: np.ndarray, n_bootstrap=N_BOOTSTRAP, alpha=ALPHA):
    """使用bootstrap方法计算置信区间"""
    if len(x) < 10:  # 数据太少不计算置信区间
        return np.array([]), np.array([]), np.array([])
    
    mask = ~np.isnan(x) & ~np.isnan(y)
    x_clean, y_clean = x[mask], y[mask]
    
    if len(x_clean) < 10:
        return np.array([]), np.array([]), np.array([])
    
    # 存储bootstrap结果
    bootstrap_results = []
    x_eval = np.linspace(x_clean.min(), x_clean.max(), 100)
    
    for _ in range(n_bootstrap):
        # 有放回抽样
        indices = np.random.choice(len(x_clean), len(x_clean), replace=True)
        x_sample = x_clean[indices]
        y_sample = y_clean[indices]
        
        try:
            # 排序并平滑
            order = np.argsort(x_sample)
            smoothed = lowess(y_sample[order], x_sample[order], frac=FRAC, it=3)
            if len(smoothed) > 0:
                # 插值到统一的x网格
                y_interp = np.interp(x_eval, smoothed[:, 0], smoothed[:, 1], left=np.nan, right=np.nan)
                bootstrap_results.append(y_interp)
        except:
            continue
    
    if not bootstrap_results:
        return np.array([]), np.array([]), np.array([])
    
    bootstrap_results = np.array(bootstrap_results)
    # 计算置信区间
    lower = np.nanpercentile(bootstrap_results, (alpha/2)*100, axis=0)
    upper = np.nanpercentile(bootstrap_results, (1-alpha/2)*100, axis=0)
    mean = np.nanmean(bootstrap_results, axis=0)
    
    return x_eval, mean, (lower, upper)

# -------------- 数据构建 --------------
def build_black_df(rounds: list[int]) -> pd.DataFrame:
    detailed = pd.read_csv(os.path.join(BASE, 'black', 'user_round_counts_detailed.csv'))
    round_cols = [f'round_{r}' for r in rounds]
    detailed = detailed[['user_id'] + round_cols].melt(
        id_vars='user_id', var_name='round_col', value_name='val')
    detailed = detailed[detailed['val'] <= 0]
    detailed['round'] = detailed['round_col'].str.extract(r'round_(\d+)').astype(int)

    black_keys = detailed[['user_id', 'round']].drop_duplicates()
    black_keys['user_id'] = pd.to_numeric(black_keys['user_id'], errors='coerce')
    black_keys = black_keys.dropna().astype({'user_id': 'int64', 'round': 'int64'})

    data_path = os.path.join(BASE, 'black', 'user_data.csv')
    if not os.path.exists(data_path):
        return pd.DataFrame()
    df = pd.read_csv(data_path)
    df['user_id'] = pd.to_numeric(df['user_id'], errors='coerce')
    df = df.dropna(subset=['user_id']).astype({'user_id': 'int64', 'round': 'int64'})
    df = df.merge(black_keys, on=['user_id', 'round'], how='inner')
    return df

def build_colored_df(rounds: list[int], lower: int, upper: int | None):
    """lower < avg <= upper；upper=None 表示无上限"""
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

    data_paths = [os.path.join(BASE, fld, 'user_data.csv') for fld in ('clean', 'pilot')]
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
                       *lowess_line(g['time'].values, g['score'].values),
                       left=np.nan, right=np.nan))
               .reset_index(name='score_val'))
    best = (score.sort_values('score_val')
                  .drop_duplicates(['user_id', 'round'], keep='last')
                  .assign(group='top'))
    best['agent_id_best'] = best['agent_id']
    sub = sub.merge(best[['user_id', 'round', 'agent_id_best', 'group']],
                    on=['user_id', 'round'], how='left')
    sub['group'] = np.where(sub['agent_id'] == sub['agent_id_best'], 'top', 'low')
    return sub[['user_id', 'round', 'agent_id', 'time', 'score', 'group']]

# -------------- 绘图函数 --------------
def plot_all_types():
    settings = [([2, 3], "setting1", 1),
                ([4, 5], "setting2", 2),
                ([6, 7], "setting3", 3),
                ([8, 9], "setting4", 4)]
    fig, axes = plt.subplots(1, 4, figsize=(24, 6))
    
    # 先收集所有数据点的Y值范围，用于统一设置Y轴范围
    all_y_values = []
    
    def delta_line(xs: np.ndarray, ys: np.ndarray, base_x: np.ndarray, base_y: np.ndarray):
        """返回 (xs, ys - base_y@xs) ；base 用线性插值补全"""
        if base_x.size == 0:
            return xs, ys          # 无基准则原样返回
        base_interp = np.interp(xs, base_x, base_y, left=np.nan, right=np.nan)
        return xs, ys - base_interp
    
    # 先收集所有数据点的Y值范围
    for ax, (rnds, title, st) in zip(axes, settings):
        # ---- 基准黑线（只计算不画）----
        black_df = build_black_df(rnds)
        base_lines = {}          # 存 top/low 的 (x_sm, y_sm) 供后面做差
        if not black_df.empty:
            if st <= 2:
                b = black_df[black_df['agent_id'] == 0]
                base_x, base_y = lowess_line(b['time'].values, b['score'].values)
                base_lines['all'] = (base_x, base_y)
            else:
                bsub = build_top_low(black_df, rnds)
                for grp in ['top', 'low']:
                    b = bsub[bsub['group'] == grp]
                    base_x, base_y = lowess_line(b['time'].values, b['score'].values)
                    base_lines[grp] = (base_x, base_y)
        # ----------------------------------

        # ---- 红线（相对黑线） ----
        red_df = build_colored_df(rnds, 0, 15)
        if not red_df.empty:
            if st <= 2:
                r = red_df[red_df['agent_id'] == 0]
                x_sm, y_sm = lowess_line(r['time'].values, r['score'].values)
                x_sm, y_sm = delta_line(x_sm, y_sm, *base_lines.get('all', (np.array([]), np.array([]))))
                if x_sm.size:
                    all_y_values.extend(y_sm)
            else:
                rsub = build_top_low(red_df, rnds)
                for grp, lst in [('top', '-'), ('low', '--')]:
                    r = rsub[rsub['group'] == grp]
                    x_sm, y_sm = lowess_line(r['time'].values, r['score'].values)
                    x_sm, y_sm = delta_line(x_sm, y_sm, *base_lines.get(grp, (np.array([]), np.array([]))))
                    if x_sm.size:
                        all_y_values.extend(y_sm)

        # ---- 蓝线（相对黑线） ----
        blue_df = build_colored_df(rnds, 15, None)
        if not blue_df.empty:
            if st <= 2:
                b = blue_df[blue_df['agent_id'] == 0]
                x_sm, y_sm = lowess_line(b['time'].values, b['score'].values)
                x_sm, y_sm = delta_line(x_sm, y_sm, *base_lines.get('all', (np.array([]), np.array([]))))
                if x_sm.size:
                    all_y_values.extend(y_sm)
            else:
                bsub = build_top_low(blue_df, rnds)
                for grp, lst in [('top', '-'), ('low', '--')]:
                    b = bsub[bsub['group'] == grp]
                    x_sm, y_sm = lowess_line(b['time'].values, b['score'].values)
                    x_sm, y_sm = delta_line(x_sm, y_sm, *base_lines.get(grp, (np.array([]), np.array([]))))
                    if x_sm.size:
                        all_y_values.extend(y_sm)
    
    # 计算统一的Y轴范围，并留出一些边距
    if all_y_values:
        y_min = min(all_y_values)
        y_max = max(all_y_values)
        margin = (y_max - y_min) * 0.1  # 10%的边距
        y_min -= margin
        y_max += margin
    else:
        # 如果没有数据，使用默认范围
        y_min, y_max = -1, 1
    
    # 再次循环，这次绘制图形并设置统一的Y轴范围
    for ax, (rnds, title, st) in zip(axes, settings):
        # ---- 基准黑线（只计算不画）----
        black_df = build_black_df(rnds)
        base_lines = {}          # 存 top/low 的 (x_sm, y_sm) 供后面做差
        if not black_df.empty:
            if st <= 2:
                b = black_df[black_df['agent_id'] == 0]
                base_x, base_y = lowess_line(b['time'].values, b['score'].values)
                base_lines['all'] = (base_x, base_y)
            else:
                bsub = build_top_low(black_df, rnds)
                for grp in ['top', 'low']:
                    b = bsub[bsub['group'] == grp]
                    base_x, base_y = lowess_line(b['time'].values, b['score'].values)
                    base_lines[grp] = (base_x, base_y)
        # ----------------------------------

        # ---- 红线（相对黑线） ----
        red_df = build_colored_df(rnds, 0, 15)
        if not red_df.empty:
            if st <= 2:
                r = red_df[red_df['agent_id'] == 0]
                x_sm, y_sm = lowess_line(r['time'].values, r['score'].values)
                x_sm, y_sm = delta_line(x_sm, y_sm, *base_lines.get('all', (np.array([]), np.array([]))))
                if x_sm.size:
                    # 计算置信区间
                    x_ci, y_ci, (lower_ci, upper_ci) = bootstrap_ci(r['time'].values, r['score'].values)
                    if x_ci.size:
                        # 对置信区间也做差值处理
                        base_x_all, base_y_all = base_lines.get('all', (np.array([]), np.array([])))
                        if base_x_all.size:
                            base_interp = np.interp(x_ci, base_x_all, base_y_all, left=np.nan, right=np.nan)
                            y_ci = y_ci - base_interp
                            lower_ci = lower_ci - base_interp
                            upper_ci = upper_ci - base_interp
                        
                        ax.fill_between(x_ci, lower_ci, upper_ci, color='red', alpha=0.3)
                        ax.plot(x_sm, y_sm, color='red', linewidth=2.5, label='RED (≤15)')
            else:
                rsub = build_top_low(red_df, rnds)
                for grp, lst in [('top', '-'), ('low', '--')]:
                    r = rsub[rsub['group'] == grp]
                    x_sm, y_sm = lowess_line(r['time'].values, r['score'].values)
                    x_sm, y_sm = delta_line(x_sm, y_sm, *base_lines.get(grp, (np.array([]), np.array([]))))
                    if x_sm.size:
                        # 计算置信区间
                        x_ci, y_ci, (lower_ci, upper_ci) = bootstrap_ci(r['time'].values, r['score'].values)
                        if x_ci.size:
                            # 对置信区间也做差值处理
                            base_x_grp, base_y_grp = base_lines.get(grp, (np.array([]), np.array([])))
                            if base_x_grp.size:
                                base_interp = np.interp(x_ci, base_x_grp, base_y_grp, left=np.nan, right=np.nan)
                                y_ci = y_ci - base_interp
                                lower_ci = lower_ci - base_interp
                                upper_ci = upper_ci - base_interp
                            
                            ax.fill_between(x_ci, lower_ci, upper_ci, color='red', alpha=0.3)
                            ax.plot(x_sm, y_sm, color='red', linewidth=2.5, linestyle=lst, label=f'RED-{grp} (≤15)')

        # ---- 蓝线（相对黑线） ----
        blue_df = build_colored_df(rnds, 15, None)
        if not blue_df.empty:
            if st <= 2:
                b = blue_df[blue_df['agent_id'] == 0]
                x_sm, y_sm = lowess_line(b['time'].values, b['score'].values)
                x_sm, y_sm = delta_line(x_sm, y_sm, *base_lines.get('all', (np.array([]), np.array([]))))
                if x_sm.size:
                    # 计算置信区间
                    x_ci, y_ci, (lower_ci, upper_ci) = bootstrap_ci(b['time'].values, b['score'].values)
                    if x_ci.size:
                        # 对置信区间也做差值处理
                        base_x_all, base_y_all = base_lines.get('all', (np.array([]), np.array([])))
                        if base_x_all.size:
                            base_interp = np.interp(x_ci, base_x_all, base_y_all, left=np.nan, right=np.nan)
                            y_ci = y_ci - base_interp
                            lower_ci = lower_ci - base_interp
                            upper_ci = upper_ci - base_interp
                        
                        ax.fill_between(x_ci, lower_ci, upper_ci, color='blue', alpha=0.3)
                        ax.plot(x_sm, y_sm, color='blue', linewidth=2.5, label='BLUE (>15)')
            else:
                bsub = build_top_low(blue_df, rnds)
                for grp, lst in [('top', '-'), ('low', '--')]:
                    b = bsub[bsub['group'] == grp]
                    x_sm, y_sm = lowess_line(b['time'].values, b['score'].values)
                    x_sm, y_sm = delta_line(x_sm, y_sm, *base_lines.get(grp, (np.array([]), np.array([]))))
                    if x_sm.size:
                        # 计算置信区间
                        x_ci, y_ci, (lower_ci, upper_ci) = bootstrap_ci(b['time'].values, b['score'].values)
                        if x_ci.size:
                            # 对置信区间也做差值处理
                            base_x_grp, base_y_grp = base_lines.get(grp, (np.array([]), np.array([])))
                            if base_x_grp.size:
                                base_interp = np.interp(x_ci, base_x_grp, base_y_grp, left=np.nan, right=np.nan)
                                y_ci = y_ci - base_interp
                                lower_ci = lower_ci - base_interp
                                upper_ci = upper_ci - base_interp
                            
                            ax.fill_between(x_ci, lower_ci, upper_ci, color='blue', alpha=0.3)
                            ax.plot(x_sm, y_sm, color='blue', linewidth=2.5, linestyle=lst, label=f'BLUE-{grp} (>15)')

        ax.axhline(0, color='black', linewidth=1.5, linestyle='-')
        ax.set_title(setting_titles[title], fontsize=24, fontweight='bold')
        ax.set_xlabel('Time', fontsize=24, fontweight='bold')
        if ax == axes[0]:
            ax.set_ylabel('Reward Difference', fontsize=24, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', which='major', labelsize=24)
        
        # 设置统一的Y轴范围
        ax.set_ylim(y_min, y_max)
        if st != 1:
            ax.set_yticklabels([])
        
        # # 添加图例
        # if st == 1:  # 只在第一个子图添加图例
        #     ax.legend(loc='best', fontsize=10)

    plt.tight_layout()
    fname = "7.5.32.png"
    out_path = os.path.join(BASE, fname)
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"图片已保存至: {os.path.abspath(out_path)}")

# -------------- 主函数 --------------
def main():
    try:
        plot_all_types()
        print("所有类型得分对比图生成完成！")
    except Exception as e:
        print("处理失败:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()