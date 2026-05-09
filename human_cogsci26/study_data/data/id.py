#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计 clean 与 pilot 两组 user_round_statistics.csv 中
user_id 对应的 INTERPRET_TYPE 分布
"""

import os
import pandas as pd
from pathlib import Path

# ---------- 1. 定位脚本所在目录 ----------
BASE_DIR = Path(__file__).resolve().parent   # 脚本所在文件夹
CLEAN_DIR  = BASE_DIR / "clean"
PILOT_DIR  = BASE_DIR / "pilot"

CSV_NAME = "user_round_statistics.csv"

# ---------- 2. 映射函数（与 React 侧保持一致） ----------
def interpret_type(uid: int) -> int:
    """
    对应 React 代码：
    const candidates = [0,1,2,3,4,5];
    const index = (username - 1) % candidates.length;
    return candidates[index];
    """
    return (uid - 1) % 6

# ---------- 3. 单组统计函数 ----------
def count_types(folder: Path) -> pd.Series:
    """
    读取 folder/CSV_NAME，把 user_id 列转成类型后统计
    返回 0-5 六类的计数 Series（index 顺序 0-5，缺类补 0）
    """
    csv_path = folder / CSV_NAME
    if not csv_path.exists():
        raise FileNotFoundError(f"找不到文件：{csv_path}")

    df = pd.read_csv(csv_path)
    if "user_id" not in df.columns:
        raise ValueError(f"{csv_path} 中缺少 user_id 列")

    # 确保是整数，非法值直接丢弃
    df["user_id"] = pd.to_numeric(df["user_id"], errors="coerce")
    df = df.dropna(subset=["user_id"])
    df["user_id"] = df["user_id"].astype(int)

    # 映射并统计
    types = df["user_id"].map(interpret_type)
    counts = types.value_counts().sort_index()

    # 补全 0-5 所有类
    counts = counts.reindex(range(6), fill_value=0).astype(int)
    return counts

# ---------- 4. 分别统计两组 ----------
clean_counts = count_types(CLEAN_DIR)
pilot_counts = count_types(PILOT_DIR)
total_counts = clean_counts + pilot_counts

# ---------- 5. 打印结果 ----------
type_names = ["SUGGESTION", "RESET", "INTERRUPT", "TRANSITION", "DISRUPT", "IMPEDE"]

print("clean 组统计：")
for t, c in clean_counts.items():
    print(f"  {type_names[t]}({t}): {c}")

print("\npilot 组统计：")
for t, c in pilot_counts.items():
    print(f"  {type_names[t]}({t}): {c}")

print("\n合并后总统计：")
for t, c in total_counts.items():
    print(f"  {type_names[t]}({t}): {c}")

print(f"\n总行数验证：clean={clean_counts.sum()}, pilot={pilot_counts.sum()}, total={total_counts.sum()}")
if total_counts.sum() == 64:
    print("✅ 总行数 = 64，验证通过")
else:
    print("❌ 总行数 ≠ 64，请检查数据")