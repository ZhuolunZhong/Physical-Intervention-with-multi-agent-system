# expected_q.py  （已修复 merge 类型冲突）
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.nonparametric.smoothers_lowess import lowess

plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False
plt.ioff()

FRAC = 0.3
BASE = os.path.dirname(os.path.abspath(__file__))

# ----------- 通用工具 -----------
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

def eval_at_100(x: np.ndarray, y: np.ndarray) -> float:
    x_sm, y_sm = lowess_line(x, y)
    if not x_sm.size:
        return np.nan
    return np.interp(100, x_sm, y_sm, left=np.nan, right=np.nan)

# ----------- 主数据 -----------
def read_main() -> pd.DataFrame:
    parts = []
    for folder in ('clean', 'pilot'):
        path = os.path.join(BASE, folder)
        stats = os.path.join(path, 'user_round_statistics.csv')
        data  = os.path.join(path, 'user_data_q.csv')
        if not (os.path.exists(stats) and os.path.exists(data)):
            continue
        valid = pd.read_csv(stats)['user_id'].unique()
        df    = pd.read_csv(data)
        df    = df[df['user_id'].isin(valid)]
        df['interpret_type'] = df['user_id'].apply(get_interpret_type)
        df['data_source']    = folder
        parts.append(df)
    if not parts:
        raise RuntimeError("未读取到任何有效主数据")
    return pd.concat(parts, ignore_index=True)

# ----------- 黑线数据构建 -----------
def build_black_df(rounds: list[int]) -> pd.DataFrame:
    detailed = pd.read_csv(os.path.join(BASE, 'black', 'user_round_counts_detailed.csv'))
    round_cols = [f'round_{r}' for r in rounds]
    detailed = detailed[['user_id'] + round_cols].melt(
        id_vars='user_id', var_name='round_col', value_name='val')
    detailed = detailed[detailed['val'] <= 3]
    detailed['round'] = detailed['round_col'].str.extract(r'round_(\d+)').astype(int)

    # 修复：先把 user_id 转数字，非法值丢弃
    black_keys = detailed[['user_id', 'round']].drop_duplicates()
    black_keys['user_id'] = pd.to_numeric(black_keys['user_id'], errors='coerce')
    black_keys = black_keys.dropna().astype({'user_id': 'int64', 'round': 'int64'})

    data_path = os.path.join(BASE, 'black', 'user_data_q.csv')
    if not os.path.exists(data_path):
        return pd.DataFrame()
    df = pd.read_csv(data_path)
    # 同样先转数字，丢弃非法 user_id
    df['user_id'] = pd.to_numeric(df['user_id'], errors='coerce')
    df = df.dropna(subset=['user_id']).astype({'user_id': 'int64', 'round': 'int64'})
    df = df.merge(black_keys, on=['user_id', 'round'], how='inner')
    return df

def build_top_low(df: pd.DataFrame, rounds: list[int]) -> pd.DataFrame:
    sub = df[df['round'].isin(rounds) & df['agent_id'].isin([0, 1])].copy()
    score = (sub.groupby(['user_id', 'round', 'agent_id'])
               .apply(lambda g: eval_at_100(g['time'].values, g['ExpectedQvalue'].values))
               .reset_index(name='score'))
    best = (score.sort_values('score')
                  .drop_duplicates(['user_id', 'round'], keep='last')
                  .assign(group='top'))
    best['agent_id_best'] = best['agent_id']
    sub = sub.merge(best[['user_id', 'round', 'agent_id_best', 'group']],
                    on=['user_id', 'round'], how='left')
    sub['group'] = np.where(sub['agent_id'] == sub['agent_id_best'], 'top', 'low')
    return sub[['user_id', 'round', 'agent_id', 'time', 'ExpectedQvalue',
                'interpret_type', 'data_source', 'group']]

# ----------- 绘制 -----------
def plot_four(df_main: pd.DataFrame):
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    fig, axes = plt.subplots(1, 4, figsize=(24, 6))

    for ax, (rnds, title, st) in zip(axes,
                                     [([2, 3], "setting1", 1),
                                      ([4, 5], "setting2", 2),
                                      ([6, 7], "setting3", 3),
                                      ([8, 9], "setting4", 4)]):
        # 主数据
        if st <= 2:
            sub = df_main[df_main['round'].isin(rnds) & (df_main['agent_id'] == 0)]
            for itype in range(6):
                piece = sub[sub['interpret_type'] == itype]
                if piece.empty:
                    continue
                x_sm, y_sm = lowess_line(piece['time'].values, piece['ExpectedQvalue'].values)
                if x_sm.size:
                    ax.plot(x_sm, y_sm, color=colors[itype], linewidth=2.5,
                            label=get_type_name(itype))
        else:
            sub = build_top_low(df_main, rnds)
            for itype in range(6):
                for grp, lst in [('top', '-'), ('low', '--')]:
                    piece = sub[(sub['interpret_type'] == itype) & (sub['group'] == grp)]
                    if piece.empty:
                        continue
                    x_sm, y_sm = lowess_line(piece['time'].values, piece['ExpectedQvalue'].values)
                    if x_sm.size:
                        ax.plot(x_sm, y_sm, color=colors[itype], linewidth=2.5,
                               linestyle=lst, label=f"{get_type_name(itype)}-{grp}")

        # 黑线
        black_df = build_black_df(rnds)
        if not black_df.empty:
            if st <= 2:
                black_df = black_df[black_df['agent_id'] == 0]
                x_sm, y_sm = lowess_line(black_df['time'].values, black_df['ExpectedQvalue'].values)
                if x_sm.size:
                    ax.plot(x_sm, y_sm, color='black', linewidth=1.2)
            else:
                # 黑线也做 Top/Low
                score = (black_df.groupby(['user_id', 'round', 'agent_id'])
                                 .apply(lambda g: eval_at_100(g['time'].values, g['ExpectedQvalue'].values))
                                 .reset_index(name='score'))
                best  = (score.sort_values('score')
                               .drop_duplicates(['user_id', 'round'], keep='last')
                               .assign(group='top'))
                best['agent_id_best'] = best['agent_id']
                black_df = black_df.merge(best[['user_id', 'round', 'agent_id_best', 'group']],
                                          on=['user_id', 'round'], how='left')
                black_df['group'] = np.where(black_df['agent_id'] == black_df['agent_id_best'], 'top', 'low')
                for grp, lst in [('top', '-'), ('low', '--')]:
                    bsub = black_df[black_df['group'] == grp]
                    if bsub.empty:
                        continue
                    x_sm, y_sm = lowess_line(bsub['time'].values, bsub['ExpectedQvalue'].values)
                    if x_sm.size:
                        ax.plot(x_sm, y_sm, color='black', linewidth=1.2, linestyle=lst)

        ax.set_title(title, fontsize=14)
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Expected Q Value', fontsize=12)
        ax.grid(True, alpha=0.3)


    plt.tight_layout()
    out_path = os.path.join(BASE, "expected_q_lowess.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"图片已保存至: {os.path.abspath(out_path)}")

# ----------- 主入口 -----------
def main():
    try:
        df = read_main()
        plot_four(df)
    except Exception as e:
        print("处理失败:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()