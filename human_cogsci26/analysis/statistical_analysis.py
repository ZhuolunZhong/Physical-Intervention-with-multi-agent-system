"""Statistical Analysis for CogSci 2026 Paper

Analyzes human teaching intervention data to substantiate claims in the paper.
"""

import pandas as pd
from scipy import stats
import warnings

warnings.filterwarnings("ignore")

# Interpretation types mapping
INTERPRETATION_TYPES = {
    0: "SUGGESTION",
    1: "RESET",
    2: "INTERRUPT",
    3: "TRANSITION",
    4: "DISRUPT",
    5: "IMPEDE",
}


def get_interpretation_type(user_id):
    """Get interpretation type from user_id using (user_id - 1) % 6"""
    try:
        return (int(user_id) - 1) % 6
    except (ValueError, TypeError):
        return -1  # Unknown user


# Load data
print("=" * 60)
print("STATISTICAL ANALYSIS FOR COGSCI 2026 PAPER")
print("=" * 60)

print("\n[1] Loading data files...")
action_df = pd.read_csv("study_data/user_data_action.csv")
score_df = pd.read_csv("study_data/user_data.csv")
qvalue_df = pd.read_csv("study_data/user_data_q.csv")

print(f"  - action_df: {len(action_df)} rows")
print(f"  - score_df: {len(score_df)} rows")
print(f"  - qvalue_df: {len(qvalue_df)} rows")

# Add interpretation type to action dataframe
action_df["interpretation_type"] = action_df["user_id"].apply(get_interpretation_type)
action_df["interpretation_name"] = action_df["interpretation_type"].map(
    INTERPRETATION_TYPES
)

print("\n" + "=" * 60)
print("ANALYSIS 1: INTERVENTION COUNTS AND PROPORTIONS")
print("=" * 60)

# Total interventions
total_interventions = len(action_df)
print(f"\nTotal interventions: {total_interventions}")

# Count by optimality
optimal_interventions = action_df[action_df["is_optimal"] == 1]
suboptimal_interventions = action_df[action_df["is_optimal"] == 0]

print(
    f"Interventions on optimal actions: {len(optimal_interventions)} ({100 * len(optimal_interventions) / total_interventions:.2f}%)"
)
print(
    f"Interventions on suboptimal actions: {len(suboptimal_interventions)} ({100 * len(suboptimal_interventions) / total_interventions:.2f}%)"
)

# Split by world type (rounds 2-5 = random, rounds 6-9 = smooth)
action_df["world_type"] = action_df["round"].apply(
    lambda r: "random" if r <= 5 else "smooth"
)

random_actions = action_df[action_df["world_type"] == "random"]
smooth_actions = action_df[action_df["world_type"] == "smooth"]

print("\nBy world type:")
print(f"  Random (rounds 2-5): {len(random_actions)} interventions")
print(f"  Smooth (rounds 6-9): {len(smooth_actions)} interventions")

# Proportions by world type and optimality
random_optimal = len(random_actions[random_actions["is_optimal"] == 1])
random_suboptimal = len(random_actions[random_actions["is_optimal"] == 0])
smooth_optimal = len(smooth_actions[smooth_actions["is_optimal"] == 1])
smooth_suboptimal = len(smooth_actions[smooth_actions["is_optimal"] == 0])

print("\nRandom distribution proportions:")
if len(random_actions) > 0:
    print(f"  Optimal: {random_optimal} ({random_optimal / len(random_actions):.4f})")
    print(
        f"  Suboptimal: {random_suboptimal} ({random_suboptimal / len(random_actions):.4f})"
    )

print("\nSmooth distribution proportions:")
if len(smooth_actions) > 0:
    print(f"  Optimal: {smooth_optimal} ({smooth_optimal / len(smooth_actions):.4f})")
    print(
        f"  Suboptimal: {smooth_suboptimal} ({smooth_suboptimal / len(smooth_actions):.4f})"
    )

# Chi-square test for independence between world type and optimality
contingency_table = pd.crosstab(action_df["world_type"], action_df["is_optimal"])
chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
print("\nChi-square test (world type x optimality):")
print(f"  χ² = {chi2:.4f}, p = {p_value:.4e}, df = {dof}")

print("\n" + "=" * 60)
print("ANALYSIS 2: INTERVENTION FREQUENCY BY USER")
print("=" * 60)

# Count interventions per user per round
user_round_counts = (
    action_df.groupby(["user_id", "round"]).size().reset_index(name="count")
)

# Average interventions per round per user
avg_per_user_round = user_round_counts.groupby("user_id")["count"].mean()
print(
    f"\nMean interventions per round across users: {avg_per_user_round.mean():.2f} (SD: {avg_per_user_round.std():.2f})"
)

# High vs low frequency groups (threshold: 15 per round based on paper)
FREQ_THRESHOLD = 15
user_avg_freq = user_round_counts.groupby("user_id")["count"].mean()
high_freq_users = user_avg_freq[user_avg_freq >= FREQ_THRESHOLD].index
low_freq_users = user_avg_freq[user_avg_freq < FREQ_THRESHOLD].index

print(f"\nFrequency groups (threshold: {FREQ_THRESHOLD} interventions/round):")
print(f"  High-frequency users: {len(high_freq_users)}")
print(f"  Low-frequency users: {len(low_freq_users)}")

print("\n" + "=" * 60)
print("ANALYSIS 3: TEACHING HYPOTHESES")
print("=" * 60)

# Based on paper Table 1:
# H1 (Undoing): Move agent back to where it was before
# H2 (Correcting): Move agent toward optimal path
# H3 (Exploration-encouraging): Move to unvisited state
# H4 (Restart): Move to starting position


def classify_teaching_hypothesis(row):
    """Classify intervention into teaching hypothesis based on positions.

    H1 (Undoing): agent_end_pos == agent_ini_pos (put back to initial)
    H2 (Correcting): Intervention on suboptimal action
    H3 (Exploration): Would need visit data to determine
    H4 (Restart): agent_end_pos is starting position (e.g., 0,0 or corner)

    Simplified version based on available data.
    """
    end_x, end_y = row["agent_end_pos_x"], row["agent_end_pos_y"]
    ini_x, ini_y = row["agent_ini_pos_x"], row["agent_ini_pos_y"]
    is_optimal = row["is_optimal"]

    # H4: Reset to starting position (assuming corners or fixed start)
    # Check if end position is a corner (0,0), (0,7), (7,0), (7,7)
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    if (end_x, end_y) in corners:
        return "H4_Restart"

    # H1: Undoing - put agent back to where it started the action
    if end_x == ini_x and end_y == ini_y:
        return "H1_Undoing"

    # H2: Correcting - intervene on suboptimal action
    if is_optimal == 0:
        return "H2_Correcting"

    # Default: Could be exploration or other
    return "H3_Exploration"


action_df["teaching_hypothesis"] = action_df.apply(classify_teaching_hypothesis, axis=1)

# Count by hypothesis
hypothesis_counts = action_df["teaching_hypothesis"].value_counts()
print("\nTeaching hypothesis distribution (simplified classification):")
for hyp, count in hypothesis_counts.items():
    print(f"  {hyp}: {count} ({100 * count / total_interventions:.1f}%)")

# Per-user dominant hypothesis (for Table 1 in paper)
user_hypothesis = (
    action_df.groupby(["user_id", "teaching_hypothesis"]).size().unstack(fill_value=0)
)
dominant_hypothesis = user_hypothesis.idxmax(axis=1)
hypothesis_user_counts = dominant_hypothesis.value_counts()

print("\nUsers by dominant teaching hypothesis:")
for hyp, count in hypothesis_user_counts.items():
    print(f"  {hyp}: {count} users")

print("\n" + "=" * 60)
print("ANALYSIS 4: Q-VALUE ANALYSIS")
print("=" * 60)

# Get final Q-values per user per round
final_qvalues = (
    qvalue_df.groupby(["user_id", "round"])
    .agg({"ExpectedQvalue": "last"})
    .reset_index()
)

# Add interpretation type
final_qvalues["interpretation_type"] = final_qvalues["user_id"].apply(
    get_interpretation_type
)
final_qvalues["interpretation_name"] = final_qvalues["interpretation_type"].map(
    INTERPRETATION_TYPES
)
final_qvalues["world_type"] = final_qvalues["round"].apply(
    lambda r: "random" if r <= 5 else "smooth"
)

# Summary statistics by interpretation type
print("\nFinal Expected Q-value by interpretation type:")
qvalue_by_type = final_qvalues.groupby("interpretation_name")["ExpectedQvalue"].agg(
    ["mean", "std", "count"]
)
print(qvalue_by_type.to_string())

# ANOVA test across interpretation types
interpretation_groups = [
    group["ExpectedQvalue"].values
    for name, group in final_qvalues.groupby("interpretation_name")
]
f_stat, p_value = stats.f_oneway(*interpretation_groups)
print("\nOne-way ANOVA (Q-value ~ interpretation type):")
print(f"  F = {f_stat:.4f}, p = {p_value:.4e}")

# By world type
print("\nFinal Expected Q-value by world type:")
qvalue_by_world = final_qvalues.groupby("world_type")["ExpectedQvalue"].agg(
    ["mean", "std", "count"]
)
print(qvalue_by_world.to_string())

# T-test between world types
random_qvals = final_qvalues[final_qvalues["world_type"] == "random"]["ExpectedQvalue"]
smooth_qvals = final_qvalues[final_qvalues["world_type"] == "smooth"]["ExpectedQvalue"]
t_stat, p_value = stats.ttest_ind(random_qvals, smooth_qvals)
print("\nT-test (random vs smooth Q-values):")
print(f"  t = {t_stat:.4f}, p = {p_value:.4e}")

print("\n" + "=" * 60)
print("ANALYSIS 5: SCORE ANALYSIS")
print("=" * 60)

# Final scores per user per round
final_scores = (
    score_df.groupby(["user_id", "round"]).agg({"score": "last"}).reset_index()
)

# Convert score to numeric
final_scores["score"] = pd.to_numeric(final_scores["score"], errors="coerce")

final_scores["interpretation_type"] = final_scores["user_id"].apply(
    get_interpretation_type
)
final_scores["interpretation_name"] = final_scores["interpretation_type"].map(
    INTERPRETATION_TYPES
)
final_scores["world_type"] = final_scores["round"].apply(
    lambda r: "random" if r <= 5 else "smooth"
)

print("\nFinal scores by interpretation type:")
score_by_type = final_scores.groupby("interpretation_name")["score"].agg(
    ["mean", "std", "count"]
)
print(score_by_type.to_string())

# ANOVA for scores
score_groups = [
    group["score"].dropna().values
    for name, group in final_scores.groupby("interpretation_name")
]
f_stat, p_value = stats.f_oneway(*score_groups)
print("\nOne-way ANOVA (score ~ interpretation type):")
print(f"  F = {f_stat:.4f}, p = {p_value:.4e}")

print("\n" + "=" * 60)
print("ANALYSIS 6: INTERPRETATION TYPE COMPARISON")
print("=" * 60)

# Detailed breakdown by interpretation type
for interp_type in sorted(INTERPRETATION_TYPES.keys()):
    interp_name = INTERPRETATION_TYPES[interp_type]
    type_actions = action_df[action_df["interpretation_type"] == interp_type]
    type_scores = final_scores[final_scores["interpretation_type"] == interp_type]
    type_qvals = final_qvalues[final_qvalues["interpretation_type"] == interp_type]

    n_users = type_actions["user_id"].nunique()
    n_rounds = type_actions["round"].nunique() if n_users > 0 else 1

    print(f"\n{interp_name} (type {interp_type}):")
    print(f"  Users: {n_users}")
    print(f"  Total interventions: {len(type_actions)}")
    if n_users > 0 and n_rounds > 0:
        print(
            f"  Avg interventions/round: {len(type_actions) / (n_users * n_rounds):.2f}"
        )
    print(
        f"  Optimal intervention rate: {type_actions['is_optimal'].mean():.3f}"
        if len(type_actions) > 0
        else "  No interventions"
    )
    print(
        f"  Mean final score: {type_scores['score'].mean():.2f} (SD: {type_scores['score'].std():.2f})"
        if len(type_scores) > 0
        else "  No scores"
    )
    print(
        f"  Mean final Q-value: {type_qvals['ExpectedQvalue'].mean():.2f} (SD: {type_qvals['ExpectedQvalue'].std():.2f})"
        if len(type_qvals) > 0
        else "  No Q-values"
    )

print("\n" + "=" * 60)
print("ANALYSIS 7: HIGH vs LOW FREQUENCY COMPARISON")
print("=" * 60)

# Merge frequency info with scores and Q-values
user_freq_group = pd.DataFrame(
    {
        "user_id": user_avg_freq.index,
        "avg_freq": user_avg_freq.values,
        "freq_group": [
            "high" if f >= FREQ_THRESHOLD else "low" for f in user_avg_freq.values
        ],
    }
)

# Scores by frequency group
scores_with_freq = final_scores.merge(user_freq_group, on="user_id")
print("\nFinal scores by frequency group:")
score_by_freq = scores_with_freq.groupby("freq_group")["score"].agg(
    ["mean", "std", "count"]
)
print(score_by_freq.to_string())

# T-test
high_freq_scores = scores_with_freq[scores_with_freq["freq_group"] == "high"][
    "score"
].dropna()
low_freq_scores = scores_with_freq[scores_with_freq["freq_group"] == "low"][
    "score"
].dropna()
if len(high_freq_scores) > 0 and len(low_freq_scores) > 0:
    t_stat, p_value = stats.ttest_ind(high_freq_scores, low_freq_scores)
    print("\nT-test (high vs low frequency scores):")
    print(f"  t = {t_stat:.4f}, p = {p_value:.4e}")

# Q-values by frequency group
qvals_with_freq = final_qvalues.merge(user_freq_group, on="user_id")
print("\nFinal Q-values by frequency group:")
qval_by_freq = qvals_with_freq.groupby("freq_group")["ExpectedQvalue"].agg(
    ["mean", "std", "count"]
)
print(qval_by_freq.to_string())

high_freq_qvals = qvals_with_freq[qvals_with_freq["freq_group"] == "high"][
    "ExpectedQvalue"
].dropna()
low_freq_qvals = qvals_with_freq[qvals_with_freq["freq_group"] == "low"][
    "ExpectedQvalue"
].dropna()
if len(high_freq_qvals) > 0 and len(low_freq_qvals) > 0:
    t_stat, p_value = stats.ttest_ind(high_freq_qvals, low_freq_qvals)
    print("\nT-test (high vs low frequency Q-values):")
    print(f"  t = {t_stat:.4f}, p = {p_value:.4e}")

print("\n" + "=" * 60)
print("ANALYSIS 8: INTERVENTION TIMING ANALYSIS")
print("=" * 60)

# Average duration of interventions
print("\nIntervention duration (ms):")
print(f"  Mean: {action_df['duration'].mean():.2f}")
print(f"  SD: {action_df['duration'].std():.2f}")
print(f"  Median: {action_df['duration'].median():.2f}")

# Duration by optimality
optimal_duration = action_df[action_df["is_optimal"] == 1]["duration"]
suboptimal_duration = action_df[action_df["is_optimal"] == 0]["duration"]

print("\nDuration by optimality:")
print(
    f"  Optimal actions: {optimal_duration.mean():.2f} (SD: {optimal_duration.std():.2f})"
)
print(
    f"  Suboptimal actions: {suboptimal_duration.mean():.2f} (SD: {suboptimal_duration.std():.2f})"
)

t_stat, p_value = stats.ttest_ind(optimal_duration, suboptimal_duration)
print("\nT-test (duration: optimal vs suboptimal):")
print(f"  t = {t_stat:.4f}, p = {p_value:.4e}")

print("\n" + "=" * 60)
print("SUMMARY TABLE: KEY STATISTICS")
print("=" * 60)

print(f"""
| Metric | Value |
|--------|-------|
| Total interventions | {total_interventions} |
| Interventions on optimal | {len(optimal_interventions)} ({100 * len(optimal_interventions) / total_interventions:.1f}%) |
| Interventions on suboptimal | {len(suboptimal_interventions)} ({100 * len(suboptimal_interventions) / total_interventions:.1f}%) |
| Random world interventions | {len(random_actions)} |
| Smooth world interventions | {len(smooth_actions)} |
| High-frequency users | {len(high_freq_users)} |
| Low-frequency users | {len(low_freq_users)} |
| Unique users | {action_df["user_id"].nunique()} |
| Unique rounds (per user) | {action_df["round"].nunique()} |
""")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)
