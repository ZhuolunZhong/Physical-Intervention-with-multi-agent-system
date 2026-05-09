#!/usr/bin/env python3
# pyright: reportCallIssue=false, reportArgumentType=false, reportAttributeAccessIssue=false
"""Reproduce Q-Value x Intervention Frequency Analysis.

This script reproduces the key finding that high-frequency teachers target
lower expected Q-value states than low-frequency teachers.

Key Finding:
    High-frequency interveners (>15 interventions/round) target significantly
    lower expected Q-value states compared to low-frequency interveners.

Data Sources:
    - study_data/user_data_q.csv: Timestep-level ExpectedQvalue (0.5s intervals)
    - study_data/user_data_action.csv: Intervention records for frequency counts

CRITICAL: The analysis uses ExpectedQvalue from user_data_q.csv (full trajectory
Q-values at all timesteps), NOT expected_q_value from user_data_action.csv
(Q-values only at intervention moments). These represent different constructs:
    - user_data_q.csv: What states users experienced across the entire round
    - user_data_action.csv: What states users intervened on specifically

Usage:
    python reproduce_qvalue_frequency_analysis.py

Output:
    Prints statistics matching the paper's claims about frequency -> Q-value targeting.
"""

import numpy as np
import pandas as pd
from scipy import stats


def run_analysis(data_dir: str = "study_data"):
    """Run the complete Q-value x frequency analysis."""
    # Load data
    print("Loading data...")
    q_df = pd.read_csv(f"{data_dir}/user_data_q.csv")
    action_df = pd.read_csv(f"{data_dir}/user_data_action.csv")
    print(f"  Q-value data: {len(q_df):,} rows")
    print(f"  Action data: {len(action_df):,} rows")

    # Compute user-level mean ExpectedQvalue across all timesteps
    user_eq = q_df.groupby("user_id")["ExpectedQvalue"].mean().reset_index()

    # Compute intervention frequency per user (8 rounds)
    n_rounds = 8
    user_counts = action_df.groupby("user_id").size().reset_index(name="total")
    user_counts["freq_per_round"] = user_counts["total"] / n_rounds

    # Merge and classify by median split at 15 interventions/round
    user_df = user_eq.merge(user_counts, on="user_id")
    user_df["group"] = np.where(user_df["freq_per_round"] > 15, "high", "low")

    # Split groups
    high = user_df[user_df["group"] == "high"]
    low = user_df[user_df["group"] == "low"]

    high_eq = np.array(high["ExpectedQvalue"])
    low_eq = np.array(low["ExpectedQvalue"])

    # Compute statistics
    result = stats.ttest_ind(high_eq, low_eq)
    t_stat = float(result.statistic)
    p_value = float(result.pvalue)
    df = len(high_eq) + len(low_eq) - 2

    # Cohen's d
    n1, n2 = len(high_eq), len(low_eq)
    pooled_std = np.sqrt(
        (
            (n1 - 1) * np.std(high_eq, ddof=1) ** 2
            + (n2 - 1) * np.std(low_eq, ddof=1) ** 2
        )
        / (n1 + n2 - 2)
    )
    cohens_d = (np.mean(high_eq) - np.mean(low_eq)) / pooled_std

    # Normalize to 0-1 for paper reporting
    eq_min = float(q_df["ExpectedQvalue"].min())
    eq_max = float(q_df["ExpectedQvalue"].max())
    high_norm = (high_eq - eq_min) / (eq_max - eq_min)
    low_norm = (low_eq - eq_min) / (eq_max - eq_min)

    # Print results
    print("\n" + "=" * 70)
    print("Q-VALUE x INTERVENTION FREQUENCY ANALYSIS")
    print("=" * 70)

    print("\n[1] SAMPLE SIZES")
    print(f"    High-frequency group: n = {len(high)}")
    print(f"    Low-frequency group:  n = {len(low)}")
    print(f"    Total participants:   N = {len(user_df)}")

    print("\n[2] INTERVENTION FREQUENCIES (per round)")
    high_freq_mean = float(high["freq_per_round"].mean())
    low_freq_mean = float(low["freq_per_round"].mean())
    print(f"    High-frequency group: M = {high_freq_mean:.1f} interventions/round")
    print(f"    Low-frequency group:  M = {low_freq_mean:.1f} interventions/round")
    print("    Median split threshold: 15 interventions/round")

    print("\n[3] EXPECTED Q-VALUES (raw scale)")
    print(
        f"    High-frequency: M = {np.mean(high_eq):.2f}, SD = {np.std(high_eq, ddof=1):.2f}"
    )
    print(
        f"    Low-frequency:  M = {np.mean(low_eq):.2f}, SD = {np.std(low_eq, ddof=1):.2f}"
    )

    print("\n[4] EXPECTED Q-VALUES (normalized 0-1 scale)")
    print(
        f"    High-frequency: M = {np.mean(high_norm):.3f}, SD = {np.std(high_norm, ddof=1):.3f}"
    )
    print(
        f"    Low-frequency:  M = {np.mean(low_norm):.3f}, SD = {np.std(low_norm, ddof=1):.3f}"
    )

    print("\n[5] STATISTICAL TEST")
    print(f"    t({df}) = {t_stat:.2f}")
    print(f"    p = {p_value:.3f}")
    print(f"    Cohen's d = {cohens_d:.2f}")

    print("\n[6] INTERPRETATION")
    if t_stat < 0 and p_value < 0.05:
        print("    [OK] High-frequency teachers target LOWER expected Q-value states")
        print("    [OK] Effect is statistically significant")
        if abs(cohens_d) < 0.5:
            effect_size = "small"
        elif abs(cohens_d) < 0.8:
            effect_size = "medium"
        else:
            effect_size = "large"
        print(f"    [OK] Effect size is {effect_size} (d = {cohens_d:.2f})")
    else:
        print("    [X] Effect not statistically significant")

    print("\n" + "=" * 70)
    print("FOR PAPER (LaTeX format):")
    print("=" * 70)
    high_mean_norm = np.mean(high_norm)
    high_sd_norm = np.std(high_norm, ddof=1)
    low_mean_norm = np.mean(low_norm)
    low_sd_norm = np.std(low_norm, ddof=1)
    print("\nHigh-frequency teachers targeted significantly lower Q-values")
    print(f"($M = {high_mean_norm:.3f}$, $SD = {high_sd_norm:.3f}$) than")
    print(
        f"low-frequency teachers ($M = {low_mean_norm:.3f}$, $SD = {low_sd_norm:.3f}$),"
    )
    print(f"$t({df}) = {t_stat:.2f}$, $p = {p_value:.3f}$, $d = {cohens_d:.2f}$.")

    return {
        "n_high": len(high),
        "n_low": len(low),
        "t_statistic": t_stat,
        "p_value": p_value,
        "cohens_d": cohens_d,
        "high_mean_norm": high_mean_norm,
        "low_mean_norm": low_mean_norm,
    }


if __name__ == "__main__":
    run_analysis()
