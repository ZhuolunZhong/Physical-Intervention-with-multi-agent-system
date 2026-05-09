# expected_score_by_type_std.py
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.nonparametric.smoothers_lowess import lowess
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False
plt.ioff()

FRAC = 0.3
N_BOOTSTRAP = 100
ALPHA = 0.05
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

# 新增：使用标准差计算置信区间
def std_ci(x: np.ndarray, y: np.ndarray, alpha=ALPHA):
    """使用标准差方法计算置信区间"""
    if len(x) < 5:
        return np.array([]), np.array([]), np.array([])
    
    mask = ~np.isnan(x) & ~np.isnan(y)
    x_clean, y_clean = x[mask], y[mask]
    
    if len(x_clean) < 5:
        return np.array([]), np.array([]), np.array([])
    
    # 按时间分箱计算均值和标准差
    n_bins = min(20, len(x_clean) // 5)  # 动态分箱数量
    if n_bins < 3:
        return np.array([]), np.array([]), np.array([])
    
    # 创建时间分箱
    bins = np.linspace(x_clean.min(), x_clean.max(), n_bins + 1)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    
    means = []
    stds = []
    counts = []
    
    for i in range(len(bins) - 1):
        mask_bin = (x_clean >= bins[i]) & (x_clean < bins[i + 1])
        if i == len(bins) - 2:  # 最后一个区间包含上限
            mask_bin = (x_clean >= bins[i]) & (x_clean <= bins[i + 1])
        
        y_bin = y_clean[mask_bin]
        if len(y_bin) >= 3:  # 至少3个点才计算
            means.append(np.mean(y_bin))
            stds.append(np.std(y_bin))
            counts.append(len(y_bin))
        else:
            means.append(np.nan)
            stds.append(np.nan)
            counts.append(0)
    
    # 计算置信区间
    z_score = stats.norm.ppf(1 - alpha/2)
    ci_lower = []
    ci_upper = []
    
    for mean, std, count in zip(means, stds, counts):
        if not np.isnan(mean) and not np.isnan(std) and count >= 3:
            # 使用标准误
            se = std / np.sqrt(count)
            ci_lower.append(mean - z_score * se)
            ci_upper.append(mean + z_score * se)
        else:
            ci_lower.append(np.nan)
            ci_upper.append(np.nan)
    
    # 过滤掉NaN值
    valid_mask = ~np.isnan(means) & ~np.isnan(ci_lower) & ~np.isnan(ci_upper)
    if np.sum(valid_mask) < 3:
        return np.array([]), np.array([]), np.array([])
    
    bin_centers_valid = bin_centers[valid_mask]
    means_valid = np.array(means)[valid_mask]
    ci_lower_valid = np.array(ci_lower)[valid_mask]
    ci_upper_valid = np.array(ci_upper)[valid_mask]
    
    return bin_centers_valid, means_valid, (ci_lower_valid, ci_upper_valid)

# 原有的bootstrap方法
def bootstrap_ci(x: np.ndarray, y: np.ndarray, n_bootstrap=N_BOOTSTRAP, alpha=ALPHA):
    """使用bootstrap方法计算置信区间"""
    if len(x) < 10:
        return np.array([]), np.array([]), np.array([])
    
    mask = ~np.isnan(x) & ~np.isnan(y)
    x_clean, y_clean = x[mask], y[mask]
    
    if len(x_clean) < 10:
        return np.array([]), np.array([]), np.array([])
    
    bootstrap_results = []
    x_eval = np.linspace(x_clean.min(), x_clean.max(), 100)
    
    for _ in range(n_bootstrap):
        indices = np.random.choice(len(x_clean), len(x_clean), replace=True)
        x_sample = x_clean[indices]
        y_sample = y_clean[indices]
        
        try:
            order = np.argsort(x_sample)
            smoothed = lowess(y_sample[order], x_sample[order], frac=FRAC, it=3)
            if len(smoothed) > 0:
                y_interp = np.interp(x_eval, smoothed[:, 0], smoothed[:, 1], left=np.nan, right=np.nan)
                bootstrap_results.append(y_interp)
        except:
            continue
    
    if not bootstrap_results:
        return np.array([]), np.array([]), np.array([])
    
    bootstrap_results = np.array(bootstrap_results)
    lower = np.nanpercentile(bootstrap_results, (alpha/2)*100, axis=0)
    upper = np.nanpercentile(bootstrap_results, (1-alpha/2)*100, axis=0)
    mean = np.nanmean(bootstrap_results, axis=0)
    
    return x_eval, mean, (lower, upper)

# -------------- 数据构建函数（修复返回None的问题） --------------
def build_black_df(rounds: list[int]) -> pd.DataFrame:
    try:
        detailed_path = os.path.join(BASE, 'black', 'user_round_counts_detailed.csv')
        if not os.path.exists(detailed_path):
            return pd.DataFrame()
            
        detailed = pd.read_csv(detailed_path)
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
    except Exception as e:
        print(f"构建黑数据时出错: {e}")
        return pd.DataFrame()

def build_colored_df(rounds: list[int], lower: int, upper: int | None):
    """lower < avg <= upper；upper=None 表示无上限"""
    try:
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
    except Exception as e:
        print(f"构建彩色数据时出错: {e}")
        return pd.DataFrame()

def build_top_low(df: pd.DataFrame, rounds: list[int]) -> pd.DataFrame:
    try:
        if df is None or df.empty:
            return pd.DataFrame()
            
        sub = df[df['round'].isin(rounds) & df['agent_id'].isin([0, 1])].copy()
        if sub.empty:
            return pd.DataFrame()
            
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
    except Exception as e:
        print(f"构建top/low数据时出错: {e}")
        return pd.DataFrame()

# -------------- 辅助函数 --------------
def is_empty_df(df):
    """安全检查DataFrame是否为空"""
    return df is None or df.empty

def safe_lowess_line(x, y):
    """安全的lowess_line调用"""
    if x is None or y is None or len(x) == 0 or len(y) == 0:
        return np.array([]), np.array([])
    return lowess_line(x, y)

# -------------- 绘图函数 --------------
def plot_all_types(method='bootstrap'):
    """
    参数:
    method: 'bootstrap' 或 'std'，选择置信区间计算方法
    """
    settings = [([2, 3], "setting1", 1),
                ([4, 5], "setting2", 2),
                ([6, 7], "setting3", 3),
                ([8, 9], "setting4", 4)]
    fig, axes = plt.subplots(1, 4, figsize=(24, 6))
    
    # 选择置信区间计算方法
    if method == 'std':
        ci_function = std_ci
        method_label = '标准差方法'
    else:
        ci_function = bootstrap_ci
        method_label = 'Bootstrap方法'
    
    # 先收集所有数据点的Y值范围
    all_y_values = []
    
    def delta_line(xs: np.ndarray, ys: np.ndarray, base_x: np.ndarray, base_y: np.ndarray):
        if base_x is None or len(base_x) == 0 or len(base_y) == 0:
            return xs, ys
        base_interp = np.interp(xs, base_x, base_y, left=np.nan, right=np.nan)
        return xs, ys - base_interp
    
    # 收集Y值范围
    for ax, (rnds, title, st) in zip(axes, settings):
        black_df = build_black_df(rnds)
        base_lines = {}
        if not is_empty_df(black_df):
            if st <= 2:
                b = black_df[black_df['agent_id'] == 0]
                if not is_empty_df(b):
                    base_x, base_y = safe_lowess_line(b['time'].values, b['score'].values)
                    if len(base_x) > 0:
                        base_lines['all'] = (base_x, base_y)
            else:
                bsub = build_top_low(black_df, rnds)
                if not is_empty_df(bsub):
                    for grp in ['top', 'low']:
                        b = bsub[bsub['group'] == grp]
                        if not is_empty_df(b):
                            base_x, base_y = safe_lowess_line(b['time'].values, b['score'].values)
                            if len(base_x) > 0:
                                base_lines[grp] = (base_x, base_y)
        
        # 收集红线数据
        red_df = build_colored_df(rnds, 0, 15)
        if not is_empty_df(red_df):
            if st <= 2:
                r = red_df[red_df['agent_id'] == 0]
                if not is_empty_df(r):
                    x_sm, y_sm = safe_lowess_line(r['time'].values, r['score'].values)
                    if len(x_sm) > 0:
                        base_x_all, base_y_all = base_lines.get('all', (np.array([]), np.array([])))
                        x_sm, y_sm = delta_line(x_sm, y_sm, base_x_all, base_y_all)
                        all_y_values.extend(y_sm[~np.isnan(y_sm)])
            else:
                rsub = build_top_low(red_df, rnds)
                if not is_empty_df(rsub):
                    for grp in ['top', 'low']:
                        r = rsub[rsub['group'] == grp]
                        if not is_empty_df(r):
                            x_sm, y_sm = safe_lowess_line(r['time'].values, r['score'].values)
                            if len(x_sm) > 0:
                                base_x_grp, base_y_grp = base_lines.get(grp, (np.array([]), np.array([])))
                                x_sm, y_sm = delta_line(x_sm, y_sm, base_x_grp, base_y_grp)
                                all_y_values.extend(y_sm[~np.isnan(y_sm)])
        
        # 收集蓝线数据
        blue_df = build_colored_df(rnds, 15, None)
        if not is_empty_df(blue_df):
            if st <= 2:
                b = blue_df[blue_df['agent_id'] == 0]
                if not is_empty_df(b):
                    x_sm, y_sm = safe_lowess_line(b['time'].values, b['score'].values)
                    if len(x_sm) > 0:
                        base_x_all, base_y_all = base_lines.get('all', (np.array([]), np.array([])))
                        x_sm, y_sm = delta_line(x_sm, y_sm, base_x_all, base_y_all)
                        all_y_values.extend(y_sm[~np.isnan(y_sm)])
            else:
                bsub = build_top_low(blue_df, rnds)
                if not is_empty_df(bsub):
                    for grp in ['top', 'low']:
                        b = bsub[bsub['group'] == grp]
                        if not is_empty_df(b):
                            x_sm, y_sm = safe_lowess_line(b['time'].values, b['score'].values)
                            if len(x_sm) > 0:
                                base_x_grp, base_y_grp = base_lines.get(grp, (np.array([]), np.array([])))
                                x_sm, y_sm = delta_line(x_sm, y_sm, base_x_grp, base_y_grp)
                                all_y_values.extend(y_sm[~np.isnan(y_sm)])
    
    # 计算统一的Y轴范围
    if all_y_values:
        valid_y = [y for y in all_y_values if not np.isnan(y)]
        if valid_y:
            y_min = min(valid_y)
            y_max = max(valid_y)
            margin = (y_max - y_min) * 0.1
            y_min -= margin
            y_max += margin
        else:
            y_min, y_max = -1, 1
    else:
        y_min, y_max = -1, 1
    
    # 绘制图形
    for ax, (rnds, title, st) in zip(axes, settings):
        black_df = build_black_df(rnds)
        base_lines = {}
        if not is_empty_df(black_df):
            if st <= 2:
                b = black_df[black_df['agent_id'] == 0]
                if not is_empty_df(b):
                    base_x, base_y = safe_lowess_line(b['time'].values, b['score'].values)
                    if len(base_x) > 0:
                        base_lines['all'] = (base_x, base_y)
            else:
                bsub = build_top_low(black_df, rnds)
                if not is_empty_df(bsub):
                    for grp in ['top', 'low']:
                        b = bsub[bsub['group'] == grp]
                        if not is_empty_df(b):
                            base_x, base_y = safe_lowess_line(b['time'].values, b['score'].values)
                            if len(base_x) > 0:
                                base_lines[grp] = (base_x, base_y)
        
        # 红线
        red_df = build_colored_df(rnds, 0, 15)
        if not is_empty_df(red_df):
            if st <= 2:
                r = red_df[red_df['agent_id'] == 0]
                if not is_empty_df(r):
                    x_sm, y_sm = safe_lowess_line(r['time'].values, r['score'].values)
                    if len(x_sm) > 0:
                        base_x_all, base_y_all = base_lines.get('all', (np.array([]), np.array([])))
                        x_sm, y_sm = delta_line(x_sm, y_sm, base_x_all, base_y_all)
                        
                        x_ci, y_ci, (lower_ci, upper_ci) = ci_function(r['time'].values, r['score'].values)
                        if len(x_ci) > 0:
                            if len(base_x_all) > 0:
                                base_interp = np.interp(x_ci, base_x_all, base_y_all, left=np.nan, right=np.nan)
                                y_ci = y_ci - base_interp
                                lower_ci = lower_ci - base_interp
                                upper_ci = upper_ci - base_interp
                            
                            valid_mask = ~np.isnan(lower_ci) & ~np.isnan(upper_ci)
                            if np.any(valid_mask):
                                ax.fill_between(x_ci[valid_mask], lower_ci[valid_mask], 
                                              upper_ci[valid_mask], color='red', alpha=0.3)
                        ax.plot(x_sm, y_sm, color='red', linewidth=2.5, label='RED (≤15)')
            else:
                rsub = build_top_low(red_df, rnds)
                if not is_empty_df(rsub):
                    for grp, lst in [('top', '-'), ('low', '--')]:
                        r = rsub[rsub['group'] == grp]
                        if not is_empty_df(r):
                            x_sm, y_sm = safe_lowess_line(r['time'].values, r['score'].values)
                            if len(x_sm) > 0:
                                base_x_grp, base_y_grp = base_lines.get(grp, (np.array([]), np.array([])))
                                x_sm, y_sm = delta_line(x_sm, y_sm, base_x_grp, base_y_grp)
                                
                                x_ci, y_ci, (lower_ci, upper_ci) = ci_function(r['time'].values, r['score'].values)
                                if len(x_ci) > 0:
                                    if len(base_x_grp) > 0:
                                        base_interp = np.interp(x_ci, base_x_grp, base_y_grp, left=np.nan, right=np.nan)
                                        y_ci = y_ci - base_interp
                                        lower_ci = lower_ci - base_interp
                                        upper_ci = upper_ci - base_interp
                                    
                                    valid_mask = ~np.isnan(lower_ci) & ~np.isnan(upper_ci)
                                    if np.any(valid_mask):
                                        ax.fill_between(x_ci[valid_mask], lower_ci[valid_mask], 
                                                      upper_ci[valid_mask], color='red', alpha=0.3)
                                ax.plot(x_sm, y_sm, color='red', linewidth=2.5, linestyle=lst, label=f'RED-{grp} (≤15)')
        
        # 蓝线
        blue_df = build_colored_df(rnds, 15, None)
        if not is_empty_df(blue_df):
            if st <= 2:
                b = blue_df[blue_df['agent_id'] == 0]
                if not is_empty_df(b):
                    x_sm, y_sm = safe_lowess_line(b['time'].values, b['score'].values)
                    if len(x_sm) > 0:
                        base_x_all, base_y_all = base_lines.get('all', (np.array([]), np.array([])))
                        x_sm, y_sm = delta_line(x_sm, y_sm, base_x_all, base_y_all)
                        
                        x_ci, y_ci, (lower_ci, upper_ci) = ci_function(b['time'].values, b['score'].values)
                        if len(x_ci) > 0:
                            if len(base_x_all) > 0:
                                base_interp = np.interp(x_ci, base_x_all, base_y_all, left=np.nan, right=np.nan)
                                y_ci = y_ci - base_interp
                                lower_ci = lower_ci - base_interp
                                upper_ci = upper_ci - base_interp
                            
                            valid_mask = ~np.isnan(lower_ci) & ~np.isnan(upper_ci)
                            if np.any(valid_mask):
                                ax.fill_between(x_ci[valid_mask], lower_ci[valid_mask], 
                                              upper_ci[valid_mask], color='blue', alpha=0.3)
                        ax.plot(x_sm, y_sm, color='blue', linewidth=2.5, label='BLUE (>15)')
            else:
                bsub = build_top_low(blue_df, rnds)
                if not is_empty_df(bsub):
                    for grp, lst in [('top', '-'), ('low', '--')]:
                        b = bsub[bsub['group'] == grp]
                        if not is_empty_df(b):
                            x_sm, y_sm = safe_lowess_line(b['time'].values, b['score'].values)
                            if len(x_sm) > 0:
                                base_x_grp, base_y_grp = base_lines.get(grp, (np.array([]), np.array([])))
                                x_sm, y_sm = delta_line(x_sm, y_sm, base_x_grp, base_y_grp)
                                
                                x_ci, y_ci, (lower_ci, upper_ci) = ci_function(b['time'].values, b['score'].values)
                                if len(x_ci) > 0:
                                    if len(base_x_grp) > 0:
                                        base_interp = np.interp(x_ci, base_x_grp, base_y_grp, left=np.nan, right=np.nan)
                                        y_ci = y_ci - base_interp
                                        lower_ci = lower_ci - base_interp
                                        upper_ci = upper_ci - base_interp
                                    
                                    valid_mask = ~np.isnan(lower_ci) & ~np.isnan(upper_ci)
                                    if np.any(valid_mask):
                                        ax.fill_between(x_ci[valid_mask], lower_ci[valid_mask], 
                                                      upper_ci[valid_mask], color='blue', alpha=0.3)
                                ax.plot(x_sm, y_sm, color='blue', linewidth=2.5, linestyle=lst, label=f'BLUE-{grp} (>15)')

        ax.axhline(0, color='black', linewidth=1.5, linestyle='-')
        ax.set_title(f"{title} - {method_label}", fontsize=14)
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Δ Score', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(y_min, y_max)
        
        if st == 1:
            ax.legend(loc='best', fontsize=10)

    plt.tight_layout()
    fname = f"all_types_score_comparison_{method}_ci.png"
    out_path = os.path.join(BASE, fname)
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"图片已保存至: {os.path.abspath(out_path)}")

# -------------- 主函数 --------------
def main():
    try:
        # 生成两种方法的图片
        print("生成Bootstrap方法图片...")
        plot_all_types(method='bootstrap')
        
        print("生成标准差方法图片...")
        plot_all_types(method='std')
        
    except Exception as e:
        print("处理失败:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()