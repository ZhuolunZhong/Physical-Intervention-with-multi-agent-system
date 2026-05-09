# expected_q.py  （完全自包含，含 build_top_low）
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

# ----------- 主数据 Top/Low 构建 -----------
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

# ----------- 读取主数据 -----------
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

# ----------- 读取黑线 -----------
def read_black_setting(setting: int):
    spath = os.path.join(BASE, 'black', f'setting{setting}')
    runs  = []
    for run_id in range(1, 51):
        file = os.path.join(spath, f'run_{run_id}.csv')
        if not os.path.exists(file):
            continue
        df = pd.read_csv(file)
        df = df[df['step'] <= 33].copy()
        df['time'] = df['step'] * 3
        df['run_id'] = run_id
        runs.append(df[['time', 'ExpectedQvalue', 'agentid', 'run_id']])
    return pd.concat(runs, ignore_index=True) if runs else pd.DataFrame()

def black_top_low(df: pd.DataFrame) -> pd.DataFrame:
    score = (df.groupby(['run_id', 'agentid'])
               .apply(lambda g: eval_at_100(g['time'].values, g['ExpectedQvalue'].values))
               .reset_index(name='score'))
    best = (score.sort_values('score')
                  .drop_duplicates(['run_id'], keep='last')
                  .assign(group='top'))
    best['agentid_best'] = best['agentid']
    df = df.merge(best[['run_id', 'agentid_best', 'group']],
                  on='run_id', how='left')
    df['group'] = np.where(df['agentid'] == df['agentid_best'], 'top', 'low')
    return df

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
        black_df = read_black_setting(st)
        if not black_df.empty:
            if st <= 2:
                black_df = black_df[black_df['agentid'] == 0]
                x_sm, y_sm = lowess_line(black_df['time'].values, black_df['ExpectedQvalue'].values)
                if x_sm.size:
                    ax.plot(x_sm, y_sm, color='black', linewidth=1.2)
            else:
                black_df = black_top_low(black_df)
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
        if st <= 2:
            ax.legend(fontsize=9)
        else:
            handles, labels = ax.get_legend_handles_labels()
            short = [(h, l) for h, l in zip(handles, labels) if l.endswith('-top')]
            if short:
                ax.legend(*zip(*short), fontsize=9)

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